#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reproduce the exact two MTK telephony API-owner fixes in a separate JAR.

Upstream: begonia-dev/mediatek-telephony-base-jar c2be40fc862bf88315eec0d52ee0945134db6441.
Preserves every disassembled instruction/prototype except the two owner changes;
permits only the assembler's documented default-false static-value canonicalization.
Never modifies the input, Android source tree, Git state or a connected device.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, struct, subprocess, zipfile, zlib

JAR_SHA = 'b5f7720204345774e49cbfaf5de9d99b5c52c809233f91a51d8bcc8c1d324d48'
TOOL_SHA = {
    'smali.jar': 'b8f790266a640a0de35391dc91fc12c7519ae4c5501f12496b138003fe4631ef',
    'baksmali.jar': '9b821ea330526f97231888402664b50617b81561e8b2d6bc21c55c358bc8440f',
}
OLD = 'Landroid/telephony/SubscriptionManager;->getSimStateForSlotIndex(I)I'
NEW = 'Landroid/telephony/TelephonyManager;->getSimStateForSlotIndex(I)I'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True, help='Pinned smali/baksmali JAR directory')
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True, help='New directory; never reused or deleted')
    args = parser.parse_args()
    jar, tools, java, PREP = args.input.resolve(), args.tools.resolve(), args.java.resolve(), args.work_dir.resolve()
    assert not jar.is_symlink() and jar.is_file()
    assert sha(jar) == JAR_SHA, 'Exact original JAR input required'
    assert not args.output.exists() and not PREP.exists(), 'Refuse to overwrite output/work directory'
    assert args.output.resolve() != jar
    for name, expected in TOOL_SHA.items():
        assert sha(tools / name) == expected, 'Pinned assembler/disassembler changed'
    PREP.mkdir(parents=True)
    resume = False
    def tool(name, *values):
        with (PREP / (name + '.log')).open('ab') as log:
            subprocess.run([str(java), '-Xmx256m', '-jar', str(tools / name), *map(str, values)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    with zipfile.ZipFile(jar) as old_zip:
        entries = old_zip.infolist()
        assert [x.filename for x in entries] == ['META-INF/MANIFEST.MF', 'classes.dex']
        original_dex = old_zip.read('classes.dex')
        assert original_dex[:8] == b'dex\n039\0' and old_zip.testzip() is None
        assert not any(x.filename.upper().endswith(('.RSA', '.DSA', '.EC', '.SF')) for x in entries)
        original_members = {x.filename: old_zip.read(x.filename) for x in entries}
    original = PREP / 'original'
    if not resume:
        tool('baksmali.jar', 'd', '-a', '31', '--debug-info', 'true', '-j', '1', '-o', original, jar)
    old_classes = {str(p.relative_to(original)): p.read_text() for p in original.rglob('*.smali')}
    assert sum(s.count(OLD) for s in old_classes.values()) == 2
    assert sum(s.count(NEW) for s in old_classes.values()) == 0
    patched = PREP / 'patched'
    if not resume:
        # Decoded source text needs no inherited filesystem metadata. Avoid
        # copytree/copy2 directory chmod/copystat requirements on shared mounts.
        for relative, source in old_classes.items():
            target = patched / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
    changed = []
    for relative, source in old_classes.items():
        if OLD in source:
            changed.append(relative)
            if not resume:
                (patched / relative).write_text(source.replace(OLD, NEW))
    assert changed == ['com/mediatek/telephony/MtkTelephonyManagerEx.smali']
    expected_classes = {p: s.replace(OLD, NEW) for p, s in old_classes.items()}
    assert {str(p.relative_to(patched)): p.read_text() for p in patched.rglob('*.smali')} == expected_classes
    dex = PREP / 'classes.dex'
    if not resume:
        tool('smali.jar', 'a', '-a', '31', '-j', '1', '-o', dex, patched)
    data = dex.read_bytes()
    assert data[:8] == original_dex[:8]
    assert data[12:32] == hashlib.sha1(data[32:]).digest()
    assert struct.unpack_from('<I', data, 8)[0] == zlib.adler32(data[12:]) & 0xffffffff
    rebuilt = PREP / 'mediatek-telephony-base-owner-fixed.jar'
    if not resume:
        with zipfile.ZipFile(rebuilt, 'w') as output:
            for entry in entries:
                output.writestr(entry, data if entry.filename == 'classes.dex' else original_members[entry.filename])
    with zipfile.ZipFile(rebuilt) as output:
        assert output.testzip() is None and output.namelist() == [x.filename for x in entries]
        assert output.read('META-INF/MANIFEST.MF') == original_members['META-INF/MANIFEST.MF']
        assert output.read('classes.dex') == data
        assert [x.compress_type for x in output.infolist()] == [x.compress_type for x in entries]
    decoded = PREP / ('redecoded-resume' if resume else 'redecoded')
    assert not decoded.exists(), 'Preserve prior independent verification'
    tool('baksmali.jar', 'd', '-a', '31', '--debug-info', 'true', '-j', '1', '-o', decoded, rebuilt)
    actual_classes = {str(p.relative_to(decoded)): p.read_text() for p in decoded.rglob('*.smali')}
    # dexlib2 omits the trailing default false initializer for this exact field.
    # DEX static_values_off specifies type-appropriate zero for omitted values:
    # https://source.android.com/docs/core/runtime/dex-format#class-def-item
    canonical_class = 'com/mediatek/internal/telephony/MtkSubscriptionManager.smali'
    explicit = '.field private static final VDBG:Z = false\n'
    implicit = '.field private static final VDBG:Z\n'
    assert expected_classes[canonical_class].count(explicit) == 1
    assert actual_classes[canonical_class] == expected_classes[canonical_class].replace(explicit, implicit)
    canonical_expected = dict(expected_classes)
    canonical_expected[canonical_class] = canonical_expected[canonical_class].replace(explicit, implicit)
    assert actual_classes == canonical_expected, 'Other instructions, annotations or prototypes changed'
    assert sum(s.count(OLD) for s in actual_classes.values()) == 0
    assert sum(s.count(NEW) for s in actual_classes.values()) == 2
    methods = lambda classes: {p: re.findall(r'^\.method .+$', s, re.M) for p, s in classes.items()}
    assert methods(old_classes) == methods(actual_classes)
    assert len(actual_classes) == 128
    method_count = sum(len(v) for v in methods(actual_classes).values())
    assert method_count == 1239
    expected_output = '48f42f2501c308a47568517c58e8d5d351d7d0d52e108f06a8bef0f7a40211a4'
    assert sha(rebuilt) == expected_output, 'Output is not the audited source JAR'
    with args.output.open('xb') as output:
        output.write(rebuilt.read_bytes())
    print(json.dumps({'status': 'EXACT_TWO_OWNER_FIX_REPRODUCED', 'output_sha256': expected_output,
                      'classes': 128, 'methods': method_count, 'old_invocations': 0, 'new_invocations': 2}))


if __name__ == '__main__':
    main()
