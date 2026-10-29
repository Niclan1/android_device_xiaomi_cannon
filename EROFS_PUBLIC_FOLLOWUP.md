# Optional EROFS kernel source and release procedure

This optional kernel adds read-only EROFS support to the unofficial LineageOS 24 / Android 17 port for the **global Redmi Note 9T, `cannong`, GL / M2007J22G**. The shared build target remains `cannon`. It does not add Google applications, root, modules, account data or proprietary payloads. The original vanilla release and its sources remain available separately.

## Exact source and attribution

The optional source branch is prepared locally as `lineage-24.0-cannong-erofs` in `Niclan1/android_kernel_xiaomi_cannon`. Publication must verify the remote object before advertising it as available. Its reviewed revision is `9b1c084c00cf9a82964387db268bfeceba803b96`, source tree `96c85a2278f961260b930d185f631ce67fd358c1`, based on published vanilla revision `83a6778ef82186e6a56431c9c914b9f566a964aa`. Exactly 30 paths change. The optional branch has the same complete source tree as the functionally tested development kernel; it retains the published upstream history and adds a maintainer-applied integration commit.

Thank you to [fangzny1](https://github.com/fangzny1/kernel_xiaomi_mt6853/tree/ea65d0f51005a76cf210a9005f746d55eeb25132/fs/erofs), the [LineageOS SM6150 maintainers](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/tree/e03e5ba22586be70673afb5d3c3f70510524e658), Huawei's EROFS authors, Michael Bestas, Guo Xuenan, Yann Collet, Sven Schmidt and the original Linux/LZ4 authors and reviewers. Their original notices remain in the files. The EROFS directory is identical in the two pinned donor trees, except normalization of surplus trailing blank lines in two headers. Matching trace/page-private interfaces and the maintained four-file LZ4 implementation are included.

Relevant primary changes are [page-private API adaptation](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/commit/e187e73390d276ec8b1c0f3cd1c1717cc57330cf), [decoder update](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/commit/ed70447ce073c911406e577acfa6e07170bb6fe0), [in-place decoding](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/commit/0f57679c845b9d0852afeb900743b2dde31418e8), [compressor update](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/commit/4e1a33b105ddf201f66dcc44490c6086a25eca0b) and [partial-decoder bounds fix](https://github.com/LineageOS/android_kernel_xiaomi_sm6150/commit/dae8edd8f82c4f24c8c8d8acc7fdc390d54c4181). Keep the GPL EROFS/kernel notices and the BSD LZ4 notices. Baseline contributors are listed in [CREDITS.md](CREDITS.md).

## Verified scope

ARM64 compilation retained LLVM CFI, shadow call stack, enforcing-capable SELinux, KFENCE, userfaultfd and the existing FCM options. Exactly these five configuration options were added:

```text
CONFIG_EROFS_FS=y
CONFIG_EROFS_FS_XATTR=y
CONFIG_EROFS_FS_POSIX_ACL=y
CONFIG_EROFS_FS_SECURITY=y
CONFIG_EROFS_FS_ZIP=y
```

An actual 4.14 ARM64 VM read the complete unchanged filesystem image twice, including a 217,107,692-byte compressed file and three other files, with all SHA256 values matching an independent host reference. The first driver-only attempt failed decompression; the included coherent LZ4 prerequisites resolved that failure. An additional exact-source ASan/UBSan test passed 8,915 checks covering fast/HC roundtrip, full/partial bounds, malformed/truncated data and partial-decoder fuzzing.

On the physical global Redmi Note 9T on 2026-10-29, the new kernel booted Android 17 and completed a read-only loop mount, two complete four-file read/hash passes and real `security.selinux` checks under enforcing Android policy: 25 checks, zero failures, followed by verified unmount/detach. This establishes that tested EROFS/LZ4 image feature set, not every EROFS feature or application. It does not prove Google application, Wallet or Play Integrity compatibility. The ordinary Android filesystems remain unchanged.

## Reproduce the source with standard tools

Use the published [release manifest and build guide](https://github.com/Niclan1/android_device_xiaomi_cannon/tree/release-manifest) and its three pinned post-sync patches. These helpers use Python3, Git, Make and the Android toolchains. They perform no phone operations.

From a stopped, clean checkout at the vanilla kernel revision:

```sh
python3 erofs/apply_source.py --kernel "$ANDROID_ROOT/kernel/xiaomi/cannon"
python3 erofs/apply_source.py --kernel "$ANDROID_ROOT/kernel/xiaomi/cannon" --apply
```

The first command validates only. The second applies the checked portable mail patch and produces the exact reviewed source commit. Repeating it on the same clean result is harmless; different or dirty trees are refused. `erofs/source.json` records the baseline/result tree, all30paths, source hashes and patch checksums. After the optional branch is published, fetching and checking out its exact commit is equivalent. Do not change source while a builder is consuming it.

## Kernel and Android builds

Use Linux on a case-sensitive filesystem. Install the Android build prerequisites and GNU cross tools `gcc-aarch64-linux-gnu` and `binutils-arm-linux-gnueabi`. The selected Android Clang is `clang-r596125`, 22.0.2, with LLD 22.0.2; the existing compatibility vDSO still uses GNU `ld.bfd`. The helper verifies the real required tools and configuration instead of spoofing their identity.

```sh
python3 erofs/build_kernel.py --android-root "$ANDROID_ROOT" --out "$HOME/out/cannong-erofs" --jobs 6
python3 erofs/build_kernel.py --android-root "$ANDROID_ROOT" --out "$HOME/out/cannong-erofs" --jobs 6 --execute
```

This uses a separate output and an exclusive output lock. Existing objects/configuration are reused with `olddefconfig`; no clean/clobber is performed. The result is `arch/arm64/boot/Image.gz` plus `erofs-build.json`. Git LOCALVERSION, timestamps, host metadata and the public integration commit ID can change binary hashes; byte-for-byte equality to the development binary is not claimed.

For a coherent full Android build, use the exact published manifest, extracted generic vendor inputs and documented portable blob fixups. Keep one writer in the Android tree:

```sh
cd "$ANDROID_ROOT"
source build/envsetup.sh
source vendor/lineage/vars/aosp_target_release
lunch "lineage_cannon-${aosp_target_release}-userdebug"
export SOONG_NINJA=ninja GOMEMLIMIT=24GiB GOGC=50 GOMAXPROCS=6
m -j6 kernel bootimage check-vintf-all
m -j6 target-files-package otatools bacon
```

Building an independent Image.gz does not automatically replace the kernel in the Android output. The Android kernel target above must consume the optional source before packaging. Validate generated configuration, VINTF, partition sizes and the final kernel inside the boot image. A successful build is not a substitute for installing/testing the exact newly generated ZIP.

## Coherent boot images, AVB and a full OTA

For a full source build, keep boot, system, vendor, product, system_ext, child vbmeta and top vbmeta from the **same final target-files set**. Use that set's `ota_from_target_files`/`bacon` result, not a system-only overlay on an unrelated LOS20 installation. The tested port needs the matching kernel, vendor HAL fixes, system_ext compatibility libraries, framework/bootclasspath and complete AVB descriptors. Retain the working DTBO unless an exact separately tested package intentionally replaces it. Recovery is optional and separate.

For a developer-only kernel replacement in an already verified vanilla image set, reproduce these host operations with the pinned AOSP tools:

1. Unpack its boot with `system/tools/mkbootimg/unpack_bootimg.py --format mkbootimg`. Reuse the returned arguments and replace only `--kernel` with the new Image.gz. Preserve ramdisk, actual board DTB, header version, offsets, command line and OS version fields. Confirm the unpacked ramdisk/DTB bytes are unchanged after repacking.
2. Read the original boot's `external/avb/avbtool.py info_image` output. Recreate its boot hash footer for partition `boot`, size 67,108,864 bytes, preserving original salt and property descriptors. The tested vanilla cohort uses boot-footer algorithm `NONE`.
3. Use that same pinned tool's `update_partition_descriptor --image OLD_VBMETA --partition_image NEW_BOOT --output NEW_VBMETA`, with the original signing algorithm/key, flags and rollback index. The current development cohort uses the **public AOSP test RSA4096 key**, flags 3 and rollback index 0. These are development/unlocked-bootloader settings, not production certification. Do not substitute unknown keys, change rollback/security state or sign only one side of the pair.
4. Parse both top images: every encoded descriptor other than the boot hash descriptor must remain byte-identical. Keep vbmeta_system/vbmeta_vendor unchanged for a boot-only update. Verify the complete new chain using `avbtool.py verify_image --image NEW_VBMETA --follow_chain_partitions`, with every referenced image present at its exact partition filename. Check boot fits 64 MiB and top vbmeta fits its 64 KiB image extent.
5. Distribute the new boot and matching top vbmeta together with their SHA256 sums and exact baseline requirement. Preserve the original pair for rollback. Do not mix this pair into an old ZIP merely by replacing two ZIP members: its OTA transfer data, target-files metadata and image hashes must also be regenerated from the final coherent image set.

For a full OTA, rebuild/repack the final target-files set through the published release packaging procedure, regenerate changed image/AVB descriptors first, then run the pinned `ota_from_target_files` and verify the ZIP CRC, metadata, transfer operations, extracted images and complete AVB chain. Install the **exact final ZIP** through the documented Recovery route and repeat first boot, display, radios, storage and EROFS read/hash/xattr tests before publishing it as tested. Preserve the original vanilla ZIP and checksums under its original name. A new optional EROFS OTA needs its own name, hashes and acceptance record; no binary is supplied by this source-only follow-up.

## Publish this optional source branch

After reviewing its 30-path source diff and notices, from the exact clean optional kernel commit:

```sh
python3 erofs/apply_source.py --kernel "$ANDROID_ROOT/kernel/xiaomi/cannon" --publish
git -C "$ANDROID_ROOT/kernel/xiaomi/cannon" ls-remote \
  https://github.com/Niclan1/android_kernel_xiaomi_cannon \
  refs/heads/lineage-24.0-cannong-erofs
```

The helper uses ordinary authenticated Git, pushes only the exact optional commit without force and verifies the remote revision. It does not create repositories, change the vanilla branch or upload ROM images. Publish this guide and the allowlisted `erofs/` source files separately on the release-manifest branch after review. Never publish the development workspace, personal module directories, signing credentials, backup catalogs or device dumps.
