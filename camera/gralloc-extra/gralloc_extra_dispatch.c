/* SPDX-License-Identifier: Apache-2.0 */
#include "gralloc_extra_api.h"
#include <android/log.h>
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>

#define LEGACY_NAME "libgralloc_extra_cannon_legacy.so"
static pthread_once_t once = PTHREAD_ONCE_INIT;
static int route = -1;
static void *legacy;
static void loader_error(const char *what) {
    const char *error = dlerror();
    __android_log_print(ANDROID_LOG_ERROR, "gralloc_extra_cannon", "%s: %s", what, error ? error : "invalid kernel selector");
}
extern int mainline_gralloc_extra_query(buffer_handle_t h, int attr, void *p);
static int (*legacy_gralloc_extra_query)(buffer_handle_t h, int attr, void *p);
extern int mainline_gralloc_extra_perform(buffer_handle_t h, int attr, void *p);
static int (*legacy_gralloc_extra_perform)(buffer_handle_t h, int attr, void *p);
extern int mainline_gralloc_extra_sf_set_status(void *p, int32_t mask, int32_t value);
static int (*legacy_gralloc_extra_sf_set_status)(void *p, int32_t mask, int32_t value);
extern int mainline_gralloc_extra_sf_set_status2(void *p, int32_t mask, int32_t value);
static int (*legacy_gralloc_extra_sf_set_status2)(void *p, int32_t mask, int32_t value);
extern int mainline_gralloc_extra_need_resident(uint32_t usage);
static int (*legacy_gralloc_extra_need_resident)(uint32_t usage);
extern int mainline_gralloc_extra_get_platform_format(int format, uint64_t usage);
static int (*legacy_gralloc_extra_get_platform_format)(int format, uint64_t usage);
extern int mainline_ge_alloc(void);
static uint32_t (*legacy_ge_alloc)(buffer_handle_t h);
extern int mainline_ge_retain(buffer_handle_t h);
static int (*legacy_ge_retain)(buffer_handle_t h, uint32_t ge);
extern int mainline_ge_release(buffer_handle_t h);
static int (*legacy_ge_release)(buffer_handle_t h, uint32_t ge);
extern int mainline_ge_free(buffer_handle_t h);
static int (*legacy_ge_free)(buffer_handle_t h);
extern int mainline_ge_perform_alloc_sec_hwc(buffer_handle_t h, int ge, void *p);
static int (*legacy_ge_perform_alloc_sec_hwc)(buffer_handle_t h, uint32_t ge, void *p);
extern int mainline_ge_perform_free_sec_hwc(buffer_handle_t h, int ge, void *p);
static int (*legacy_ge_perform_free_sec_hwc)(buffer_handle_t h, uint32_t ge, void *p);
extern int mainline_ge_perform_ion_debug(buffer_handle_t h, int ge, void *p);
static int (*legacy_ge_perform_ion_debug)(buffer_handle_t h, uint32_t ge, void *p);
extern int mainline_ge_query_ion_debug(buffer_handle_t h, int ge, void *p);
static int (*legacy_ge_query_ion_debug)(buffer_handle_t h, uint32_t ge, void *p);

static void select_route(void) {
    struct utsname uts;
    if (uname(&uts) != 0) { loader_error("uname"); return; }
    if (strncmp(uts.release, "6.18.", 5) == 0) { route = 1; return; }
    if (strncmp(uts.release, "4.14.", 5) != 0) { loader_error("unsupported kernel"); return; }
    legacy = dlopen(LEGACY_NAME, RTLD_NOW | RTLD_LOCAL);
    if (!legacy) { loader_error(LEGACY_NAME); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_query) = dlsym(legacy, "gralloc_extra_query");
    if (!legacy_gralloc_extra_query) { loader_error("gralloc_extra_query"); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_perform) = dlsym(legacy, "gralloc_extra_perform");
    if (!legacy_gralloc_extra_perform) { loader_error("gralloc_extra_perform"); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_sf_set_status) = dlsym(legacy, "gralloc_extra_sf_set_status");
    if (!legacy_gralloc_extra_sf_set_status) { loader_error("gralloc_extra_sf_set_status"); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_sf_set_status2) = dlsym(legacy, "gralloc_extra_sf_set_status2");
    if (!legacy_gralloc_extra_sf_set_status2) { loader_error("gralloc_extra_sf_set_status2"); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_need_resident) = dlsym(legacy, "gralloc_extra_need_resident");
    if (!legacy_gralloc_extra_need_resident) { loader_error("gralloc_extra_need_resident"); return; }
    dlerror();
    *(void **)(&legacy_gralloc_extra_get_platform_format) = dlsym(legacy, "gralloc_extra_get_platform_format");
    if (!legacy_gralloc_extra_get_platform_format) { loader_error("gralloc_extra_get_platform_format"); return; }
    dlerror();
    *(void **)(&legacy_ge_alloc) = dlsym(legacy, "ge_alloc");
    if (!legacy_ge_alloc) { loader_error("ge_alloc"); return; }
    dlerror();
    *(void **)(&legacy_ge_retain) = dlsym(legacy, "ge_retain");
    if (!legacy_ge_retain) { loader_error("ge_retain"); return; }
    dlerror();
    *(void **)(&legacy_ge_release) = dlsym(legacy, "ge_release");
    if (!legacy_ge_release) { loader_error("ge_release"); return; }
    dlerror();
    *(void **)(&legacy_ge_free) = dlsym(legacy, "ge_free");
    if (!legacy_ge_free) { loader_error("ge_free"); return; }
    dlerror();
    *(void **)(&legacy_ge_perform_alloc_sec_hwc) = dlsym(legacy, "ge_perform_alloc_sec_hwc");
    if (!legacy_ge_perform_alloc_sec_hwc) { loader_error("ge_perform_alloc_sec_hwc"); return; }
    dlerror();
    *(void **)(&legacy_ge_perform_free_sec_hwc) = dlsym(legacy, "ge_perform_free_sec_hwc");
    if (!legacy_ge_perform_free_sec_hwc) { loader_error("ge_perform_free_sec_hwc"); return; }
    dlerror();
    *(void **)(&legacy_ge_perform_ion_debug) = dlsym(legacy, "ge_perform_ion_debug");
    if (!legacy_ge_perform_ion_debug) { loader_error("ge_perform_ion_debug"); return; }
    dlerror();
    *(void **)(&legacy_ge_query_ion_debug) = dlsym(legacy, "ge_query_ion_debug");
    if (!legacy_ge_query_ion_debug) { loader_error("ge_query_ion_debug"); return; }
    route = 0;
}

