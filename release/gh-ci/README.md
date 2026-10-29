# Hosted EROFS packaging

This workflow runs on a standard GitHub-hosted Ubuntu24.04 runner with Java17,
Python3, OpenSSL and the distro Brotli CLI. It needs no development PC,
Android checkout, root, phone or private credential. The repository's normal
GitHub token is used only to publish the resulting experimental prerelease.

It **reuses compiled images**. It does not build Android or the kernel from
source. The fixed vanilla ROM and rootless EROFS boot/vbmeta input ZIP are pinned
by complete size/SHA256 in `inputs.json`, as is the public AOSP signing toolkit.
For network reliability the base ROM is transported as ordered parts, each
limited to64MiB. The pinned manifest and every part are verified before joining;
the complete joined ROM must still match the original fixed SHA256. Parts created
by the downloader are removed only after that complete check.
The kernel source is published at revision
`9b1c084c00cf9a82964387db268bfeceba803b96`; its source tree matches the compiled
development revision recorded in the input manifest. Git-derived version strings
can differ when rebuilding that source; bit-identical rebuilds are not claimed.

## Checks

The packager verifies source ZIP hashes, safe/unique member paths, signing-tool
member hashes and the public AOSP test certificate. It verifies the base whole-file
signature, original ramdisk/DTB/header preservation, the actual replacement
kernel hash, fixed OS-only resize operations and Android17 manual-Recovery metadata.

All four filesystem images are reconstructed from exact full BLOCKv4/Brotli
streams and checked against their complete expected SHA256 values. The pinned
AOSP AVB implementation verifies the top RSA signature, unchanged key/flags/
rollback policy, exact equality of all non-boot descriptors, the boot footer/top
hash, both child signatures and the four filesystem hashtrees. The DTBO image
is intentionally absent from the installer; its unchanged descriptor is inherited
from the pinned verified base. No fresh DTBO read/hash check is claimed.

Only boot.img, top vbmeta.img, their two Edify raw-readback SHA1 assertions and
the source/qualification metadata are changed. The original OTA metadata text and
protobuf stay byte-identical; this remains a manual-Recovery package without
streaming-offset metadata. The new ZIP is whole-file signed using the published
AOSP development test key. OpenSSL verifies its exact Android-Recovery PKCS7
boundary against the pinned certificate. ZIP CRC and complete SHA256 equality of
every unchanged entry are checked after signing.

The four temporary expanded images are deleted **after** AVB validation and
before repacking/signing. Only exact regular files created inside the new scratch
directory are eligible for cleanup. Existing output directories, local input
archives and original vanilla artifacts are never cleaned or overwritten. The
download route requires14GB free initially and the packaging route requires12GB
free; memory-intensive Android compilation is not involved.

## Run

After the fixed public assets exist under the repository's
`build-inputs-20261029-v3` prerelease, select **Package unrooted EROFS ROM (hosted
Ubuntu)** in Actions and run it manually as `Niclan1`. It has no push/PR trigger,
uses no Actions artifact/cache upload, and does not cancel an existing run.
Successful results are uploaded to a new draft Release. Exact server asset
names, sizes and SHA256 digests must match all three local output files before
the draft is published as an `erofs-ci-RUN-ATTEMPT` prerelease. A failed upload
remains a draft; nothing is overwritten or deleted. Results are never marked
latest automatically.

For a local Linux replay with the same public inputs:

```sh
python3 release/gh-ci/pack_erofs.py --work-dir /tmp/cannong-erofs-new-run
```

For an offline replay with already verified downloads:

```sh
python3 release/gh-ci/pack_erofs.py --work-dir /tmp/cannong-erofs-offline-run \
  --base-rom /path/to/lineage-24.0-20261029-UNOFFICIAL-cannong.zip \
  --erofs-inputs /path/to/ci-erofs-inputs.zip \
  --toolkit /path/to/cannong-public-signing-toolkit-v1.zip
```

`--java` and `--brotli` accept installed executable paths. All output stays below
the new work directory. Publish only its `artifacts/` directory, containing the
signed ZIP, SHA256 sidecar and sanitized validation report.

The resulting exact full ZIP is **physically untested**, even though its input
kernel was functionally tested. Installation of the final ZIP, first boot,
rollback and hardware/application acceptance are separate gates. It adds no
Magisk, Google apps, Recovery image, personal data or userdata-format operation.

## Source and licenses

`vendor/avbtool.py` is unchanged AOSP source at
[`cb5eae91a6b83e1394882decbf6de133239107e1`](https://android.googlesource.com/platform/external/avb/+/cb5eae91a6b83e1394882decbf6de133239107e1/avbtool.py),
with its original MIT copyright/license notice and the repository aggregate license
`vendor/AVB_LICENSE.txt`. The new packaging
source is Apache2.0 (`LICENSE.txt`). The signing toolkit includes its AOSP, Conscrypt, BoringSSL
and BouncyCastle source revisions/notices and only the publicly distributed AOSP
test key. ROM/kernel components retain their original licenses and attribution;
see the [published source manifest and credits](https://github.com/Niclan1/android_device_xiaomi_cannon/tree/release-manifest). No private signing, attestation,
account, backup or device-identity material is included.
