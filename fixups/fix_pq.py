#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reproduce the audited PQ TinyXML ABI and file-backed PT_PHDR repair.

Uses the existing LineageOS libtinyxml2-v34 selection and an ELF-layout repair;
does not replace Bionic, change load permissions or disable PQ functionality.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from pq_elf_phdr import repair, validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


INPUTS = [
    ('lib/hw/vendor.mediatek.hardware.pq@2.13-impl.so',
     '70ebf4f82b53e429aa57410f346490f97e368fb2e550f57152b8a5eb8e0729d8',
     '1221809f03b7834195699c2a8633865418b5dea68a4a69224c8f681e5fb63186'),
    ('lib64/hw/vendor.mediatek.hardware.pq@2.13-impl.so',
     '87b421512356f1a5c3a37f73ac0483ff4def5f9f5b8c66ed13764159b5a528ee',
     'a5f8202e6f309a373b4e50443bb5c23d7b512df2204fbeb59e734cc13cea5f5d'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-vendor', type=Path, required=True)
    parser.add_argument('--output-vendor', type=Path, required=True)
    parser.add_argument('--patchelf', type=Path, required=True)
    args = parser.parse_args()
    pin = json.loads((Path(__file__).resolve().parent / 'patchelf-pin.json').read_text())
    assert sha(args.patchelf) == pin['sha256'], 'Pinned extract-tools patchelf 0_18 required'
    assert not args.output_vendor.exists(), 'Refuse to overwrite output'
    for relative, before, _ in INPUTS:
        assert sha(args.input_vendor / relative) == before, 'Unexpected PQ input: ' + relative
    results = []
    for relative, _, expected in INPUTS:
        source, target = args.input_vendor / relative, args.output_vendor / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        before = subprocess.check_output([str(args.patchelf), '--print-needed', str(source)], text=True).splitlines()
        assert before.count('libtinyxml2.so') == 1 and 'libtinyxml2-v34.so' not in before
        subprocess.run([str(args.patchelf), '--page-size', '4096', '--replace-needed',
                        'libtinyxml2.so', 'libtinyxml2-v34.so', str(target)], check=True)
        fixed, result = repair(target.read_bytes())
        validate(fixed)
        target.write_bytes(fixed)
        after = subprocess.check_output([str(args.patchelf), '--print-needed', str(target)], text=True).splitlines()
        assert after == [x.replace('libtinyxml2.so', 'libtinyxml2-v34.so') for x in before]
        assert sha(target) == expected, 'Result differs from audited final PQ artifact'
        results.append({'path': relative, 'sha256': expected, 'file_backed_phdr': True,
                        'address_fields_only_after_dependency_rewrite': result['all_other_bytes_unchanged']})
    print(json.dumps({'status': 'EXACT_TWO_PQ_FIXUPS_REPRODUCED', 'files': results}))


if __name__ == '__main__':
    main()
