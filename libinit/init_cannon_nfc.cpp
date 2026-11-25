/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

#include <sys/utsname.h>
#include <unistd.h>

#include <cstdlib>

#include <android-base/properties.h>
#include <libinit_utils.h>

#include "vendor_init.h"

void select_mainline_nfc_sku() {
    struct utsname uts;
    if (uname(&uts) != 0 || std::atoi(uts.release) < 6) return;

    const auto hwc = android::base::GetProperty("ro.boot.hwc", "");
    if (hwc != "GL") return;

    if (!android::base::GetProperty("ro.boot.product.hardware.sku", "").empty()) return;

    // Probe must have validated the controller before publishing NFC features.
    if (access("/sys/class/misc/nq-nci", F_OK) != 0) return;

    property_override("ro.boot.product.hardware.sku", "nfc_mainline");
}
