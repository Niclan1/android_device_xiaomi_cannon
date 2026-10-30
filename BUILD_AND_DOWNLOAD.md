# Redmi Note9T cannong — Android17 downloads and GitHub packaging

Unofficial, experimental LineageOS24 for the global Redmi Note9T
`cannong`/M2007J22G. This package contains no Google apps, root, personal modules
or account data. Other variants are not covered by this device's evidence.

## Download

- **[Full unrooted EROFS ROM ZIP](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/download/lineage24-cannong-ahandler-20261030/lineage-24.0-20261030T095022Z-UNOFFICIAL-cannong-EROFS-AHandler-UNTESTED.zip)**
  —1261040651bytes. SHA256:
  `8ee87a25843814d347ca0f6233d247d10c2549f0c79684b4533914f5086b4101`.
  [Release, checksum and validation report](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/tag/lineage24-cannong-ahandler-20261030).
- **[Raw Android17 Recovery image](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/download/recovery-android17-cannong-20261029/recovery.img)**
  —134217728bytes. SHA256:
  `321edf16505aefdde71ef90382fa611b814aab68836bc041e13f3edcce5ce952`.
  [Recovery release and source/limitations](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/tag/recovery-android17-cannong-20261029).

Choose these named binary assets. GitHub's automatic Source code ZIP/tar.gz is
not a flashable Android ROM. Check the complete SHA256 after downloading:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\recovery.img'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\lineage-24.0-20261030T095022Z-UNOFFICIAL-cannong-EROFS-AHandler-UNTESTED.zip'
```

This2026-10-30 package contains the all-consumer AHandler repair. The same
four userspace images passed bounded owner checks (call, web, camera/video,
brightness/wake and WhatsApp) on the personal rooted kernel188 installation;
the VT service's repeated idle CPU loop dropped from about100% to0% in the
observed windows, including after a functional call. This is not full acceptance.
The **exact clean ZIP has not been physically installed**. Whole-file signature,
four filesystem reconstructions, raw-image hashes and full AVB chain passed
host validation. [Validation report](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/download/lineage24-cannong-ahandler-20261030/VALIDATION.json).

The retained unrooted EROFS kernel has matching published source; the package
contains no Magisk, GApps, personal modules or data. Recovery below is unchanged
and separately flashed; installing the ROM ZIP does not install Recovery.

## Install scope

Use an already-unlocked global cannong, working USB data cable, current
platform-tools, compatible Lineage Recovery and matching base firmware/DTBO.
Keep verified personal backups/account recovery and the original Recovery.
Do not relock the bootloader with this unofficial build.

For Recovery, use the
[tested raw-image flash guide](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/download/recovery-android17-cannong-20261029/FLASH-RECOVERY.md).
The same-image fastboot flash, complete readback and normal Android17 return
passed on the maintainer's cannong. No conversion is needed; `fastboot boot`
RAM launch remains untested. The
[public validation](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/download/recovery-android17-cannong-20261029/FASTBOOT-VALIDATION.json)
supersedes the original release files' historical PENDING transport statement.

For the ROM, enter compatible Lineage Recovery, select **Apply update → Apply
from ADB**, and run:

```sh
adb sideload lineage-24.0-20261030T095022Z-UNOFFICIAL-cannong-EROFS-AHandler-UNTESTED.zip
```

Wait for actual Recovery installation success. The complete matched OTA writes
the OS image/AVB family and retains Recovery/DTBO; it includes no userdata-format
operation. Do not combine LinkBoi's LOS20 with only this system image or mix
other boot/vendor/vbmeta candidates. The retained DTBO must match
`221f62fdb07d6ab69acc9cafdc71b289347d489b872aa2bc4e0624dfbe63cd6a`.

Updating an existing compatible Android17 installation keeps userdata. A first
installation across Android versions needs a separately verified starting-state,
backup and clean-install plan; arbitrary MIUI/LOS20 routes are not claimed tested.
Do not wipe to bypass an image/DTBO assertion, format backup media or write
modem/NVRAM, calibration, identity/security or other protected partitions.

Fingerprint was pre-existing broken after unlocking on the test device. Full
hardware/app/endurance, encrypted-data decryption, Play certification/Integrity
and Wallet acceptance remain incomplete. Compilation or quiet logs are not
functional proof. Recovery is not presented as hardened against root/raw writes.

## Existing hosted packaging workflow (older seed)

**The existing workflow still packages its earlier seed and does not include this
AHandler repair.** This new release was built locally from the fresh userspace
cohort. No runner/server migration or workflow dispatch was changed.

For the older package, the maintainer can open
[Actions → Package unrooted EROFS ROM](https://github.com/Niclan1/android_device_xiaomi_cannon/actions/workflows/package-erofs-hosted.yml)
and choose **Run workflow**, branch`lineage-22.2`. The workflow is manual and
restricted to ownerNiclan1. It verifies the public seed hashes, signs/revalidates
the package, checks every uploaded asset's server digest and publishes a
physically untested prerelease. Standard public Ubuntu runners are used, with
no larger paid runner or Actions artifact/cache uploads.

See the [packager documentation](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/lineage-22.2/release/gh-ci/README.md).
Fresh source-built images and any future full ROM build require their own
artifact and hardware validation before replacing a tested cohort.

## Sources and thanks

**Required14th component for this release:** [matching frameworks/av source,
exact bundle/patch and build supplement](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/lineage-22.2/release/ahandler-20261030/SOURCE.md).
The previous13-tree manifest alone does not contain the AHandler fix.


[Pinned source manifest](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/default.xml) ·
[Source/build guide](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/SOURCE_BUILD.md) ·
[Credits and upstream links](https://github.com/Niclan1/android_device_xiaomi_cannon/blob/release-manifest/CREDITS.md) ·
[EROFS kernel source](https://github.com/Niclan1/android_kernel_xiaomi_cannon/tree/lineage-24.0-cannong-erofs) ·
[Recovery kernel source](https://github.com/Niclan1/android_kernel_xiaomi_cannon/tree/lineage-24.0-cannong-recovery).

Thanks to LineageOS/AOSP, LinkBoi and the cannon/cannong device community, and
the kernel/MediaTek/upstream authors linked in the credits. Original authorship,
licenses and notices are retained.
