#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3

#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
from pq_elf_phdr import repair as repair_phdr
from extract_utils.tools import DEFAULT_PATCHELF_VERSION, patchelf_version_path_map
from extract_utils.utils import run_cmd

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)

from extract_utils.fixups_lib import (
    lib_fixup_remove_arch_suffix,
    lib_fixup_vendorcompat,
    lib_fixups_user_type,
    libs_clang_rt_ubsan,
    libs_proto_3_9_1,
)

from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/xiaomi/cannon',
    'hardware/mediatek',
    'hardware/mediatek/libmtkperf_client',
    'hardware/xiaomi',
]

lib_fixups: lib_fixups_user_type = {
    'libformatter': lambda lib, partition: 'libformatter-cannon' if partition == 'vendor' else lib,
    'libmnl': lambda lib, partition: 'libmnl-cannon' if partition == 'vendor' else lib,
    libs_clang_rt_ubsan: lib_fixup_remove_arch_suffix,
    libs_proto_3_9_1: lib_fixup_vendorcompat,
}

def pq_tinyxml_abi_fixup(ctx, file, file_path, *args, **kwargs):
    # Pin the device's 4KiB layout, then restore PT_PHDR's actual mapped address.
    # patchelf 0.17/0.18 can retain a stale virtual bias after moving this table.
    run_cmd([
        patchelf_version_path_map[DEFAULT_PATCHELF_VERSION],
        '--page-size', '4096',
        '--replace-needed', 'libtinyxml2.so', 'libtinyxml2-v34.so',
        file_path,
    ])
    path = Path(file_path)
    fixed, _ = repair_phdr(path.read_bytes())
    path.write_bytes(fixed)


