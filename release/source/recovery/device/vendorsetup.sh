# SPDX-License-Identifier: Apache-2.0

if [[ ${1:-${FOX_BUILD_DEVICE:-}} == cannon ]]; then
    export FOX_BUILD_DEVICE=cannon
    export FOX_VANILLA_BUILD=1
    export FOX_DELETE_MAGISK_ADDON=1
    export FOX_RECOVERY_INSTALL_PARTITION=/dev/block/by-name/recovery
    export FOX_RECOVERY_BOOT_PARTITION=/dev/block/by-name/boot
    export FOX_USE_TAR_BINARY=1
    export OF_MAINTAINER=Niclan
    export FOX_BUILD_TYPE=Unofficial
    export OF_DONT_PATCH_ENCRYPTED_DEVICE=1
    export OF_SCREEN_H=2340
    export OF_STATUS_H=80
    export OF_STATUS_INDENT_LEFT=48
    export OF_STATUS_INDENT_RIGHT=48
    export OF_ALLOW_DISABLE_NAVBAR=0
fi