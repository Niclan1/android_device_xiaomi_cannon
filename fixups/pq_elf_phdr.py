# SPDX-License-Identifier: Apache-2.0
"""Validate ARM shared-object PT_PHDR against actual file-backed PT_LOAD bytes.

The bounded repair changes only PT_PHDR p_vaddr/p_paddr. It does not relocate
segments, alter permissions, weaken Bionic checks or change any file contents
outside those address fields. CLI is read-only; callers own write-path guards.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAX_BYTES = 16 * 2**20


def layout(data):
    if not 52 <= len(data) <= MAX_BYTES or data[:4] != b'\x7fELF' or data[5:7] != b'\x01\x01':
        raise ValueError('Bounded little-endian ELF required')
    bits = data[4]
    if bits == 2:
        if len(data) < 64: raise ValueError('Truncated ELF64 header')
        phoff = struct.unpack_from('<Q', data, 32)[0]
        ehsize, entsize, count = struct.unpack_from('<HHH', data, 52)
        fmt, expected_header, expected_entry, machine = '<IIQQQQQQ', 64, 56, 183
        offsets, width = (16, 24), 8
    elif bits == 1:
        phoff = struct.unpack_from('<I', data, 28)[0]
        ehsize, entsize, count = struct.unpack_from('<HHH', data, 40)
        fmt, expected_header, expected_entry, machine = '<IIIIIIII', 52, 32, 40
        offsets, width = (8, 12), 4
    else:
        raise ValueError('Unsupported ELF class')
    etype, actual_machine, version = struct.unpack_from('<HHI', data, 16)
    if etype != 3 or actual_machine != machine or version != 1 or ehsize != expected_header or entsize != expected_entry:
        raise ValueError('Exact ARM/ARM64 ET_DYN header required')
    size = count * entsize
    if not 1 <= count or size >= 65536 or phoff < ehsize or phoff % width or phoff + size > len(data):
        raise ValueError('Program header table outside bounded file')
    headers = []
    limit = 1 << (width * 8)
    for i in range(count):
        h = struct.unpack_from(fmt, data, phoff + i * entsize)
        if bits == 2: typ, flags, off, va, pa, fs, ms, align = h
        else: typ, off, va, pa, fs, ms, flags, align = h
        row = dict(type=typ, flags=flags, offset=off, vaddr=va, paddr=pa, filesz=fs, memsz=ms, align=align, index=i)
        if typ == 1:
            if fs > ms or off + fs > len(data) or va + ms >= limit or pa + ms >= limit:
                raise ValueError('LOAD file/memory range invalid')
            if align > 1 and (align & (align - 1) or (va - off) % align):
                raise ValueError('LOAD alignment/congruence invalid')
            if flags & 7 == 7 or not flags & 4:
                raise ValueError('Unreadable/RWX LOAD refused')
        headers.append(row)
    tables = [h for h in headers if h['type'] == 6]
    if len(tables) != 1:
        raise ValueError('Exactly one PT_PHDR required')
    table = tables[0]
    if table['offset'] != phoff or table['filesz'] != size or table['memsz'] != size or table['flags'] != 4:
        raise ValueError('PT_PHDR offset/size/read permission inconsistent')
    loads = [h for h in headers if h['type'] == 1 and h['offset'] <= phoff and phoff + size <= h['offset'] + h['filesz']]
    if len(loads) != 1:
        raise ValueError('Table must have one unambiguous file-backed LOAD mapping')
    load = loads[0]; delta = phoff - load['offset']
    address, physical = load['vaddr'] + delta, load['paddr'] + delta
    covered = [h for h in headers if h['type'] == 1 and h['vaddr'] <= table['vaddr'] and table['vaddr'] + size <= h['vaddr'] + h['filesz']]
    return dict(bits=width * 8, phoff=phoff, phentsize=entsize, phnum=count,
                phdr=table, load=load, expected_vaddr=address, expected_paddr=physical,
                address_field_offsets=[phoff + table['index'] * entsize + n for n in offsets],
                bionic_file_backed_coverage=bool(covered),
                exact_table_mapping=table['vaddr'] == address and table['paddr'] == physical,
                headers=headers)


def validate(data):
    result = layout(data)
    if not result['bionic_file_backed_coverage'] or not result['exact_table_mapping']:
        raise ValueError('PT_PHDR does not point to actual file-backed program header table')
    return result


def repair(data):
    before = layout(data)
    result = bytearray(data)
    fmt = '<Q' if before['bits'] == 64 else '<I'
    for offset, value in zip(before['address_field_offsets'], [before['expected_vaddr'], before['expected_paddr']]):
        struct.pack_into(fmt, result, offset, value)
    result = bytes(result); after = validate(result)
    allowed = {j for off in before['address_field_offsets'] for j in range(off, off + before['bits'] // 8)}
    changed = [i for i, (a, b) in enumerate(zip(data, result)) if a != b]
    if set(changed) - allowed or len(result) != len(data):
        raise AssertionError('Repair exceeded two PT_PHDR address fields')
    report = {'bits': before['bits'], 'phoff': before['phoff'], 'phnum': before['phnum'],
              'before_vaddr': before['phdr']['vaddr'], 'before_paddr': before['phdr']['paddr'],
              'after_vaddr': after['phdr']['vaddr'], 'after_paddr': after['phdr']['paddr'],
              'changed_byte_offsets': changed, 'allowed_field_offsets': before['address_field_offsets'],
              'file_backed_table_offset': before['phoff'], 'file_backed_load_index': before['load']['index'],
              'before_sha256': hashlib.sha256(data).hexdigest(), 'after_sha256': hashlib.sha256(result).hexdigest(),
              'bionic_file_backed_coverage': True, 'all_other_bytes_unchanged': True}
    return result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    if not args.file.is_file() or args.file.stat().st_size > MAX_BYTES:
        raise ValueError('Bounded existing ELF file required')
    result = validate(args.file.read_bytes())
    print(json.dumps({'status': 'VALID_FILE_BACKED_PHDR_MAPPING_ONLY', 'bits': result['bits'], 'phoff': result['phoff'], 'phnum': result['phnum']}))


if __name__ == '__main__': main()
