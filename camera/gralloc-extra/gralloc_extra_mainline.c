/*
 * libgralloc_extra.so replacement for the mainline (minigbm) graphics stack.
 *
 * The stock library reads MTK Arm-gralloc private handles and keeps per-buffer
 * metadata in GED regions (/proc/ged), none of which exist on 6.18. Buffers now
 * come from minigbm (cros_gralloc_handle), so answer the queries from that
 * handle and keep the GED regions in a process-local table keyed by the dma-buf
 * inode. IDs and region sizes mirror the stock vendor/lib64/libgralloc_extra.so.
 */
#include <android/log.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define LOG_TAG "gralloc_extra_shim"
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

#define GE_OK 0
#define GE_NOT_SUPPORTED (-2)
#define GE_NULL_HANDLE (-5)
#define GE_BAD_HANDLE 7

typedef struct {
	int version;
	int numFds;
	int numInts;
	int data[0];
} ge_native_handle_t;
typedef const ge_native_handle_t *buffer_handle_t;

/* cros_gralloc_handle (packed) field offsets from the start of the handle */
#define CH_FDS 12
#define CH_STRIDES 32
#define CH_OFFSETS 48
#define CH_WIDTH 84
#define CH_HEIGHT 88
#define CH_FORMAT 92
#define CH_MAGIC 116
#define CH_PIXEL_STRIDE 120
#define CH_DROID_FORMAT 124
#define CH_USAGE 128
#define CH_NUM_PLANES 136
#define CH_TOTAL_SIZE 148
#define CH_SIZE 156
#define CROS_GRALLOC_MAGIC 0xABCDDCBAu

#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | ((uint32_t)(d) << 24))

#define HAL_RGBA_8888 1
#define HAL_RGBX_8888 2
#define HAL_RGB_888 3
#define HAL_RGB_565 4
#define HAL_BGRA_8888 5
#define HAL_YCRCB_420_SP 0x11
#define HAL_BLOB 0x21
#define HAL_IMPLEMENTATION_DEFINED 0x22
#define HAL_YCBCR_420_888 0x23
#define HAL_YV12 0x32315659
#define HAL_Y8 0x20203859
#define HAL_MTK_NV12 0x1000 /* "NV12" in libmtkcam_grallocutils */

#define USAGE_PROTECTED 0x4000ull
#define USAGE_VIDEO_ENCODER 0x10000ull
#define USAGE_CAMERA_WRITE 0x20000ull
#define USAGE_CAMERA_READ 0x40000ull

static uint32_t rd32(buffer_handle_t h, unsigned off)
{
	uint32_t v;
	memcpy(&v, (const char *)h + off, sizeof(v));
	return v;
}

static uint64_t rd64(buffer_handle_t h, unsigned off)
{
	uint64_t v;
	memcpy(&v, (const char *)h + off, sizeof(v));
	return v;
}

static int is_cros(buffer_handle_t h)
{
	if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0)
		return 0;
	if (12 + 4 * (h->numFds + h->numInts) < CH_SIZE)
		return 0;
	return rd32(h, CH_MAGIC) == CROS_GRALLOC_MAGIC;
}

static int check(buffer_handle_t h)
{
	if (!h)
		return GE_NULL_HANDLE;
	return is_cros(h) ? GE_OK : GE_BAD_HANDLE;
}

static int hal_format(buffer_handle_t h)
{
	int32_t droid = (int32_t)rd32(h, CH_DROID_FORMAT);
	uint32_t drm = rd32(h, CH_FORMAT);

	if (droid != HAL_IMPLEMENTATION_DEFINED && droid != HAL_YCBCR_420_888)
		return droid;
	switch (drm) {
	case FOURCC('N', 'V', '1', '2'): return HAL_MTK_NV12;
	case FOURCC('N', 'V', '2', '1'): return HAL_YCRCB_420_SP;
	case FOURCC('Y', 'V', '1', '2'):
	case FOURCC('9', '9', '9', '7'): return HAL_YV12; /* YVU420_ANDROID */
	case FOURCC('A', 'B', '2', '4'): return HAL_RGBA_8888;
	case FOURCC('X', 'B', '2', '4'): return HAL_RGBX_8888;
	case FOURCC('A', 'R', '2', '4'): return HAL_BGRA_8888;
	case FOURCC('B', 'G', '2', '4'): return HAL_RGB_888;
	case FOURCC('R', 'G', '1', '6'): return HAL_RGB_565;
	case FOURCC('R', '8', ' ', ' '): return HAL_Y8;
	default: return droid;
	}
}

