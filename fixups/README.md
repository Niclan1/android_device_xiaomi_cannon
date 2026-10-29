# Reproducible vendor fixups

These tools operate on separate input/output paths. They do not edit Android sources, access a phone, install dependencies or invoke a build. Inputs are pinned to the audited source artifacts; an unexpected firmware or tool revision fails rather than receiving a speculative patch. Follow [the source attribution](../CREDITS.md).

## libmtkutils symbol isolation

`rename_mtkutils.py` is unchanged upstream Apache-2.0 source from [itskenny0 / rabbit-r1 commit 8eac590](https://github.com/haretic/android_device_rabbit_r1/blob/8eac590e24b83c24f39fada228132bda6b3b98fc/modem/rename-mtkutils.py). Its SHA-256 is pinned in `mtkutils-inputs.json`. The wrapper restricts its input/output to the seven audited dependent blobs and requires the exact platform vendor `libutils.so` used by the validated integration.

```sh
python3 fix_mtkutils.py \
  --input-lib64 ORIGINAL_VENDOR_LIB64 \
  --modern-libutils PLATFORM_VENDOR_LIBUTILS_SO \
  --output-lib64 NEW_RENAMED_LIB64
```

Original and transformed source hashes are listed in `mtkutils-inputs.json`. They identify generic software artifacts, not a particular phone's calibration or backup. The wrapper requires byte-identical expected results for all seven files.

## MTK telephony API owners

`fix_telephony_owner.py` adapts [SamarV-121 / begonia-dev c2be40f](https://github.com/begonia-dev/mediatek-telephony-base-jar/commit/c2be40fc862bf88315eec0d52ee0945134db6441). It replaces exactly two `getSimStateForSlotIndex` invocation owners, retaining every other disassembled instruction, annotation and method prototype. It permits only one documented explicit-false to implicit-default-false static metadata normalization by dexlib2.

```sh
python3 fix_telephony_owner.py \
  --input ORIGINAL_MEDIATEK_TELEPHONY_BASE_JAR \
  --output NEW_MEDIATEK_TELEPHONY_BASE_JAR \
  --tools PINNED_SMALI_DIRECTORY \
  --java JAVA_EXECUTABLE \
  --work-dir NEW_TEMPORARY_DIRECTORY
```

The tool requires the original JAR SHA-256 `b5f7720204345774e49cbfaf5de9d99b5c52c809233f91a51d8bcc8c1d324d48` and produces source JAR SHA-256 `48f42f2501c308a47568517c58e8d5d351d7d0d52e108f06a8bef0f7a40211a4`. Smali and baksmali hashes are checked against the pinned Android extract-tools inputs. ZIP CRC, DEX SHA-1/Adler32, 128 classes, 1,239 method signatures, zero old-owner invokes and two new-owner invokes are all required. Subsequent ART hiddenapi processing may legitimately change the installed JAR header/ZIP metadata; validate its instructions against this audited source.

## PQ compatibility

`fix_pq.py` selects the existing `libtinyxml2-v34` implementation, then uses the licensed `pq_elf_phdr.py` helper to make PT_PHDR refer to the actual file-backed program-header table. Only the table's two address fields change after the dependency rewrite; Bionic validation and load permissions remain intact. `patchelf-pin.json` identifies the exact extract-tools 0_18 binary.

```sh
python3 fix_pq.py --input-vendor ORIGINAL_VENDOR_DIRECTORY \
  --output-vendor NEW_FIXED_VENDOR_DIRECTORY --patchelf PINNED_PATCHELF_0_18
```

Both architecture outputs are required to match the tested deployment artifacts exactly: ARM `1221809f03b7834195699c2a8633865418b5dea68a4a69224c8f681e5fb63186`, ARM64 `a5f8202e6f309a373b4e50443bb5c23d7b512df2204fbeb59e734cc13cea5f5d`. `replay-validation.json` records successful real-input replay of all three fixups. Candidate `182454Z` also passed owner brightness/wake checks and the final bounded PQ service-stability capture. The device extraction source includes the same transformation for future extractions.

These recipes supplement the firmware extraction list. They do not establish redistribution rights for proprietary vendor payloads or replace their notices.
