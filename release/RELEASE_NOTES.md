# LineageOS 24 / Android 17 for Redmi Note 9T

Unofficial experimental release for global `cannong` / M2007J22G. This is a
vanilla ROM: **no GApps, Magisk, Zygisk, personal modules, or accounts**.

Download the ROM, DTBO, recovery, and `SHA256SUMS` from this same release.
Follow `INSTALLATION.md`; older DTBO or recovery builds are not interchangeable.

## Included changes

- Integrated Linux 6.18.33 device kernel.
- Corrected MT6360 Type-C interrupt initialization and USB role handling.
  Real USB headset audio was accepted on the device.
- Corrected Bluetooth Sniff Subrating response handling in both command paths.
  A controller's legitimate unsupported-feature response is handled as an
  error, not converted to success or allowed to abort Bluetooth. Real earbud
  playback, silence and resume were exercised and accepted.
- Compiled AAudio SELinux policy for legacy PCM mapping; low-latency input and
  output operate without runtime policy injection.
- FUSE passthrough integration for media-file handling.
- Owned OTA/platform/AVB identities and privately signed runtime APEXes.
  The upstream, explicitly `PRESIGNED` CTS compatibility-test APEX is retained
  unchanged, following Android's signing policy for that test fixture.
- Matched, signed OrangeFox recovery and the exact required DTBO are supplied
  as separate installation assets.

## Important limitations

- Shared AAudio MMAP input and output achieve low latency. The hardware does
  not provide shareable exclusive buffers: an exclusive-mode request can fall
  back to a shared stream, and the first cold request can use ordinary latency.
  Exclusive hardware-buffer support is not claimed.
- OrangeFox ADB sideload works; encrypted internal-storage access does not.
  Its storage warning must not be "fixed" by formatting userdata or metadata.
  Recovery backup/restore is not qualified.
- TCPM can negotiate a higher current while the charger remains limited to
  500 mA. Charging-current integration is still pending; fast charging is not
  claimed fixed.
- The proprietary Thermal HAL does not expose the real kernel thermal zones.
  A replacement HAL remains pending. No temperatures or thermal capabilities
  are fabricated.
- This is a userdebug port for an unlocked bootloader, not an official,
  certified LineageOS device release. Banking, Wallet and Play certification
  compatibility are not guaranteed. The unlocked bootloader remains in the
  orange verified-boot state; OS hashtree verification remains enforcing.
- Testing is scoped to the enrolled global handset and available accessories.
  Arbitrary firmware migrations, every hardware variant, clean installs from
  every earlier Android version and long-term endurance are not established.

## Release qualification

The supplied DTBO and recovery were flashed in the documented bootloader
fastboot order, then this exact privately signed ZIP was installed through
OrangeFox with signature verification. Android booted with SELinux and OS
hashtree verification enforcing. All ten running OS/DTBO/recovery partition
contents matched the packaged images. All 40 privately signed runtime APEXes
and the unchanged CTS fixture were active and byte-verified.

Vanilla runtime testing retained existing userdata, with old Google/root
packages absent or disabled and no active Magisk or Google services. This was
not a factory-reset test. USB headset and Bluetooth playback/silence/resume
were accepted on the unchanged functional payload before the final
signing-only build; the final build's controller, Bluetooth library and four
real shared low-latency input/output streams were checked again.

See `ACCEPTANCE.json` for artifact hashes, verification scope and observations,
and `SOURCE_INDEX.json` for matching source repositories. The device source
contains the pinned manifest, verified platform/recovery patches, build
configuration and upstream credits. Personal Google/root/application-hook
setup is not part of this public ROM.
