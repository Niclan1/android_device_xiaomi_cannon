/*
 * Copyright (C) 2025 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <unistd.h>

#include <string>

#include <android-base/file.h>
#include <android-base/properties.h>
#include <android-base/strings.h>
#include <libinit_radio.h>
#include <libinit_utils.h>

#define RADIO_PROP "ro.boot.cannon.radio"
#define SKU_PROP "ro.boot.product.vendor.sku"
#define NORADIO_SKU "noradio"
#define CCCI_POWER_PARAM "/sys/module/mtk_ccci/parameters/power"

/*
 * The CCCI driver registers /sys/kernel/ccci and the ccci_node class
 * (ccci_monitor is the node the MD init daemons wait for). vendor_load_properties
 * runs before ueventd, so /dev is not populated yet: check sysfs first and
 * only fall back to the device node.
 */
static bool modem_present() {
    if (access("/sys/kernel/ccci", F_OK) != 0) return false;

    if (access("/sys/class/ccci_node/ccci_monitor", F_OK) != 0 &&
        access("/dev/ccci_monitor", F_OK) != 0)
        return false;

    /*
     * mtk_ccci.power=0 registers the nodes but never powers MD1 on: rild
     * would never be started by the gsm0710muxd chain while the framework
     * waits for the declared IRadio HAL, so treat it as no modem.
     */
    std::string power;
    if (android::base::ReadFileToString(CCCI_POWER_PARAM, &power) &&
        android::base::Trim(power) == "N")
        return false;

    return true;
}

/*
 * Telephony is on by default. The "noradio" vendor SKU is only a fallback for
 * kernels without the modem stack: it selects /vendor/etc/vintf/manifest_noradio.xml
 * (manifest_mainline_noradio.xml once set_graphics_stack() adds the kernel part;
 * no radio, mtkradioex or videotelephony HALs, so nothing waits for or lazily
 * starts them) and /vendor/etc/permissions/sku_*noradio (telephony features off).
 * The CannonNoRadioOverlay (ro.boot.cannon.radio=off) marks the device as not
 * voice/SMS/data capable but still creates the phone process, so apps that
 * query the "phone" service (dialer: isEmergencyNumber) keep working.
 * androidboot.cannon.radio=on|off overrides the detection.
 */
void set_radio_sku() {
    const std::string req = android::base::GetProperty(RADIO_PROP, "");
    bool radio;

    if (req == "on")
        radio = true;
    else if (req == "off")
        radio = false;
    else
        radio = modem_present();

    /* Publish the effective state, later stages only look at this property. */
    property_override(RADIO_PROP, radio ? "on" : "off");

    if (radio) return;

    if (android::base::GetProperty(SKU_PROP, "").empty())
        property_override(SKU_PROP, NORADIO_SKU);

    /* the audio HAL retries /dev/ccci_aud every 10 ms and logs each attempt */
    property_override("log.tag.SpeechMessengerNormal", "S");
}
