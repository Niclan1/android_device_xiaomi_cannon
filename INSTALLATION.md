# Install experimental LineageOS24 / Android17 on cannong

For the global Redmi Note9T `cannong`, modelM2007J22G, with an already-unlocked
bootloader. Other variants and arbitrary MIUI/firmware starting states have not
been validated. This is an unofficial experimental ROM; keep a recovery path.

## Before starting

- Back up personal files and confirm access to important accounts, phone numbers
  and encrypted-backup passwords privately. A clean installation can erase local
  userdata. Keep backups off any storage you might format.
- Have working ADB/platform-tools, a USB data cable and a **compatible Lineage
  Recovery**. The exact ZIP was installed using retained Android17 Recovery SHA256
  `321edf16505aefdde71ef90382fa611b814aab68836bc041e13f3edcce5ce952`.
  Its image is not bundled here. An older LOS20/TWRP/OrangeFox Recovery is not
  claimed tested; TWRP/OrangeFox are explicitly refused by this updater.
- Use matching base firmware/DTBO. The updater requires the retained32MiB DTBO
  SHA256`221f62fdb07d6ab69acc9cafdc71b289347d489b872aa2bc4e0624dfbe63cd6a`.
  It checks DTBO and does not overwrite it. If that guard fails, stop and obtain
  a device-specific verified baseline; do not bypass the assertion or flash
  random firmware/calibration images.
- Do not relock the bootloader or erase modem/NVRAM, calibration, identity,
  security-key, preloader or other protected partitions.

## Download and verify

Download the exact ZIP from the maintainer's shared download link. A GitHub
binary release has not been published by this workflow; do not substitute an
unverified mirror or assume the source repositories contain the flashable ZIP.

File: `lineage-24.0-20261029-UNOFFICIAL-cannong.zip` (1259870437bytes).

SHA256: `fb6022836171f691b8842a58301209c75e195f177bd535741135dd17a685f8dd`

In PowerShell in the download directory:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\lineage-24.0-20261029-UNOFFICIAL-cannong.zip'
```

Compare the entire hash. Do not install a different file with the same name.

## Flash the complete OTA

1. Enter your compatible Lineage Recovery. Leave the backup microSD alone.
2. Choose **Apply update → Apply from ADB**.
3. On the PC, in the ZIP directory, run:

```sh
adb sideload lineage-24.0-20261029-UNOFFICIAL-cannong.zip
```

4. Wait for Recovery's actual success result. A host transfer percentage by
   itself does not prove installation succeeded. If an assertion or image
   verification fails, stay in Recovery and preserve the exact error.
5. Updating this tested Android17 installation preserves userdata: no format is
   included in the ZIP. For a first installation from another Android version,
   a userdata format may be required **only after backups/account recovery and
   the compatible starting state are confirmed**, before booting the new ROM.
   This deletes local files/apps. Never format the backup microSD or use a wipe
   as a workaround for a firmware/DTBO/Recovery assertion.
6. Reboot to system after successful installation and any genuinely required
   clean-install userdata operation. First boot can take longer than a normal
   reboot; persistent loops require logs and diagnosis, not repeated wipes.

The exact tested route was an Android17 update retaining its existing userdata.
A universal clean installation/migration from every LOS20 or MIUI state is not
claimed. If the prerequisites above cannot be verified, ask for a starting-state
procedure before changing partitions.

## What the ZIP changes

The matched cohort installs `system`, `vendor`, `product`, `system_ext`, `boot`,
`vbmeta_system`, `vbmeta_vendor` and `vbmeta`, with asserted full image readbacks.
Dynamic OS partition metadata is updated for the four fixed logical image sizes.
It does **not** install Recovery or DTBO, format userdata or write protected
modem/calibration/security partitions. Do not combine LinkBoi's LOS20 with only
our system image or mix AVB/boot/vendor images from other candidates.

This vanilla build includes no Google apps, root, personal modules or accounts.
Boot, responsive brightness/wake, browsing and saved media passed the exact-ZIP
regression; the full hardware/app/endurance checklist is incomplete. Fingerprint
was pre-existing broken after unlocking on the test device. Certification,
Integrity, Wallet and banking compatibility are not guaranteed.

[Sources/build](SOURCE_BUILD.md) · [Pinned manifest](default.xml) ·
[Credits and upstream contributors](CREDITS.md) ·
[Optional EROFS source follow-up](EROFS_PUBLIC_FOLLOWUP.md)
