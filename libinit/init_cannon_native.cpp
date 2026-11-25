/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

#include "vendor_init.h"

void select_mainline_nfc_sku();
void select_mainline_gauge();
void set_graphics_stack();
void set_kernel_flavor();

void vendor_load_properties() {
#ifndef RECOVERY
    select_mainline_nfc_sku();
    set_kernel_flavor();
    select_mainline_gauge();
    set_graphics_stack();
#endif
}
