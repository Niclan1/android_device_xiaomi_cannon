#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Replay the audited seven-blob symbol rename into a new output directory.

Uses the unchanged Apache-2.0 upstream renamer credited in CREDITS.md.
Only exact input and output hashes are accepted. No input is modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-lib64', type=Path, required=True)
    parser.add_argument('--modern-libutils', type=Path, required=True)
    parser.add_argument('--output-lib64', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'mtkutils-inputs.json').read_text())
    renamer = here / 'rename_mtkutils.py'
    assert sha(renamer) == manifest['renamer_sha256'], 'Upstream renamer changed'
    assert sha(args.modern_libutils) == manifest['modern_vendor_libutils_sha256'], 'Exact platform libutils required'
    assert not args.output_lib64.exists(), 'Refuse to overwrite an output directory'
    for item in manifest['inputs']:
        name = item['name']
        assert Path(name).name == name and name.endswith('.so')
        source = args.input_lib64 / name
        assert source.is_file() and not source.is_symlink()
        assert sha(source) == item['before_sha256'], 'Unexpected source blob: ' + name
    args.output_lib64.mkdir(parents=True)
    for item in manifest['inputs']:
        shutil.copyfile(args.input_lib64 / item['name'], args.output_lib64 / item['name'])
    subprocess.run([sys.executable, str(renamer), str(args.modern_libutils), str(args.output_lib64)], check=True)
    for item in manifest['inputs']:
        assert sha(args.output_lib64 / item['name']) == item['after_sha256'], 'Unexpected renamed blob: ' + item['name']
    print(json.dumps({'status': 'EXACT_SEVEN_BLOB_RENAME_REPRODUCED', 'files': len(manifest['inputs'])}))


if __name__ == '__main__':
    main()
