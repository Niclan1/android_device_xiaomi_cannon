# Mainline SELinux policy

Linux 6.18 uses DRM, LED-class haptics, native backlight and power-supply
paths, and memfd buffers rather than ashmem. Keep the legacy labels too.

## Labels before permissions

- DRM primary and render nodes use `gpu_device`. The shared MediaTek
  `base/vendor/file_contexts` must not contain the old exact `card0`
  exception assigning `dri_device`; an exact match overrides subtree regexes.
  Allocator and charger permissions follow the corrected label. Composer uses
  the platform GPU SPHAL policy; ordinary apps exclude `isolated_app_all`.
- Label the haptic LED subtree `sysfs_vibrator`, LM36273 backlight and LED
  brightness `sysfs_leds`, battery attributes `sysfs_batteryinfo`, and wakeup
  subtrees `sysfs_wakeup`. The RTC retains its existing `sysfs_rtc` label.
  Genfs entries are literal prefixes, not regular expressions. The `wakeup`
  prefix also matches numbered children; do not pin dynamically assigned IDs.
- The legacy mnld binary probes `ro.logsystem.usertype` even when unset. It is
  a logging-build integer and uses the existing public `log_prop` label.
  Its `vendor.gps.almanac` string uses `vendor_mtk_mnld_prop`. Existing reads
  of those types suffice; never grant mnld access to `default_prop`.
  Its backlight watch is already covered by `sysfs_leds` `r_file_perms`.

## Shared memory

The policy does not enable `memfd_class` or alter kernel capabilities.
Use file-class permissions on the observed domain-specific tmpfs types:
Codec2 surface/FMQ buffers, AudioTrack MemoryHeapBase, camera Parcel Blob,
metadata retriever and extractor buffers. Plain `tmpfs` FMQs are limited to
participating app/media/system/HAL domains. Do not grant execution, relabeling
or generic cross-domain file access.

## Validation and remaining work

Host validation regenerates the policy using the configured M4 flags and
source lists from the existing Ninja graph, including newly added device
files. Run `checkpolicy -M -c 30` with assertions enabled; context checks use
`checkfc` and `property_info_checker`. The platform's `policy.py` and built
`libsepolwrap.so` can query effective rules and compiled genfs entries.
DRM lookups must cover the directory, card0 and renderD128 together with
shared MediaTek contexts, not just this device's file in isolation.

The 2026-11-11 AVC capture identifies `diag_blklog`'s unlabeled block inode
8388644 as dev_t 8:36: `/dev/block/sdc4`, partition `expdb`. Both the node and
by-name symlink already have `expdb_block_device`; the existing kernel rule
allows that type. The denial is on an internal `bdev` filesystem inode with
path `/ (deleted)`, not the labelled `/dev` inode. Another `file_contexts`
entry cannot label it. A targeted kernel logger/open-path fix is still
required; do not label all of `bdev`, allow `unlabeled`, or modify expdb data.

Magisk's zygote-to-`adb_data_file` denials are intentionally not addressed.
Default/vendor-default property probes from other processes, unlabelled
service-manager lookups and Magisk-mounted APEX tmpfs files remain outside
this change. Host compilation is not enforcing-mode runtime acceptance:
rebuild, deploy through the normal userdata-preserving path, and recapture
AVCs before enabling enforcing on the daily-driver phone.