/* GED region sizes in 32-bit words (stock ged_ge_alloc(18, sizes)) */
#define NREGIONS 18
static const uint16_t region_words[NREGIONS] = { 1, 68, 16, 8, 15, 56, 2, 4, 16,
						 4, 643, 1, 15, 1, 24, 256, 1, 16 };

#define NENTRIES 192
struct meta {
	uint64_t ino;
	uint64_t stamp;
	uint32_t *region[NREGIONS];
};
static struct meta table[NENTRIES];
static uint64_t clock_;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static uint64_t buf_ino(buffer_handle_t h)
{
	struct stat st;

	if (fstat(h->data[0], &st) != 0)
		return 0;
	return (uint64_t)st.st_ino;
}

/* Caller holds lock. Returns NULL only on OOM or a bad fd. */
static uint32_t *region_get(buffer_handle_t h, int r)
{
	uint64_t ino = buf_ino(h);
	struct meta *m = NULL, *old = &table[0];
	int i;

	if (!ino)
		return NULL;
	for (i = 0; i < NENTRIES; i++) {
		if (table[i].ino == ino) {
			m = &table[i];
			break;
		}
		if (table[i].stamp < old->stamp)
			old = &table[i];
	}
	if (!m) {
		/* Evict the least recently used buffer (its fd/inode may be gone). */
		m = old;
		for (i = 0; i < NREGIONS; i++) {
			free(m->region[i]);
			m->region[i] = NULL;
		}
		m->ino = ino;
	}
	m->stamp = ++clock_;
	if (!m->region[r])
		m->region[r] = calloc(region_words[r], sizeof(uint32_t));
	return m->region[r];
}

static int region_io(buffer_handle_t h, int r, unsigned off, unsigned words, void *p, int set)
{
	uint32_t *reg;
	int ret = GE_OK;

	if (!p)
		return GE_NULL_HANDLE;
	if (off + words > region_words[r])
		return GE_NOT_SUPPORTED;
	pthread_mutex_lock(&lock);
	reg = region_get(h, r);
	if (!reg)
		ret = -6;
	else if (set)
		memcpy(reg + off, p, words * 4);
	else
		memcpy(p, reg + off, words * 4);
	pthread_mutex_unlock(&lock);
	return ret;
}

struct rmap {
	int16_t id, region, off, words;
};

static const struct rmap query_regions[] = {
	{ 100, 2, 0, 16 },  { 101, 1, 0, 68 },  { 102, 17, 0, 16 }, { 103, 3, 4, 1 },
	{ 106, 0, 0, 1 },   { 107, 4, 0, 15 },  { 108, 5, 0, 56 },  { 109, 6, 0, 2 },
	{ 110, 7, 0, 4 },   { 111, 8, 0, 2 },   { 112, 8, 0, 16 },  { 113, 9, 0, 4 },
	{ 114, 10, 0, 643 }, { 115, 11, 0, 1 }, { 116, 12, 0, 15 }, { 117, 13, 0, 1 },
	{ 118, 14, 0, 24 }, { 119, 15, 0, 256 }, { 120, 16, 0, 1 },
};

static const struct rmap perform_regions[] = {
	{ 100, 2, 0, 16 },  { 101, 1, 0, 68 },  { 102, 17, 0, 16 }, { 105, 0, 0, 1 },
	{ 106, 4, 0, 15 },  { 107, 5, 0, 56 },  { 108, 6, 0, 2 },   { 109, 7, 0, 4 },
	{ 110, 8, 0, 2 },   { 111, 8, 0, 16 },  { 112, 9, 0, 4 },   { 113, 10, 0, 643 },
	{ 114, 11, 0, 1 },  { 115, 12, 0, 15 }, { 116, 13, 0, 1 },  { 117, 14, 0, 24 },
	{ 118, 15, 0, 256 }, { 119, 16, 0, 1 },
};

static const struct rmap *find(const struct rmap *t, size_t n, int id)
{
	size_t i;

	for (i = 0; i < n; i++)
		if (t[i].id == id)
			return &t[i];
	return NULL;
}

static void warn_once(const char *what, int id)
{
	static unsigned char seen[2][128];
	int k = what[0] == 'q' ? 0 : 1;

	if (id >= 0 && id < 128) {
		if (seen[k][id])
			return;
		seen[k][id] = 1;
	}
	LOGW("unsupported %s id %d", what, id);
}

static int put_i32(void *p, int32_t v)
{
	memcpy(p, &v, sizeof(v));
	return GE_OK;
}

static int put_u64(void *p, uint64_t v)
{
	memcpy(p, &v, sizeof(v));
	return GE_OK;
}

