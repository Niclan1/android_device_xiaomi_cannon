#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/xiaomi/cannon

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-2a-dotprod
TARGET_CPU_ABI := arm64-v8a 
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a76

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-2a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

# Build system
BUILD_BROKEN_DUP_RULES := true
BUILD_BROKEN_ENFORCE_SYSPROP_OWNER := true
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

# APEX
DEXPREOPT_GENERATE_APEX_IMAGE := true

# OTA
TARGET_OTA_ASSERT_DEVICE := cannon,cannong
AB_OTA_UPDATER := false

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := cannon
TARGET_NO_BOOTLOADER := true

# Display
TARGET_SCREEN_DENSITY := 440

# Kernel
BOARD_BOOTIMG_HEADER_VERSION := 2
BOARD_KERNEL_BASE := 0x40078000
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 androidboot.usbconfigfs=true androidboot.init_fatal_reboot_target=recovery
# Match the stock 4.14 ramoops layout so recovery can read logs from failed boots.
# Mainline kernel: keep the clocks, power domains and regulators that the
# bootloader left on until every consumer has a driver.
BOARD_KERNEL_CMDLINE += clk_ignore_unused pd_ignore_unused regulator_ignore_unused
# MTK camera compat drivers (ISP, DIP, MDP, flash, seninf, imgsensor) are off
# unless asked for, so a kernel without the camera stack still boots cleanly.
BOARD_KERNEL_CMDLINE += mtk_cam.hw=1 mtk_cam.isp=1 mtk_cam.dip=1 mtk_cam.mdp=1 mtk_cam.flash=1
# The camera HAL still allocates and maps image buffers through legacy /dev/ion.
BOARD_KERNEL_CMDLINE += mtk_ion_compat.enable=1
# Modem (CCCI/DPMAIF/CCMNI) stack, needed for RIL, data, VoLTE and NR.
BOARD_KERNEL_CMDLINE += mtk_ccci.hw=1 mtk_vcu.enable=1 mtk_vcu.vdec=1
# The LK/DTB bootargs turn on page_owner and initcall_debug; both cost
# memory and boot/runtime overhead, so switch them back off.
BOARD_KERNEL_CMDLINE += page_owner=off initcall_debug=0 init_on_alloc=0 kfence.sample_interval=0
# Bring-up diagnostics, only in debug builds (TARGET_CANNON_DEBUG=true in the
# environment or a local makefile). Release builds boot enforcing with the
# default log level. Do not add initcall_debug, diag_bcb, slub_debug or
# page_owner to a release boot.img (slub_debug=OFZPU/initcall_debug/page_owner
# in /proc/cmdline come from the LK/DTB chosen bootargs, not from here).
TARGET_CANNON_DEBUG ?= false
ifeq ($(TARGET_CANNON_DEBUG),true)
BOARD_KERNEL_CMDLINE += androidboot.selinux=permissive loglevel=8 printk.devkmsg=on diag_blklog=expdb log_buf_len=8M
else
BOARD_KERNEL_CMDLINE += slub_debug=- log_buf_len=1M
endif
# Optional known-good 6.18 kernel for release zips: put Image.gz (and the
# matching *.ko in modules/) in CANNON_PREBUILT_KERNEL_DIR. Without it the
# kernel is built from TARGET_KERNEL_SOURCE as usual.
CANNON_PREBUILT_KERNEL_DIR ?= device/xiaomi/cannon-kernel
ifneq ($(wildcard $(CANNON_PREBUILT_KERNEL_DIR)/Image.gz),)
TARGET_PREBUILT_KERNEL := $(CANNON_PREBUILT_KERNEL_DIR)/Image.gz
TARGET_FORCE_PREBUILT_KERNEL := true
BOARD_VENDOR_KERNEL_MODULES := $(wildcard $(CANNON_PREBUILT_KERNEL_DIR)/modules/*.ko)
endif
BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilts/dtbo.img
BOARD_PREBUILT_DTBIMAGE := $(DEVICE_PATH)/prebuilts/dtb.img
BOARD_KERNEL_PAGESIZE := 2048
BOARD_RAMDISK_OFFSET := 0x07c08000
BOARD_KERNEL_TAGS_OFFSET := 0x0bc08000
BOARD_KERNEL_IMAGE_NAME := Image.gz
KERNEL_LD := LD=ld.lld
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)
BOARD_MKBOOTIMG_ARGS += --dtb $(BOARD_PREBUILT_DTBIMAGE)
# Keep the legacy v2 header version fields of the installed system. The boot
# patch level is part of the key attestation state and must not go backwards.
BOARD_MKBOOTIMG_ARGS += --os_version 13.0.0 --os_patch_level 2024-12
TARGET_KERNEL_CONFIG := cannong_defconfig
TARGET_KERNEL_SOURCE := kernel/xiaomi/cannon

# Partitions
BOARD_FLASH_BLOCK_SIZE := 131072 # (BOARD_KERNEL_PAGESIZE * 64)
BOARD_HAS_LARGE_FILESYSTEM := true
BOARD_CACHEIMAGE_PARTITION_SIZE := 452984832
BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_DTBOIMG_PARTITION_SIZE := 33554432
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 134217728
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SUPER_PARTITION_SIZE := 9126805504
BOARD_SUPER_PARTITION_GROUPS := xiaomi_dynamic_partitions
BOARD_XIAOMI_DYNAMIC_PARTITIONS_PARTITION_LIST := system vendor product system_ext
BOARD_XIAOMI_DYNAMIC_PARTITIONS_SIZE := $(shell expr $(BOARD_SUPER_PARTITION_SIZE) - 4194304)

BOARD_SYSTEMIMAGE_PARTITION_RESERVED_SIZE := 1258291200
BOARD_VENDORIMAGE_PARTITION_RESERVED_SIZE := 30720000
BOARD_PRODUCTIMAGE_PARTITION_RESERVED_SIZE := 1258291200
BOARD_SYSTEM_EXTIMAGE_PARTITION_RESERVED_SIZE := 1258291200

BOARD_SYSTEMIMAGE_EXTFS_INODE_COUNT := -1
BOARD_PRODUCTIMAGE_EXTFS_INODE_COUNT := -1
BOARD_SYSTEM_EXTIMAGE_EXTFS_INODE_COUNT := -1

BOARD_ROOT_EXTRA_FOLDERS += metadata
BOARD_USES_METADATA_PARTITION := true

TARGET_USES_MKE2FS := true
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_VENDOR := vendor

# Platform
TARGET_BOARD_PLATFORM := mt6853
BOARD_HAS_MTK_HARDWARE := true

# Init
TARGET_INIT_VENDOR_LIB := //$(DEVICE_PATH):init_cannon
TARGET_RECOVERY_DEVICE_MODULES := init_cannon
$(call soong_config_set,libinit,vendor_init_lib,//$(DEVICE_PATH):init_cannon_native)

# Properties
TARGET_SYSTEM_PROP += $(DEVICE_PATH)/system.prop
TARGET_PRODUCT_PROP += $(DEVICE_PATH)/product.prop
TARGET_VENDOR_PROP += $(DEVICE_PATH)/vendor.prop

# Recovery
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/rootdir/etc/fstab.mt6853
BOARD_INCLUDE_RECOVERY_DTBO := true
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_UI_BLANK_UNBLANK_ON_INIT := true
TARGET_RECOVERY_UI_MARGIN_HEIGHT := 60

# Sepolicy
include device/lineage/sepolicy/libion/sepolicy.mk
include device/mediatek/sepolicy_vndr/SEPolicy.mk
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/private

# RIL
ENABLE_VENDOR_RIL_SERVICE := true

# Security patch level
VENDOR_SECURITY_PATCH := 2023-10-01

# AVB
BOARD_AVB_ENABLE := true
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3
BOARD_AVB_RECOVERY_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_RECOVERY_ALGORITHM := SHA256_RSA2048
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := 1
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1
BOARD_AVB_VBMETA_SYSTEM := system
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA2048
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2
BOARD_AVB_VBMETA_VENDOR := vendor
BOARD_AVB_VBMETA_VENDOR_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_VBMETA_VENDOR_ALGORITHM := SHA256_RSA2048
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX_LOCATION := 4

# VINTF
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE := $(DEVICE_PATH)/configs/vintf/framework_compatibility_matrix.xml
DEVICE_MATRIX_FILE += $(DEVICE_PATH)/configs/vintf/compatibility_matrix.xml
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/manifest.xml
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/manifest_mtkgfx.xml
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/manifest_radio.xml
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/android.hardware.gnss-service-mediatek.xml
# Vendor SKUs (ro.boot.product.vendor.sku, set by libinit). The default is the
# 4.14 vendor kernel with the modem. "noradio" is the fallback for kernels
# without the CCCI modem stack or androidboot.cannon.radio=off; "mainline" is a
# 6.x kernel, which drops the HIDL MTK graphics HALs (manifest_mtkgfx.xml).
DEVICE_MANIFEST_SKUS += noradio mainline mainline_noradio
DEVICE_MANIFEST_NORADIO_FILES := \
    $(DEVICE_PATH)/configs/vintf/manifest.xml \
    $(DEVICE_PATH)/configs/vintf/manifest_mtkgfx.xml \
    $(DEVICE_PATH)/configs/vintf/android.hardware.gnss-service-mediatek.xml
DEVICE_MANIFEST_MAINLINE_FILES := \
    $(DEVICE_PATH)/configs/vintf/manifest_gralloc4.xml \
    $(DEVICE_PATH)/configs/vintf/manifest.xml \
    $(DEVICE_PATH)/configs/vintf/manifest_radio.xml \
    $(DEVICE_PATH)/configs/vintf/android.hardware.gnss-service-mediatek.xml
DEVICE_MANIFEST_MAINLINE_NORADIO_FILES := \
    $(DEVICE_PATH)/configs/vintf/manifest_gralloc4.xml \
    $(DEVICE_PATH)/configs/vintf/manifest.xml \
    $(DEVICE_PATH)/configs/vintf/android.hardware.gnss-service-mediatek.xml
ODM_MANIFEST_SKUS += nfc nfc_mainline sw nfc_sw nfc_mainline_sw
ODM_MANIFEST_NFC_FILES := $(DEVICE_PATH)/configs/vintf/manifest_nfc.xml
ODM_MANIFEST_NFC_MAINLINE_FILES := $(DEVICE_PATH)/configs/vintf/manifest_nfc_mainline.xml
ODM_MANIFEST_SW_FILES := $(DEVICE_PATH)/configs/vintf/manifest_vcodec_sw.xml
ODM_MANIFEST_NFC_SW_FILES := \
    $(DEVICE_PATH)/configs/vintf/manifest_nfc.xml \
    $(DEVICE_PATH)/configs/vintf/manifest_vcodec_sw.xml
ODM_MANIFEST_NFC_MAINLINE_SW_FILES := \
    $(DEVICE_PATH)/configs/vintf/manifest_nfc_mainline.xml \
    $(DEVICE_PATH)/configs/vintf/manifest_vcodec_sw.xml

# Releasetools
TARGET_RELEASETOOLS_EXTENSIONS := $(DEVICE_PATH)

# WiFi
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_HOSTAPD_DRIVER := NL80211
WIFI_DRIVER_FW_PATH_PARAM := "/dev/wmtWifi"
WIFI_DRIVER_FW_PATH_STA := "STA"
WIFI_DRIVER_FW_PATH_AP := "AP"
WIFI_DRIVER_FW_PATH_P2P := "P2P"
WIFI_DRIVER_STATE_CTRL_PARAM := "/dev/wmtWifi"
WIFI_DRIVER_STATE_ON := "1"
WIFI_DRIVER_STATE_OFF := "0"
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY := true
WIFI_HIDL_FEATURE_DUAL_INTERFACE := true

# Inherit the proprietary files
include vendor/xiaomi/cannon/BoardConfigVendor.mk

# Retain cannon musb-hdrc/rndis initialization instead of the generic gadget rc.
$(call soong_config_set,mediatek_gadget,use_custom_usb_gadget_rc,true)

# Parse power hints after post-fs-data mounts, on either kernel.
$(call soong_config_set,power_libperfmgr,service_init_rc,//device/xiaomi/cannon:cannon_power_service_init_rc)
