# Install LineageOS 24 / Android 17 on Redmi Note 9T

This release is for the global **Redmi Note 9T, cannong, M2007J22G** with an
already-unlocked bootloader. Other similarly named Redmi phones and arbitrary
firmware starting states are not supported by this procedure.

## Download the complete matched set

Download these files from **the same GitHub release**, not an older release,
build directory, recovery thread, or mirror:

| File | Purpose |
| --- | --- |
| `lineage-24.0-20261125-UNOFFICIAL-cannon.zip` | Complete vanilla ROM |
| `dtbo-cannong-20261125.img` | Exact DTBO required by this ROM |
| `OrangeFox-cannong-20261125.img` | Exact signed recovery required by this ROM |
| `SHA256SUMS` | Checksums for this set |

**Flash the supplied DTBO even if your existing DTBO was also built by this
maintainer.** A matching filename, build date, or maintainer is not proof of
compatibility. The ROM checks the actual full DTBO and recovery contents before
changing OS partitions.

The DTBO must be 33,554,432 bytes, SHA-256:

```text
221f62fdb07d6ab69acc9cafdc71b289347d489b872aa2bc4e0624dfbe63cd6a
```

The recovery must be 134,217,728 bytes, SHA-256:

```text
fa87ed6043c5388f9418163aadbb0338aaa18c8182ce70751c3b029abdee1472
```

Do not substitute a DTB for the DTBO image. Do not edit the ZIP, remove its
assertions, or disable signature/AVB checks to get past a mismatch.

## Prerequisites and supported starting state

- Back up personal files and confirm account and encrypted-backup recovery
  access privately. Keep backups off the phone and backup microSD untouched.
- Use current official Android Platform-Tools, working USB drivers, and a
  reliable data cable. This guide's commands are for **Windows PowerShell**.
- The tested route is an update of this port's working Android 17 installation,
  retaining userdata. A clean migration from arbitrary MIUI/other Android
  versions has not been validated. Do not treat this as a universal migration
  or downgrade guide; establish a compatible starting state first.
- Keep a known-good, device-specific OS rollback available. Do not relock the
  bootloader, change firmware/preloader, or erase modem, NVRAM, calibration,
  identity, security-key, or backup partitions.

**Recovery limitation:** this OrangeFox build supports the tested ADB sideload
route, but does not decrypt the installed ROM's internal userdata. An
"unable to locate storage" message is not a request to format storage.
Use ADB sideload. Do not format userdata or metadata to hide that warning.
Encrypted internal-storage browsing and recovery backup/restore are not claimed
working.

## 1. Verify the downloads

Extract the official Platform-Tools ZIP. Put the three release files and
`SHA256SUMS` beside `adb.exe` and `fastboot.exe` in its `platform-tools` folder.
Open PowerShell in that folder.

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\lineage-24.0-20261125-UNOFFICIAL-cannon.zip'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\dtbo-cannong-20261125.img'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\OrangeFox-cannong-20261125.img'
Get-Content -LiteralPath '.\SHA256SUMS'
```

Compare all 64 hexadecimal characters for each file against `SHA256SUMS`.
Stop if any hash or size differs. Renaming a different image does not make it
compatible.

## 2. Enter bootloader fastboot

From working Android, enable USB debugging, authorize your PC, and run:

```powershell
.\adb.exe devices
$AndroidSerial = Read-Host 'Enter the serial shown for your intended phone'
if ([string]::IsNullOrWhiteSpace($AndroidSerial)) { throw 'No device selected' }
.\adb.exe -s $AndroidSerial reboot bootloader
if ($LASTEXITCODE -ne 0) { throw 'Could not enter the bootloader' }
```

Alternatively, power the phone off and use its bootloader key combination
(Volume Down + Power). This step needs **bootloader fastboot**, not fastbootd.

```powershell
.\fastboot.exe devices
$FastbootSerial = Read-Host 'Enter the bootloader serial for your intended phone'
if ([string]::IsNullOrWhiteSpace($FastbootSerial)) { throw 'No device selected' }
$Product = .\fastboot.exe -s $FastbootSerial getvar product 2>&1 | Out-String
$Product
if ($LASTEXITCODE -ne 0 -or $Product -notmatch 'product:\s*(cannon|cannong)\b') {
    throw 'Unexpected bootloader product; stop'
}
```

Check the physical phone model too. A product-family string does not validate
a different handset variant.

## 3. Flash this release's DTBO and recovery

Run these commands **in order**, using only the verified files above:

```powershell
.\fastboot.exe -s $FastbootSerial flash dtbo '.\dtbo-cannong-20261125.img'
if ($LASTEXITCODE -ne 0) { throw 'DTBO flash failed; do not continue' }

.\fastboot.exe -s $FastbootSerial flash recovery '.\OrangeFox-cannong-20261125.img'
if ($LASTEXITCODE -ne 0) { throw 'Recovery flash failed; do not continue' }

.\fastboot.exe -s $FastbootSerial reboot recovery
if ($LASTEXITCODE -ne 0) { throw 'Could not enter recovery; do not boot the OS' }
```

Do not boot the previous OS between flashing this matched set and installing
the new ROM. Do not use `fastboot boot`, flash only `system`, or add
`--disable-verity` / `--disable-verification` flags.

## 4. Sideload the complete ROM

1. In OrangeFox, enable ZIP signature verification. Open **ADB & Sideload**
   and activate sideload. Do not select cache/data wipe options.
2. In PowerShell, select the device again; its transport may have changed:

```powershell
.\adb.exe devices
$RecoverySerial = Read-Host 'Enter the serial shown in sideload mode'
if ([string]::IsNullOrWhiteSpace($RecoverySerial)) { throw 'No device selected' }
.\adb.exe -s $RecoverySerial sideload '.\lineage-24.0-20261125-UNOFFICIAL-cannon.zip'
```

3. Wait for **OrangeFox's signature verification and installation success**.
   The host percentage alone is not installation proof.
4. Reboot to System only after recovery reports success. Do not install Magisk,
   Google apps, add-on survival scripts, or application-hook modules during
   the vanilla installation.

If recovery reports an unexpected DTBO or recovery partition, **stop before
booting**. Recheck the downloaded set, checksums and completed fastboot flashes.
Do not remove the assertion, flash random firmware, or format userdata.
For another failure, keep the exact error and recovery log privately for
diagnosis; do not repeatedly wipe or retry blindly.

## What installation changes

The ZIP installs the matched `boot`, `system`, `vendor`, `product`, `system_ext`,
`vbmeta_system`, `vbmeta_vendor`, and `vbmeta` images and updates the four logical
OS partition sizes. The preceding fastboot steps install the matching `dtbo`
and `recovery`.

The ZIP does not format userdata or restore old root/Google add-ons. It does not
flash firmware, preloader, calibration, modem/NVRAM, identity, security keys,
or backup storage.

See `RELEASE_NOTES.md` for the tested scope and known limitations. A successful
flash does not imply support for every app, accessory, network, or starting ROM.
