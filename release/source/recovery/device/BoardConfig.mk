# SPDX-License-Identifier: Apache-2.0
#
# OrangeFox recovery for the Redmi Note 9T 5G (cannon/cannong, MT6853).
# The kernel, DTB and recovery DTBO are taken from the matching LineageOS
# build so recovery boots with the same Linux 6.18 kernel as the ROM.

DEVICE_PATH := device/xiaomi/cannon

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

TARGET_BOARD_PLATFORM := mt6853
TARGET_BOOTLOADER_BOARD_NAME := cannon
TARGET_NO_BOOTLOADER := true
TARGET_OTA_ASSERT_DEVICE := cannon,cannong
AB_OTA_UPDATER := false
TARGET_SCREEN_DENSITY := 440

# Kernel: everything recovery needs (UFS, F2FS, display, touch, USB) is built in.
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/Image.gz
BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/dtbo.img
BOARD_INCLUDE_RECOVERY_DTBO := true
BOARD_KERNEL_IMAGE_NAME := Image.gz
BOARD_BOOT_HEADER_VERSION := 2
BOARD_KERNEL_BASE := 0x40078000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_RAMDISK_OFFSET := 0x07c08000
BOARD_KERNEL_TAGS_OFFSET := 0x0bc08000
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 androidboot.usbconfigfs=true
BOARD_KERNEL_CMDLINE += androidboot.init_fatal_reboot_target=recovery
BOARD_KERNEL_CMDLINE += clk_ignore_unused pd_ignore_unused regulator_ignore_unused
BOARD_KERNEL_CMDLINE += mtk_cam.hw=1 mtk_cam.isp=1 mtk_cam.dip=1 mtk_cam.mdp=1 mtk_cam.flash=1
BOARD_KERNEL_CMDLINE += mtk_ion_compat.enable=1 mtk_ccci.hw=1 mtk_vcu.enable=1 mtk_vcu.vdec=1
BOARD_KERNEL_CMDLINE += page_owner=off initcall_debug=0 init_on_alloc=0 kfence.sample_interval=0
BOARD_KERNEL_CMDLINE += slub_debug=- log_buf_len=1M
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)
BOARD_MKBOOTIMG_ARGS += --dtb $(DEVICE_PATH)/prebuilt/dtb.img
BOARD_MKBOOTIMG_ARGS += --dtb_offset 0x01f00000

BOARD_AVB_ENABLE := true
BOARD_AVB_RECOVERY_ALGORITHM := SHA256_RSA4096
BOARD_AVB_RECOVERY_KEY_PATH := vendor/cannong-signing/avb.pk8
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := 1
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1

# Use the recovery branch's actual version and patch level.
BOOT_SECURITY_PATCH := $(PLATFORM_SECURITY_PATCH)

# Partitions
BOARD_FLASH_BLOCK_SIZE := 131072
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 134217728
BOARD_DTBOIMG_PARTITION_SIZE := 33554432
BOARD_CACHEIMAGE_PARTITION_SIZE := 452984832
BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
BOARD_SUPER_PARTITION_SIZE := 9126805504
BOARD_SUPER_PARTITION_GROUPS := xiaomi_dynamic_partitions
BOARD_XIAOMI_DYNAMIC_PARTITIONS_SIZE := 9122611200
BOARD_XIAOMI_DYNAMIC_PARTITIONS_PARTITION_LIST := system vendor product system_ext
BOARD_USES_METADATA_PARTITION := true
BOARD_ROOT_EXTRA_FOLDERS += metadata
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
TARGET_COPY_OUT_VENDOR := vendor

# Recovery
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery/root/system/etc/recovery.fstab
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TW_OEM_BUILD := true
TW_THEME := portrait_hdpi
TW_FRAMERATE := 60
TW_SCREEN_BLANK_ON_BOOT := true
TW_BRIGHTNESS_PATH := "/sys/class/leds/lcd-backlight/brightness"
TW_MAX_BRIGHTNESS := 2047
TW_DEFAULT_BRIGHTNESS := 1000
TW_EXTRA_LANGUAGES := true
TW_INCLUDE_NTFS_3G := false
TW_USE_TOOLBOX := true
TW_SKIP_ADDITIONAL_FSTAB := true
TW_EXCLUDE_APEX := true
TW_HAS_MTP := false
TW_EXCLUDE_MTP := true

# Sideload only: the test target does not expose encrypted personal storage.
TW_INCLUDE_CRYPTO := false
OF_FL_PATH1 := /sys/class/leds/white:flash-1