blob_fixups: blob_fixups_user_type = {

    (
        'vendor/lib/libpkm.so',
        'vendor/lib64/libpkm.so',
    ): blob_fixup().add_needed('libshim_cannon_pcap.so'),


    (
        'system/lib/libaudio_param_parser-sys.so',
        'system/lib64/libaudio_param_parser-sys.so',
        'system/lib64/libem_audio_jni.so',
    ): blob_fixup().replace_needed('libaudioclient.so', 'libaudiobase.so'),


    (
        'system_ext/lib/libaudiotoolkit.so',
        'system_ext/lib64/libaudiotoolkit.so',
    ): blob_fixup().replace_needed('libaudioclient.so', 'libaudiobase.so'),


    'system/priv-app/ImsService/ImsService.apk': blob_fixup()
        .apktool_patch('blob-patches/ImsService'),

    'system/priv-app/LPPeService/LPPeService.apk': blob_fixup()
        .apktool_patch('blob-patches/LPPeService'),

    'system/lib64/libsource.so': blob_fixup()
        .add_needed('libui_shim.so'),

    'system/lib64/libsink-mtk.so': blob_fixup()
        .add_needed('libaudioclient_shim.so'),

    'system/lib64/libimsma.so': blob_fixup()
        .replace_needed('libsink.so', 'libsink-mtk.so'),        

    (
        'system/lib/libem_support_jni.so',
        'system/lib64/libem_support_jni.so',
    ): blob_fixup()
        .add_needed('libgui_cannon_shim.so'),

    'vendor/bin/hw/android.hardware.thermal@2.0-service.mtk': blob_fixup()
        .replace_needed('libutils.so', 'libutils-v32.so')
        .replace_needed('libhidlbase.so', 'libhidlbase-v32.so'),

    (
        'vendor/bin/hw/camerahalserver',
        'vendor/lib64/libmtkcam_stdutils.so',
        'vendor/lib64/hw/android.hardware.camera.provider@2.6-impl-mediatek.so',
    ): blob_fixup()
        .replace_needed('libutils.so', 'libutils-v32.so'),

    # Legacy PQ allocates the VNDK34-sized XMLDocument (776 bytes).
    # Keep the uniquely named maintained ABI, as other MediaTek Lineage devices do.
    (
        'vendor/lib/hw/vendor.mediatek.hardware.pq@2.13-impl.so',
        'vendor/lib64/hw/vendor.mediatek.hardware.pq@2.13-impl.so',
    ): blob_fixup()
        .replace_needed('libutils.so', 'libutils-v32.so')
        .call(pq_tinyxml_abi_fixup),

    (
        'vendor/bin/mnld',
        'vendor/lib/libaalservice.so',
        'vendor/lib64/libaalservice.so',
        'vendor/lib/librgbwlightsensor.so',
        'vendor/lib64/librgbwlightsensor.so',
        'vendor/lib64/libcam.utils.sensorprovider.so',
    ): blob_fixup()
        .replace_needed(
            'libsensorndkbridge.so',
            'android.hardware.sensors@1.0-convert-shared.so',
        ),

    'vendor/lib/hw/audio.primary.mt6853.so': blob_fixup()
        .replace_needed('libalsautils.so', 'libalsautils-v31.so'),

    'vendor/etc/vintf/manifest/manifest_media_c2_V1_2_default.xml': blob_fixup()
        .regex_replace('1.1', '1.2'),

    'vendor/bin/hw/android.hardware.media.c2@1.2-mediatek-64b': blob_fixup()
        .add_needed('libstagefright_foundation-v33.so')
        .replace_needed(
            'libavservices_minijail_vendor.so',
            'libavservices_minijail.so',
        )

        .replace_needed(
            'libcodec2_hidl@1.0.so',
            'libcodec2_hidl@1.0-v31.so',
        )
        .replace_needed(
            'libcodec2_hidl@1.1.so',
            'libcodec2_hidl@1.1-v31.so',
        )
        .replace_needed(
            'libcodec2_hidl@1.2.so',
            'libcodec2_hidl@1.2-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        ),

    'vendor/lib64/libcodec2_hidl@1.0-v31.so': blob_fixup()
        .replace_needed(
            'libstagefright_bufferqueue_helper.so',
            'libstagefright_bufferqueue_helper-v33.so',
        )
        .replace_needed(
            'libcodec2_hidl_plugin.so',
            'libcodec2_hidl_plugin-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libui.so',
            'libui-v30.so',
        )
        .add_needed('libbase_shim.so'),

    'vendor/lib64/libcodec2_hidl@1.1-v31.so': blob_fixup()
        .replace_needed(
            'libstagefright_bufferqueue_helper.so',
            'libstagefright_bufferqueue_helper-v33.so',
        )
        .replace_needed(
            'libcodec2_hidl@1.0.so',
            'libcodec2_hidl@1.0-v31.so',
        )
        .replace_needed(
            'libcodec2_hidl_plugin.so',
            'libcodec2_hidl_plugin-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libui.so',
            'libui-v30.so',
        )
        .add_needed('libbase_shim.so'),

    'vendor/lib64/libcodec2_hidl@1.2-v31.so': blob_fixup()
        .replace_needed(
            'libstagefright_bufferqueue_helper.so',
            'libstagefright_bufferqueue_helper-v33.so',
        )
        .replace_needed(
            'libcodec2_hidl@1.0.so',
            'libcodec2_hidl@1.0-v31.so',
        )
        .replace_needed(
            'libcodec2_hidl@1.1.so',
            'libcodec2_hidl@1.1-v31.so',
        )
        .replace_needed(
            'libcodec2_hidl_plugin.so',
            'libcodec2_hidl_plugin-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libui.so',
            'libui-v30.so',
        )
        .add_needed('libbase_shim.so'),

    'vendor/lib64/libcodec2_hidl_plugin-v31.so': blob_fixup()
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        ),

    (
        'vendor/lib64/libcodec2_mtk_c2store.so',
        'vendor/lib64/libcodec2_vpp_qt_plugin.so',
        'vendor/lib64/libcodec2_vpp_rs_plugin.so',
    ): blob_fixup()
        .replace_needed(
            'libcodec2_soft_common.so',
            'libcodec2_soft_common-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libstagefright_foundation.so',
            'libstagefright_foundation-v33.so',
        )
        .replace_needed(
            'libsfplugin_ccodec_utils.so',
            'libsfplugin_ccodec_utils-v31.so',
        ),

    (
        'vendor/lib64/libcodec2_mtk_vdec.so',
        'vendor/lib64/libcodec2_mtk_venc.so',
    ): blob_fixup()
        .replace_needed(
            'libcodec2_soft_common.so',
            'libcodec2_soft_common-v31.so',
        )
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libstagefright_foundation.so',
            'libstagefright_foundation-v33.so',
        )
        .replace_needed(
            'libsfplugin_ccodec_utils.so',
            'libsfplugin_ccodec_utils-v31.so',
        )
        .replace_needed(
            'libui.so',
            'libui-v30.so',
        ),

    (
        'vendor/lib64/libcodec2_soft_mtk_alacdec.so',
        'vendor/lib64/libcodec2_soft_mtk_apedec.so',
        'vendor/lib64/libcodec2_soft_mtk_imaadpcmdec.so',
        'vendor/lib64/libcodec2_soft_mtk_mp3dec.so',
        'vendor/lib64/libcodec2_soft_mtk_msadpcmdec.so'
    ): blob_fixup()
        .replace_needed('libcodec2_soft_common.so', 'libcodec2_soft_common-v31.so')
        .replace_needed('libcodec2_vndk.so', 'libcodec2_vndk-v31.so')
        .replace_needed('libstagefright_foundation.so', 'libstagefright_foundation-v33.so'),

    'vendor/lib64/libcodec2_soft_common-v31.so': blob_fixup()
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        )
        .replace_needed(
            'libstagefright_foundation.so',
            'libstagefright_foundation-v33.so',
        )
        .replace_needed(
            'libsfplugin_ccodec_utils.so',
            'libsfplugin_ccodec_utils-v31.so',
        ),

    'vendor/lib64/libcodec2_vndk-v31.so': blob_fixup()
        .replace_needed(
            'libui.so',
            'libui-v30.so',
        )
        .replace_needed(
            'libstagefright_foundation.so',
            'libstagefright_foundation-v33.so',
        ),

    'vendor/lib64/libsfplugin_ccodec_utils-v31.so': blob_fixup()
        .replace_needed(
            'libcodec2_vndk.so',
            'libcodec2_vndk-v31.so',
        ),
        
    'vendor/lib64/libmtkcam_featurepolicy.so': blob_fixup()
        .binary_regex_replace(
            b'\xE8\x87\x40\xB9',
            b'\x28\x02\x80\x52',
        ),

    (
        'vendor/lib64/libteei_daemon_vfs.so',
        'vendor/lib64/lib3a.flash.so',
        'vendor/lib64/libaaa_ltm.so',
        'vendor/lib64/lib3a.ae.stat.so',
        'vendor/lib64/lib3a.sensors.color.so',
        'vendor/lib64/lib3a.sensors.flicker.so',
        'vendor/lib64/libSQLiteModule_VER_ALL.so',
    ): blob_fixup()
        .add_needed('liblog.so'),

    'vendor/lib64/libmnl.so' : blob_fixup()
        .add_needed('libcutils.so'),
         
    'vendor/lib64/libvidhance.so': blob_fixup()
        .add_needed('libcomparetf2_shim.so')
        .add_needed('libdemangle.so'),
        
    (
        'vendor/lib/libnvram.so',
        'vendor/lib/libsysenv.so',
        'vendor/lib64/libnvram.so',
        'vendor/lib64/libsysenv.so',
        'vendor/bin/hw/android.hardware.neuralnetworks@1.3-service-mtk-neuron',
        'vendor/lib/nfc_nci.nqx.default.hw.so',
        'vendor/lib64/nfc_nci.nqx.default.hw.so',
    ) : blob_fixup()
         .add_needed('libbase_shim.so'),

    (
        'vendor/bin/hw/android.hardware.gnss-service.mediatek',
        'vendor/lib64/hw/android.hardware.gnss-impl-mediatek.so',
    ): blob_fixup()
        .replace_needed(
            'android.hardware.gnss-V1-ndk_platform.so',
            'android.hardware.gnss-V1-ndk.so',
        ),
         
    'vendor/lib64/hw/hwcomposer.mt6853.so' : blob_fixup()
         .add_needed('libprocessgroup_shim.so')

}  # fmt: skip

module = ExtractUtilsModule(
    'cannon',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