int gralloc_extra_query(buffer_handle_t h, int attr, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_query(h, attr, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_gralloc_extra_query(h, attr, p);
}

int gralloc_extra_perform(buffer_handle_t h, int attr, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_perform(h, attr, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_gralloc_extra_perform(h, attr, p);
}

int gralloc_extra_sf_set_status(void *p, int32_t mask, int32_t value) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_sf_set_status(p, mask, value);
    return (int)mainline_gralloc_extra_sf_set_status(p, mask, value);
}

int gralloc_extra_sf_set_status2(void *p, int32_t mask, int32_t value) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_sf_set_status2(p, mask, value);
    return (int)mainline_gralloc_extra_sf_set_status2(p, mask, value);
}

int gralloc_extra_need_resident(uint32_t usage) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_need_resident(usage);
    return (int)mainline_gralloc_extra_need_resident(usage);
}

int gralloc_extra_get_platform_format(int format, uint64_t usage) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_gralloc_extra_get_platform_format(format, usage);
    return (int)mainline_gralloc_extra_get_platform_format(format, usage);
}

uint32_t ge_alloc(buffer_handle_t h) {
    pthread_once(&once, select_route);
    if (route < 0) return UINT32_MAX;
    if (!route) return legacy_ge_alloc(h);
    if (!h) return UINT32_MAX;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return UINT32_MAX;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return UINT32_MAX;
    return (uint32_t)mainline_ge_alloc();
}

int ge_retain(buffer_handle_t h, uint32_t ge) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_retain(h, ge);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    (void)ge;
    return (int)mainline_ge_retain(h);
}

int ge_release(buffer_handle_t h, uint32_t ge) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_release(h, ge);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    (void)ge;
    return (int)mainline_ge_release(h);
}

int ge_free(buffer_handle_t h) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_free(h);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_ge_free(h);
}

int ge_perform_alloc_sec_hwc(buffer_handle_t h, uint32_t ge, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_perform_alloc_sec_hwc(h, ge, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_ge_perform_alloc_sec_hwc(h, ge, p);
}

int ge_perform_free_sec_hwc(buffer_handle_t h, uint32_t ge, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_perform_free_sec_hwc(h, ge, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_ge_perform_free_sec_hwc(h, ge, p);
}

int ge_perform_ion_debug(buffer_handle_t h, uint32_t ge, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_perform_ion_debug(h, ge, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_ge_perform_ion_debug(h, ge, p);
}

int ge_query_ion_debug(buffer_handle_t h, uint32_t ge, void *p) {
    pthread_once(&once, select_route);
    if (route < 0) return (int)-ENODEV;
    if (!route) return legacy_ge_query_ion_debug(h, ge, p);
    if (!h) return (int)-5;
    if (h->version != 12 || h->numFds < 1 || h->numFds > 5 || h->numInts < 0 || h->numInts > 1024 ||
        (uint64_t)h->numFds + h->numInts < 36) return (int)7;
    uint32_t magic;
    memcpy(&magic, (const char *)h + 116, sizeof(magic));
    if (magic != 0xABCDDCBAu) return (int)7;
    return (int)mainline_ge_query_ion_debug(h, ge, p);
}
