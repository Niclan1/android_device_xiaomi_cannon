#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common Lineage stuff.
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# Inherit from cannon device
$(call inherit-product, device/xiaomi/cannon/device.mk)

PRODUCT_DEVICE := cannon
PRODUCT_NAME := lineage_cannon
PRODUCT_BRAND := Redmi
# This diagnostic candidate targets the enrolled GL board. Keep the shared build target.
PRODUCT_MODEL := M2007J22G
PRODUCT_SYSTEM_DEVICE := cannong
# CCCI modem RPC reads the vendor device identity; do not substitute a stock fingerprint.
PRODUCT_BUILD_PROP_OVERRIDES += DeviceName=cannong
PRODUCT_MANUFACTURER := Xiaomi

PRODUCT_GMS_CLIENTID_BASE := android-xiaomi

# Build descriptions and fingerprints come from this actual Android17 build.
