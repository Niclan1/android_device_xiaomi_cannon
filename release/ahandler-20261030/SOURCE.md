# Matching source for the 2026-10-30 AHandler package

This is a supplement to the existing13-component [source manifest](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/default.xml),
[source build guide](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/SOURCE_BUILD.md)
and [credits](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/CREDITS.md).
The old manifest alone does not include this repair. Add frameworks/av as the14th
component using its original LineageOS history and exact commit below before
building. Do not substitute a different phone's frameworks repository.

## frameworks/av

- Upstream: https://github.com/LineageOS/android_frameworks_av
- Parent: `937eb9047ec2f88620f1f6a4d9e407f6c869d91a`
- Repaired commit: `3d2fa5702bbbbffc4c73ed2a222fbf0ccc6decb6`
- Exact tree: `491e0f48c8294d95813a75a9bc29be7ce14ca2b7`
- Changes: AHandler.cpp, ALooperRoster.cpp and AHandler.h; preserve the legacy
  binary layout while keeping the newer per-handler bookkeeping in a sidecar.
  This addresses a repeated legacy VT dispatcher CPU loop. It is a compatibility
  correction, not a claim that all camera/media paths have been tested.

Download the three files SOURCE.md, source.json and the bundle below from the
same release, into a separate download directory. The bundle contains the exact
one-commit change with upstream parent attribution and requires that parent:

```sh
sha256sum frameworks-av-AHandler-3d2fa57.bundle
# 280f85f6ca52de6fea2cf73742e2e31a926592b232845c814a0cecdd6f396a0e

# In a STOPPED, clean Android source workspace; save any local changes first.
git -C frameworks/av status --porcelain
# Continue only when the output is empty.
git -C frameworks/av fetch https://github.com/LineageOS/android_frameworks_av 937eb9047ec2f88620f1f6a4d9e407f6c869d91a
git -C frameworks/av bundle verify /absolute/download/path/frameworks-av-AHandler-3d2fa57.bundle
git -C frameworks/av fetch /absolute/download/path/frameworks-av-AHandler-3d2fa57.bundle HEAD
git -C frameworks/av checkout --detach 3d2fa5702bbbbffc4c73ed2a222fbf0ccc6decb6
git -C frameworks/av rev-parse HEAD^{tree}
# 491e0f48c8294d95813a75a9bc29be7ce14ca2b7
```

The text patch is also supplied for review. SHA256:
`c857b6869a9e7e6a9da3bfac28f9101126ab0d7e1189c9783ccf5a0822af4d0e`.
Applying it on the exact parent gives the same tree; use the bundle when the
original commit identity is required. Rebuild all affected system AND vendor
consumers of the foundation interface; swapping one library is insufficient.
Do not edit source inputs while a build is active or clobber valid caches.

## Embedded kernel and packaging

The clean package deliberately retains the validated EROFS kernel188 binary.
Its corresponding published source is
[9b1c084c00cf9a82964387db268bfeceba803b96](https://github.com/Niclan1/android_kernel_xiaomi_cannon/commit/9b1c084c00cf9a82964387db268bfeceba803b96),
tree `96c85a2278f961260b930d185f631ce67fd358c1`. Its kernel SHA256 is
`9189c13c598019399c328c4518a162b1365893200ae55ce1fa26ee022ae01547`.
The later main-build kernel4b9 is NOT the binary embedded in this package.
The device remains the global cannong; the shared upstream repository names
retain cannon for compatibility.

Use the existing build guide with this additional source pin. The public
source.json records all userspace build revisions and exact OS image hashes are
in VALIDATION.json. The fresh vendor filesystem was packaged at the retained
778838016-byte extent using upstream build_image with an explicit vendor_size;
the four fixed logical sizes are2418331648,778838016,1817784320,1769865216 bytes
(system,vendor,product,system_ext). Regenerate matching child/top AVB metadata.
Retain DTBO221f62fd and use clean boot0ec54efa; do not include a personal Magisk
boot. The package writes the four OS logical partitions and boot/vbmeta family;
it retains Recovery/DTBO and includes no userdata format or Google/root modules.

The existing hosted packaging workflow still uses its earlier immutable seed.
It DOES NOT automatically include this new repair. No CI seed, server migration,
runner architecture or automatic build dispatch was changed by this publication.
This is a local source-build-derived package with host signature, full data
reconstruction and AVB verification; byte-for-byte reproduction is not claimed.

## Attribution and limits

Thanks to AOSP and LineageOS for the foundation code and upstream tree; LinkBoi
and the cannon/cannong community for the existing device/vendor integration;
and Linux/MediaTek/backport authors linked in the existing credits and kernel
history. All original source licenses/notices and commit attribution remain.
This supplement does not replace those credits or claim their work as original.

The exact clean ZIP has not been physically installed. Its four userspace images
passed the maintainer's bounded regression checks using the personal kernel188
Magisk environment. Clean boot plus installer acceptance and the full hardware,
encryption, app and endurance checklist remain incomplete. Fingerprint was
already broken after unlocking; Google certification/Wallet is not claimed.
