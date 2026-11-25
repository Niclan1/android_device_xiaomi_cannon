# Corresponding source and rebuilding

The source tag for this release is `lineage-24.0-cannong-20261125`.
`SOURCE_INDEX.json` identifies the device, kernel, compatibility and vendor
snapshots. Existing upstream copyright notices and project licenses apply.

The kernel and compatibility/vendor snapshot trees preserve the tested source
trees. The device snapshot also contains release documentation and source
overlays. Original compiled revisions and source tree identities are recorded
separately: a new snapshot commit is not the original compiled revision.
Rebuilding therefore has a new Git-derived build identity; do not falsify it.
Private signing keys are deliberately not distributed.

## ROM source

Use a Linux Android build host with the dependencies and disk/RAM capacity
required by LineageOS 24. Install Google's `repo` tool and Git LFS. In a new,
empty Android source directory:

```bash
repo init -u https://github.com/Niclan1/android_device_xiaomi_cannon \
  -b lineage-24.0-cannong-20261125 -m release/source/manifest.xml
repo sync -c -j4
python3 device/xiaomi/cannon/release/source/apply-overlays.py .
source build/envsetup.sh
breakfast cannon
m -j4 target-files-package
```

The manifest pins materialized projects, not moving branch heads. Unused
projects absent from the qualified workspace are listed explicitly.
`overlays.json` identifies each public base, patch checksum and reconstructed
Git tree. The applicator refuses a different base, dirty checkout or mismatched
result. Host build-tool changes captured in the release workspace are marked
separately; the export does not claim bit-for-bit host-tool reproducibility.

Proprietary vendor files retain their original ownership and distribution
terms. Git LFS files must be downloaded, not left as pointer text. Vendor
extraction/build rules are included in the device and vendor repositories.

## Kernel

The complete Linux 6.18.33 source is in the matching kernel repository/tag,
including the Cannong defconfig, board DTS and driver changes.
`release/source/kernel.config` is the actual qualified configuration.
The tested compiler is Android Clang `clang-r596125`; the pinned Android
manifest supplies the compiler and kernel build tools.

`release/source/build-kernel.sh` is the path-independent kernel invocation.
Run it from the synced Android source root with a separate, empty output
directory. It does not clean or overwrite another build directory.
First build the Android host device-tree compiler with `m dtc`, then run
`bash device/xiaomi/cannon/release/source/build-kernel.sh "$PWD/kernel-out"`.
The ROM kernel's original compiled revision is
`cfff553735e10828868119d411182e36e3f79695`.

## OrangeFox

Recovery uses its own pinned Android 16 / OrangeFox source graph in
`release/source/recovery/manifest.xml`, not the ROM's recovery project.
The recovery source overlays, device configuration and reconstructed tree
identities are supplied alongside it. The original recovery kernel revision
is `4473da653d287a7cb0ee180cb0c132b1dc1982bf`.
`recovery/kernel-from-rom.patch` restores that exact kernel source tree from
the published ROM kernel tree; the recorded configuration is shared.

The recovery toolchain overrides are also pinned in its manifest: Clang,
Rust and SDK prebuilts were supplied from the qualified ROM tool cohort.
Use `clang-r547379` for recovery userspace, not the ROM kernel compiler.
Apply the recorded recovery project patches to their exact bases, and copy
`recovery/device/` to `device/xiaomi/cannon` in that separate checkout.
Build the recovery kernel from its restored source with the supplied kernel
configuration. Supply the resulting `Image.gz` and board DTB at the
`prebuilt/` paths in `BoardConfig.mk`. The original embedded recovery DTBO
and board DTB are supplied in `recovery/boot-inputs/`; these are recovery
packaging inputs, **not replacements for the standalone installation DTBO**.

Provide your own recovery AVB key and OTA certificate/key at the paths named
in the device makefiles. Then:

```bash
export FOX_BUILD_DEVICE=cannon
source build/envsetup.sh
source device/xiaomi/cannon/vendorsetup.sh cannon
lunch twrp_cannon bp2a eng
m -j4 recoveryimage
```

The source includes the real DRM framebuffer, memfd ashmem and GUI/control
fixes. A clean build must compile the updated libcutils into both shared and
flattened static consumers, including libsnapshot and libsnapshot_nobinder.
The shipped incremental rebuild relinked these consumers explicitly.
Encrypted userdata support is disabled in this qualified configuration.

## Signing and installation packages

Generate and protect your own release keys. Use the platform release-signing
tools to sign APK/APEX containers, all 40 runtime APEX payloads, the AVB chain
and OTA package. Preserve the explicitly `PRESIGNED` CTS test fixture.
Public certificate fingerprints are in `ACCEPTANCE.json`.

An ordinary unsigned `target-files-package` or `bacon` output is not the
qualified release ZIP. Its custom A-only installation program and script are
published in `release/installer/`, and inside the signed release ZIP.
The package installs eight complete OS images, resizes the four logical OS
partitions, and checks the **full exact DTBO and recovery hashes before any
OS write**. Repackaged images need new AVB metadata, coherent logical sizes,
new installer image hashes, new OTA signatures and corresponding matched
installation assets. Never reuse this release's integrity assertions for
different images, sign with public test keys for a production release, or
bypass the checks to make another package install.

Source reconstruction and the documented installation route were verified
for this release. A new complete clean-room build and byte-identical rebuild
of the private-key-signed binaries are not claimed.

## Credits

LineageOS and Android Open Source Project; Linux and Android common-kernel
contributors; OrangeFox and TeamWin; xiaomi-mt6853-devs and the original Cannon
device/kernel maintainers; MediaTek and the respective vendor-file owners.
Per-file licenses and original contributor credits remain in the sources.
