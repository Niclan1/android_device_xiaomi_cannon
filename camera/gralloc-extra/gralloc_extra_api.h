/* SPDX-License-Identifier: Apache-2.0 */
#ifndef CANNON_GRALLOC_EXTRA_API_H
#define CANNON_GRALLOC_EXTRA_API_H
#include <stdint.h>
typedef struct { int version, numFds, numInts; int data[0]; } ge_native_handle_t;
typedef const ge_native_handle_t *buffer_handle_t;
int gralloc_extra_query(buffer_handle_t h, int attr, void *p);
int gralloc_extra_perform(buffer_handle_t h, int attr, void *p);
int gralloc_extra_sf_set_status(void *p, int32_t mask, int32_t value);
int gralloc_extra_sf_set_status2(void *p, int32_t mask, int32_t value);
int gralloc_extra_need_resident(uint32_t usage);
int gralloc_extra_get_platform_format(int format, uint64_t usage);
uint32_t ge_alloc(buffer_handle_t h);
int ge_retain(buffer_handle_t h, uint32_t ge);
int ge_release(buffer_handle_t h, uint32_t ge);
int ge_free(buffer_handle_t h);
int ge_perform_alloc_sec_hwc(buffer_handle_t h, uint32_t ge, void *p);
int ge_perform_free_sec_hwc(buffer_handle_t h, uint32_t ge, void *p);
int ge_perform_ion_debug(buffer_handle_t h, uint32_t ge, void *p);
int ge_query_ion_debug(buffer_handle_t h, uint32_t ge, void *p);
#endif
