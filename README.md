# LineageOS 24 for Redmi Note 9T

Unofficial Android 17 / Linux 6.18.33 port for the global **cannong,
M2007J22G**. The public ROM is vanilla: no GApps or Magisk.

**[Download the matched ROM, OrangeFox and DTBO](https://github.com/Niclan1/android_device_xiaomi_cannon/releases/tag/lineage-24.0-cannong-20261125)**

Read **[INSTALLATION.md](release/INSTALLATION.md)** before flashing.
**Use all three files from the same release, including its DTBO even if your
old DTBO was built by this maintainer.** Do not bypass compatibility assertions.
The tested route preserves userdata on this port's working Android 17 cohort;
arbitrary MIUI migrations and all-device-variant compatibility are not claimed.

OrangeFox supports ADB sideload but not encrypted internal-storage access.
Do not format userdata to hide its storage warning. Charging-current and
Thermal HAL integration remain limited. Read the full
[release notes](release/RELEASE_NOTES.md) and
[qualification record](release/ACCEPTANCE.json).

## Source

The matching source tag is `lineage-24.0-cannong-20261125`.
[BUILDING.md](release/BUILDING.md) explains the pinned manifest, exact
kernel source, platform patches, recovery source and signing requirements.
[SOURCE_INDEX.json](release/SOURCE_INDEX.json) records the source identities.
This branch's compiled device source is preserved, with release documentation
and source-reconstruction material added.

Credits: LineageOS, AOSP, Linux/Android common, OrangeFox, TeamWin,
xiaomi-mt6853-devs, original Cannon maintainers and vendor-file owners.
Per-file licenses and contributor credits remain in their respective sources.
The original device description is preserved in
[DEVICE_SPECIFICATIONS.md](release/DEVICE_SPECIFICATIONS.md).

Copyright (C) 2023 LineageOS

Copyright (C) 2022 StatiX
