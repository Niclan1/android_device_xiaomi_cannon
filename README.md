# Unofficial LineageOS 24 for Redmi Note 9T

Android 17 source manifest for the global `cannong` / M2007J22G / HWC `GL` variant. The shared build target remains `cannon`. Other variants are not validated.

## Source checkout

```sh
repo init -u https://github.com/Niclan1/android_device_xiaomi_cannon.git -b release-manifest
repo sync -c -j4
python3 .repo/manifests/apply_port_patches.py --root .
```

Ten component integrations are published on their pinned source branches. Three small integrations use real public upstream bases plus explicit post-sync patches; the helper checks every patch hash, exact base and result trees, refuses dirty/unexpected state, and leaves clean commits. No missing repository URL is presented as fetchable. Re-run the helper after a fresh sync before building.

[Build instructions](SOURCE_BUILD.md) ? [Source correspondence](sources.json) ? [Credits](CREDITS.md) ? [License inventory](license-inventory.json) ? [Installation status](INSTALLATION.md)

## Hardware evidence and release status

Physical candidate `182454Z` boots Android 17 with SELinux enforcing. The owner confirmed Wi-Fi/cellular internet, outgoing call audio, an outdoor GPS fix, responsive brightness and Power wake/unlock. A bounded final capture showed the PQ service stable without the earlier linker rejection; this is not an endurance test. A known fingerprint-service fatal and unfinished hardware/application checks remain. No Google certification, Play Integrity or Wallet claim is made.

The next standard OTA ZIP and logging-off boot profile are being validated separately. This source publication is not a claim that an untested development ZIP is a release artifact. Vendor publication includes generated rules and portable extraction/fixup recipes, without proprietary payloads or their parent history. [CREDITS.md](CREDITS.md) links the original implementations and authors.
