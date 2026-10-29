# Redmi Note 9T Android 17 installation

Draft only: no release ZIP or installation cohort has been frozen yet. The display repair has passed functional and bounded runtime tests; final OTA packaging and an installation test of the exact ZIP are pending. Do not use the previously compiled development ZIP with images from a newer candidate.

## Supported hardware and prerequisites

The tested device is the global Redmi Note 9T, `cannong`, model `M2007J22G`, boot hardware country `GL`, MediaTek MT6853. A `cannon` build target or fastboot product alias alone does not prove the correct variant. Chinese Redmi Note 9 5G and related MT6853 devices are not covered by the current hardware evidence.

Use an already-unlocked bootloader, working USB data cable, current platform tools and the exact supported Lineage Recovery. Keep the bootloader unlocked; do not relock it with this unofficial build. Keep a verified copy of your backups and original recovery material away from partitions being installed. Confirm access to your Google/WhatsApp recovery account, phone number and encrypted-backup credentials, Garmin account/synchronized activities and banking re-registration route before a clean install.

A first major-version installation may require formatting userdata and loses local files and applications. The final guide must identify that step precisely. It must never format the backup microSD or flash modem, calibration, NVRAM, identity, security-key, preloader or other protected non-OS partitions.

## Release cohort

The release must install its matched boot/kernel, system, vendor, system_ext, product and required child/top vbmeta images. Recovery is an optional separate artifact when the installed Recovery is explicitly validated for that exact package.

Installing LinkBoi's LineageOS 20 and copying only the new system image does not reproduce the tested Android 17 environment. The current kernel provides required BPF/LPM and memory-management behavior. The vendor contains the tested symbol, USB, Wi-Fi and telephony repairs; system_ext contains matching policy and framework integration. Product and AVB descriptors must also agree. Retained product data in the current candidate comes from the Android 17 image family, not from LineageOS 20.

## Intended supported route

The established device route uses Lineage Recovery and **Apply update → Apply from ADB**, followed by `adb sideload` of a complete matched OTA. LinkBoi's [device-specific installation documentation](https://www.linkdevel.com/cannon/installation/) describes that route for the earlier ROM and warns about third-party Recovery handling of userdata and dynamic partitions. Its old package names and formatting steps are not an Android 17 installation test.

The final guide will supply the exact artifact filenames, SHA-256 checks, supported Recovery installation commands, variant checks, clean-install formatting step, sideload command, expected results and recovery procedure after the final ZIP is validated. Direct raw OS flashing used during development is not proof that an OTA updater works.

Google apps are not yet part of a validated release set. Use only a package explicitly verified for the final Android version and architecture. Certification, Play Integrity and Wallet payment success are separate tests; this release makes no guarantee about them.

## Current hardware evidence

The owner has confirmed Android boot/setup, usable Wi-Fi internet, cellular internet after selecting an existing proxy-free carrier APN, outgoing call audio through earpiece/speakerphone and a GPS fix outdoors. The Android 17 Recovery UI reports the expected battery level. These observations do not certify all checklist items. On repaired candidate `native-init-20261029T182454Z`, the owner confirmed immediate brightness changes and responsive Power wake/unlock. The final 180-second capture retained the same PQ process throughout 162.21 seconds of sampled observations, with no PQ exits, program-header errors, Java fatal exceptions, ANRs or kernel-fatal signatures. This is a bounded stability result, not an extended endurance test. The reported boot-speed improvement is an owner estimate, not a timed benchmark. Camera, Bluetooth, suspend, encryption, application compatibility and the remaining acceptance cases need their own functional evidence.

Report problems with the exact release hash and a bounded, redacted log. Remove phone numbers, account identifiers, SIM/subscriber identifiers, network addresses, location coordinates and private file paths before sharing diagnostics.
