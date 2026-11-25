/*
 * Copyright (C) 2025 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <sys/utsname.h>
#include <unistd.h>

#include <cstdlib>
#include <string>

#include <android-base/properties.h>
#include <libinit_graphics.h>
#include <libinit_utils.h>

#define GFX_STACK_PROP "ro.vendor.cannon.gfx"
#define VENDOR_SKU_PROP "ro.boot.product.vendor.sku"
#define APEX_SELECT_PROP(apex) "ro.boot.vendor.apex." apex

#define COMPOSER_APEX "com.android.hardware.graphics.composer"
#define COMPOSER_APEX_DRM "com.android.hardware.graphics.composer.drm_hwcomposer"
#define GRALLOC_APEX "com.xiaomi.cannon.gralloc"

/*
 * The legacy 4.14 vendor kernel ships the MTK display/Mali drivers that the
 * proprietary HWC, gralloc and GPU blobs need. Mainline (6.x) kernels only
 * provide upstream mediatek-drm, so switch to drm_hwcomposer, minigbm and
 * Mesa panfrost (or ANGLE/SwiftShader) there. This runs before apexd-bootstrap
 * and early-init.
 */
static bool is_mainline_kernel() {
    struct utsname uts;

    if (uname(&uts) != 0) return false;

    return atoi(uts.release) >= 6;
}

void set_graphics_stack() {
    if (!is_mainline_kernel()) {
        property_override(GFX_STACK_PROP, "legacy");
        property_override(APEX_SELECT_PROP(COMPOSER_APEX), "none");
        property_override(APEX_SELECT_PROP(GRALLOC_APEX), "none");
        return;
    }

    property_override("vendor.debug.pd.vpu.enable", "0");

    /*
     * Mainline has no ashmem driver (it needs Rust), so make libcutils fall
     * back to sealed memfds. Without it system_server dies creating
     * ApplicationSharedMemory.
     */
    property_override("sys.use_memfd", "true");
    property_override(GFX_STACK_PROP, "mainline");
    property_override(APEX_SELECT_PROP(COMPOSER_APEX), COMPOSER_APEX_DRM);
    property_override(APEX_SELECT_PROP(GRALLOC_APEX), GRALLOC_APEX);

    /*
     * Mesa panfrost is the default GLES driver, androidboot.cannon.egl=angle
     * keeps ANGLE/SwiftShader as the opt-out (also used if the Mesa prebuilts
     * were not installed).
     */
    const bool mesa = android::base::GetProperty("ro.boot.cannon.egl", "") != "angle" &&
                      access("/vendor/lib64/egl/libEGL_mesa.so", F_OK) == 0;
    property_override("ro.hardware.egl", mesa ? "mesa" : "angle");

    /*
     * Mesa's u_gralloc prefers the CrOS gralloc0 API: the minigbm gralloc0
     * module reports fourcc, modifier and per-plane fds/offsets/strides of the
     * buffers the minigbm allocator hands out, which is what YUV (NV12/YV12)
     * imports need. Without it Mesa guesses RGB layouts only ("Using fallback
     * gralloc implementation"). Its EGLImage imports still fail on panfrost
     * (EGL_BAD_ALLOC for RGBA scanout buffers), so it is opt-in with
     * androidboot.cannon.gralloc0=on.
     */
    if (mesa && android::base::GetProperty("ro.boot.cannon.gralloc0", "") == "on" &&
        access("/vendor/lib64/hw/gralloc.minigbm.so", F_OK) == 0)
        property_override("ro.hardware.gralloc", "minigbm");

    /*
     * panvk does not support Valhall v9 (G57), so Vulkan stays on the
     * software driver. Never let SurfaceFlinger pick it for RenderEngine.
     */
    property_override("ro.hardware.vulkan", "pastel");
    property_override("debug.renderengine.backend", "skiaglthreaded");
    property_override("ro.opengles.version", "196609");

    /*
     * vendor.prop carries the MTK HWC tuning: 27.6 ms SF + 20 ms app work
     * durations (almost three vsyncs of touch-to-display latency at 60 Hz),
     * a 23 ms HWC minimum and the client composition cache disabled.
     * drm_hwcomposer composites on the GPU, so go back to the AOSP defaults
     * (one vsync each) and let SF reuse unchanged client targets.
     */
    for (const char* phase : {"late", "early", "earlyGl"}) {
        property_override(std::string("debug.sf.") + phase + ".sf.duration", "15600000");
        property_override(std::string("debug.sf.") + phase + ".app.duration", "16600000");
    }
    property_override("debug.sf.hwc.min.duration", "0");
    property_override("debug.sf.disable_client_composition_cache", "0");
    property_override("debug.sf.predict_hwc_composition_strategy", "1");

    property_override("ro.surface_flinger.has_HDR_display", "false");
    property_override("ro.surface_flinger.has_wide_color_display", "false");
    property_override("ro.surface_flinger.protected_contents", "false");
    property_override("ro.surface_flinger.use_color_management", "false");

    /*
     * The HIDL allocator/mapper/composer of the MTK display blobs are only
     * declared by manifest_mtkgfx.xml, which the "mainline" vendor SKUs leave
     * out: hwservicemanager would otherwise lazily restart the crashing
     * gralloc service for every client. The radio part of the SKU comes from
     * set_radio_sku(), which runs first.
     */
    const std::string sku = android::base::GetProperty(VENDOR_SKU_PROP, "");
    if (sku.empty())
        property_override(VENDOR_SKU_PROP, "mainline");
    else if (sku == "noradio")
        property_override(VENDOR_SKU_PROP, "mainline_noradio");
}
