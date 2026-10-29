# Building the cannong port

Draft for the next tested release. Ten scoped Niclan1 component integrations are published. Three remaining integrations use pinned public upstream bases plus the mandatory post-sync patches. Display candidate `182454Z` has passed its final bounded runtime check; the standard flashable OTA and matching image-packaging recipe still require exact-package validation before this is presented as a released build recipe.

This is an unofficial LineageOS 24 / Android 17 port for the global Redmi Note 9T, hardware variant `GL`, model `M2007J22G`. The shared source/build target remains `cannon`; runtime vendor identity is `cannong`. Other MT6853 devices and Chinese `cannon` hardware are not validated by this release.

## Source manifest

[default.xml](default.xml) was exported read-only from the checkout, then mapped to the actual prepared publication objects using `sources.json`. It pins all 1,245 projects. Twelve modified components retain their public upstream histories under maintainer-applied integration commits. Vendor is a source/rules-only root with no proprietary payload/history. The device extraction source includes the repaired PQ recipe and one explicit Apache-2.0 license comment on its new helper. Publication revisions differ from internal development commit IDs; source-tree correspondence is recorded explicitly.

Use this exact source manifest and its post-sync step rather than a moving `lineage-24.0` checkout. The source manifest is the `release-manifest` branch of `Niclan1/android_device_xiaomi_cannon`. Follow the README checkout and mandatory three-patch verification step before compiling.

## Host and toolchain

Use a 64-bit Linux build host and a native case-sensitive filesystem. WSL2 with the checkout and outputs on its ext4 filesystem was used for development. AOSP documents at least 400 GB free storage and 64 GB RAM for current Android development; see [the official requirements](https://source.android.com/docs/setup/start/requirements). Development here used bounded `-j8` builds with a 24 GiB Go memory limit; that observation does not replace the upstream requirements.

Install Repo and the documented Android build prerequisites. Use the pinned Android prebuilts and the kernel toolchain selected by the device tree; do not substitute a host Clang or spoof compiler/linker identity. Preserve compiler caches and intermediate outputs for incremental rebuilds. No kernel-version spoofing is required or claimed. The compiled kernel used internal revision `664796d21ab13e2ef266b5fd9e405609dabb1b7b`; its curated publication revision has the identical source tree. Git-derived LOCALVERSION, timestamps and build-host metadata can change binary hashes when rebuilding from the publication commit, so byte-for-byte kernel reproducibility is not claimed.

The current phone kernel was built with Android Clang `22.0.2`, build `r596125` / `15071444`, and LLD `22.0.2`. Its 32-bit compatibility vDSO uses the existing GNU `ld.bfd` path. Compiler/assembler/linker configuration must describe these real tools, including that separate compatibility path.

## Proprietary inputs

Use `device/xiaomi/cannon/proprietary-files.txt` and the corresponding extraction configuration. The published recipe must identify its firmware input and preserve file-specific redistribution notices. Do not extract or distribute device calibration, NVRAM, identity, security-key or personal data.

The release's extraction recipe must reproduce the seven dependent `libmtkutils` symbol-namespace changes, the two telephony JAR owner changes and the PQ TinyXML dependency selection. Current committed vendor artifacts contain these changes; the existing extraction script does not yet encode all three; portable, byte-exact symbol and JAR fixups are now staged in `fixups/`, while the final PQ dependency/PHDR fixup is also staged and reproduces both repaired deployment artifacts exactly. The three focused portable transformations reproduce the audited generic source artifacts exactly. A complete fresh firmware extraction/full rebuild has not yet been repeated. Publish the pinned renamer with its Apache-2.0 notice and portable, verified JAR/PQ fixups before claiming a reproducible fresh build.

## Compile

Once the release sources and extraction recipes are published and synchronized, the validated environment setup is:

```sh
source build/envsetup.sh
source vendor/lineage/vars/aosp_target_release
lunch "lineage_cannon-${aosp_target_release}-userdebug"
export SOONG_NINJA=ninja
export GOMEMLIMIT=24GiB GOGC=50 GOMAXPROCS=8
m -j8 check-vintf-all
m -j8 target-files-package bacon
```

Focused development targets include `kernel bootimage`, `recoveryimage`, `vendorimage`, `systemimage`, `systemextimage`, `selinux_policy`, `check-vintf-all`, `framework-minus-apex` and `services`. Use only the affected targets after a justified source change. A normal frontend invocation must regenerate the graph when build configuration changes; do not invoke a stale Ninja graph against new configuration. Keep one writer per tree. Do not clean or clobber healthy outputs.

The commands above produce build artifacts. The physical candidate also uses a verified boot ramdisk/kernel cohort and regenerated child/top AVB descriptors. Its portable packaging recipe and matching final target-files cohort are still release prerequisites; a new `bacon` output must not be assumed byte-identical to the physically tested candidate.

## Verify and distribute

Before release, verify image sizes against the actual partition layout; VINTF; final kernel configuration and capabilities; boot/kernel/ramdisk correspondence; dynamic-partition metadata; extracted image contents; and the complete AVB descriptor chain. Publish a SHA-256 list for the exact ROM ZIP and optional Recovery artifact, plus the final source manifest and license notices.

Validate installation of the exact release ZIP through the documented Recovery route and repeat first boot, display, radio/network, storage and recovery checks. Successful compilation alone is not hardware acceptance. Unfinished tests remain explicitly unverified. Public test keys, userdebug builds and modified AVB policy must be disclosed. Play Integrity, Play Protect certification and Google Wallet are not guaranteed.
