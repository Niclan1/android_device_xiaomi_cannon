/*
 * Copyright (C) 2025 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <string>
#include <sys/utsname.h>

#include <cstdlib>

#include <android-base/properties.h>
#include <libinit_kernel.h>
#include <libinit_utils.h>

#define KERNEL_PROP "ro.vendor.cannon.kernel"

/*
 * legacy:   4.14 vendor kernel (MTK out-of-tree drivers, schedtune, GM30 gauge)
 * mainline: 6.x kernel (upstream drivers, uclamp, power_supply class gauge)
 * Init scripts use ro.vendor.cannon.kernel to skip what only works on 4.14.
 */
bool is_mainline_kernel() {
    struct utsname uts;

    if (uname(&uts) != 0) return false;

    return atoi(uts.release) >= 6;
}

void set_kernel_flavor() {
    const bool mainline = is_mainline_kernel();

    property_override(KERNEL_PROP, mainline ? "mainline" : "legacy");

    /*
     * The MTK Codec2 video codecs need vpud and the 4.14 vcodec/VCU drivers.
     * The mainline mtk-vcu driver runs vpud for both, so the hardware codecs
     * are the default. androidboot.cannon.vcodec=sw switches to the
     * media_codecs*_sw.xml variants (c2.android only) and the software ODM
     * manifest, and init.cannon.rc keeps vpud stopped. ro.vendor.cannon.vcodec tells init.cannon.rc.
     */
    const std::string boot_vcodec = android::base::GetProperty("ro.boot.cannon.vcodec", "");
    const std::string vcodec = !mainline ? "hw" : (boot_vcodec == "sw" || boot_vcodec == "enc")
            ? boot_vcodec : "hw";

    /* enc: hardware encoders only, decoding stays on the c2.android codecs. */
    property_override("ro.vendor.cannon.vcodec", vcodec);
    if (vcodec == "sw") {
        property_override("ro.camera.enableSWHEVC", "true");
        const std::string sku = android::base::GetProperty("ro.boot.product.hardware.sku", "");
        property_override("ro.boot.product.hardware.sku", sku.empty() ? "sw" : sku + "_sw");
    }
    if (vcodec != "hw") {
        property_override("ro.media.xml_variant.codecs", vcodec == "enc" ? "_enc" : "_sw");
        property_override("ro.media.xml_variant.codecs_performance", "_sw");
    }
}
