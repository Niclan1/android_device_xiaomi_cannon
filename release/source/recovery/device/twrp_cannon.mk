# SPDX-License-Identifier: Apache-2.0

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)
# Include the recovery defaults directly so the additional Lineage OTA key
# can be removed rather than imported through product list inheritance.
include vendor/twrp/config/common.mk
PRODUCT_EXTRA_RECOVERY_KEYS :=
$(call inherit-product, device/xiaomi/cannon/device.mk)

PRODUCT_DEVICE := cannon
PRODUCT_NAME := twrp_cannon
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := Redmi Note 9T
PRODUCT_MANUFACTURER := Xiaomi