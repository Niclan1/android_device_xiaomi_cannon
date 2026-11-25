/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

#include <sys/utsname.h>

#include <cerrno>
#include <cstdlib>
#include <string>

#include <android-base/file.h>
#include <android-base/logging.h>
#include <android-base/properties.h>
#include <libinit_utils.h>

void select_mainline_gauge() {
    struct utsname uts;
    if (uname(&uts) != 0) {
        PLOG(ERROR) << "Cannot identify kernel for gauge selection";
        return;
    }
    char* end;
    errno = 0;
    const auto major = std::strtol(uts.release, &end, 10);
    if (errno || end == uts.release || *end != '.' || major < 0) {
        LOG(ERROR) << "Invalid kernel release for gauge selection";
        return;
    }
    if (major < 6) return;

    const auto bootmode = android::base::GetProperty(
            "ro.bootmode", android::base::GetProperty("ro.boot.mode", ""));
    if (bootmode == "charger" || bootmode == "recovery") return;

    if (!android::base::GetProperty("ro.vendor.cannon.gauge", "").empty()) {
        LOG(INFO) << "Keeping existing gauge selection";
        return;
    }

    std::string driver;
    if (!android::base::Realpath("/sys/class/power_supply/battery/device/driver", &driver)) {
        if (errno == ENOENT) {
            LOG(INFO) << "Battery driver not ready; keeping vendor gauge policy";
        } else {
            PLOG(ERROR) << "Cannot resolve battery driver; keeping vendor gauge policy";
        }
        return;
    }
    if (driver != "/sys/bus/platform/drivers/mt6853-battery") {
        LOG(INFO) << "Battery driver differs; keeping vendor gauge policy";
        return;
    }

    property_override("ro.vendor.cannon.gauge", "upstream");
    if (android::base::GetProperty("ro.vendor.cannon.gauge", "") != "upstream") {
        LOG(ERROR) << "Cannot publish native gauge selection";
        return;
    }
    LOG(INFO) << "Using bound mt6853 battery monitor without GM30 daemons";
}