int mainline_gralloc_extra_query(buffer_handle_t h, int attr, void *out)
{
	const struct rmap *m;
	uint32_t planes, s0;
	int ret = check(h);

	if (ret)
		return ret;
	if (!out)
		return GE_NULL_HANDLE;
	switch (attr) {
	case 1: return put_i32(out, h->data[0]);
	case 3:
		if (!(rd64(h, CH_USAGE) & USAGE_PROTECTED))
			return GE_NULL_HANDLE;
		return put_i32(out, 0);
	case 10: return put_i32(out, (int32_t)rd32(h, CH_WIDTH));
	case 11: return put_i32(out, (int32_t)rd32(h, CH_HEIGHT));
	case 12: return put_i32(out, (int32_t)rd32(h, CH_PIXEL_STRIDE));
	case 13:
		planes = rd32(h, CH_NUM_PLANES);
		s0 = rd32(h, CH_STRIDES);
		if (planes > 1 && s0 && rd32(h, CH_OFFSETS + 4) % s0 == 0)
			return put_i32(out, (int32_t)(rd32(h, CH_OFFSETS + 4) / s0));
		return put_i32(out, (int32_t)rd32(h, CH_HEIGHT));
	case 14: return put_i32(out, (int32_t)rd64(h, CH_TOTAL_SIZE));
	case 15:
	case 16: return put_i32(out, hal_format(h));
	case 17: return put_i32(out, (int32_t)rd64(h, CH_USAGE));
	case 51:
	case 52: return put_u64(out, rd64(h, CH_USAGE));
	case 53: return put_u64(out, buf_ino(h));
	}
	m = find(query_regions, sizeof(query_regions) / sizeof(query_regions[0]), attr);
	if (m)
		return region_io(h, m->region, m->off, m->words, out, 0);
	warn_once("query", attr);
	return GE_NOT_SUPPORTED;
}

int mainline_gralloc_extra_perform(buffer_handle_t h, int attr, void *in)
{
	const struct rmap *m;
	int ret = check(h);

	if (ret)
		return ret;
	m = find(perform_regions, sizeof(perform_regions) / sizeof(perform_regions[0]), attr);
	if (m)
		return region_io(h, m->region, m->off, m->words, in, 1);
	if (attr == 104) /* FREE_SEC_BUFFER_HWC: nothing was allocated */
		return GE_OK;
	warn_once("perform", attr);
	return GE_NOT_SUPPORTED;
}

int mainline_gralloc_extra_sf_set_status(void *sf_info, int32_t mask, int32_t value)
{
	int32_t *status = (int32_t *)((char *)sf_info + 0x24);

	*status = (*status & ~mask) | (value & mask);
	return GE_OK;
}

int mainline_gralloc_extra_sf_set_status2(void *sf_info, int32_t mask, int32_t value)
{
	int32_t *status2 = (int32_t *)((char *)sf_info + 0x38);

	*status2 = (*status2 & ~mask) | (value & mask);
	return GE_OK;
}

int mainline_gralloc_extra_need_resident(uint32_t usage)
{
	return (int)(usage & 0x60000);
}

/* Mirrors minigbm's format resolution (cros_gralloc_driver / drv_helpers). */
int mainline_gralloc_extra_get_platform_format(int format, uint64_t usage)
{
	if (format == HAL_YCBCR_420_888)
		return HAL_MTK_NV12;
	if (format == HAL_IMPLEMENTATION_DEFINED)
		return (usage & (USAGE_CAMERA_WRITE | USAGE_CAMERA_READ | USAGE_VIDEO_ENCODER)) ?
			       HAL_MTK_NV12 : HAL_RGBX_8888;
	return format;
}

/* GED entry points: only the stock MTK allocator/mapper use these. */
int mainline_ge_alloc(void) { return -1; }
int mainline_ge_retain(buffer_handle_t h) { (void)h; return 0; }
int mainline_ge_release(buffer_handle_t h) { (void)h; return 0; }
int mainline_ge_free(buffer_handle_t h) { (void)h; return 0; }
int mainline_ge_perform_alloc_sec_hwc(buffer_handle_t h, int ge_fd, void *p) { (void)h; (void)ge_fd; (void)p; return GE_NOT_SUPPORTED; }
int mainline_ge_perform_free_sec_hwc(buffer_handle_t h, int ge_fd, void *p) { (void)h; (void)ge_fd; (void)p; return 0; }
int mainline_ge_perform_ion_debug(buffer_handle_t h, int ge_fd, void *p) { (void)h; (void)ge_fd; (void)p; return 0; }
int mainline_ge_query_ion_debug(buffer_handle_t h, int ge_fd, void *p) { (void)h; (void)ge_fd; (void)p; return GE_NOT_SUPPORTED; }
