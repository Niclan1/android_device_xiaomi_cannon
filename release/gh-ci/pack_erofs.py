#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Repackage fixed vanilla OTA with a fixed unrooted EROFS boot/AVB pair.

Linux/Python3 + Java11+ + OpenSSL + Brotli CLI. No Android checkout, phone,
module installation or source compilation is used.
"""
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
RAW = ('boot', 'vbmeta_system', 'vbmeta_vendor', 'vbmeta')
LOGICAL = {'system': 2418331648, 'vendor': 778838016, 'product': 1817784320, 'system_ext': 1769865216}
SCRIPT = 'META-INF/com/google/android/updater-script'
META = 'META-INF/com/android/metadata'
RELEASE = 'META-INF/com/android/cannong-release.json'
SKIPPED_SIGNATURES = {'META-INF/MANIFEST.MF', 'META-INF/CERT.SF', 'META-INF/CERT.RSA'}
BLOCK = 4096


def fail(message): raise RuntimeError(message)


def sha(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(8 * 2**20), b''): h.update(data)
    return h.hexdigest()


def zip_sha(archive, name):
    h = hashlib.sha256()
    with archive.open(name) as f:
        for data in iter(lambda: f.read(8 * 2**20), b''): h.update(data)
    return h.hexdigest()


def checked_zip(path):
    archive = zipfile.ZipFile(path)
    names = archive.namelist()
    if len(names) != len(set(names)): fail('Duplicate ZIP members')
    for entry in archive.infolist():
        p = PurePosixPath(entry.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
            fail('Unsafe ZIP member')
    return archive


def check_file(path, row):
    if not Path(path).is_file() or Path(path).stat().st_size != row['bytes'] or sha(path) != row['sha256']:
        fail('Pinned input size/SHA256 mismatch: ' + Path(path).name)


def verify_uploaded_assets(folder, release):
    files = {p.name: p for p in folder.iterdir()}
    zips = [n for n in files if n.endswith('.zip')]
    if len(zips) != 1 or set(files) != {zips[0], zips[0] + '.sha256', 'validation.json'}:
        fail('Exactly the generated ZIP, SHA256 sidecar and validation report required')
    if any(p.is_symlink() or not p.is_file() for p in files.values()): fail('Output upload scope is not regular files')
    rows = release.get('assets', [])
    assets = {row['name']: row for row in rows}
    if (release.get('draft') is not True or release.get('prerelease') is not True
            or len(rows) != len(assets) or set(assets) != set(files)):
        fail('Exact draft prerelease asset scope required before publication')
    for name, path in files.items():
        row = assets[name]
        if row.get('state') != 'uploaded' or row.get('size') != path.stat().st_size or row.get('digest') != 'sha256:' + sha(path):
            fail('Server asset size/full SHA256 mismatch: ' + name)


def download(row, folder):
    url = urllib.parse.urlsplit(row['url'])
    if (url.scheme != 'https' or url.hostname != 'github.com' or url.username or url.password
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', row['filename'])
            or not isinstance(row['bytes'], int) or row['bytes'] <= 0
            or not re.fullmatch(r'[0-9a-f]{64}', row['sha256'])):
        fail('Fixed public GitHub HTTPS asset with safe name/size/hash required')
    target = folder / row['filename']
    for attempt in range(3):
        partial = folder / (row['filename'] + '.partial')
        try:
            request = urllib.request.Request(row['url'], headers={'User-Agent': 'cannong-erofs-packager/1'})
            with urllib.request.urlopen(request, timeout=60) as src, partial.open('xb') as out:
                if urllib.parse.urlsplit(src.geturl()).scheme != 'https': fail('Insecure download redirect')
                count = 0
                while data := src.read(8 * 2**20):
                    count += len(data)
                    if count > row['bytes']: fail('Downloaded input exceeds pinned size')
                    out.write(data)
            check_file(partial, row)
            partial.rename(target)
            return target
        except Exception:
            if partial.exists() and partial.parent == folder: partial.unlink()
            if attempt == 2: raise
            time.sleep(1 + 2 * attempt)


def join_base_parts(manifest, expected, parts, target):
    """Join only verified ordered inputs; never trust a partial or reordered base."""
    expected_source = {'name': expected['filename'], 'bytes': expected['bytes'], 'sha256': expected['sha256']}
    part_limit = manifest.get('max_part_bytes')
    if (manifest.get('format') != 1 or manifest.get('source') != expected_source
            or not isinstance(part_limit, int) or not 0 < part_limit <= 67108864):
        fail('Chunk manifest does not identify the exact pinned vanilla ROM')
    rows = manifest.get('parts', [])
    if not 2 <= len(rows) <= 64 or len(parts) != len(rows) or len({r.get('name') for r in rows}) != len(rows):
        fail('Require2..64 distinct ordered base parts')
    if any(not isinstance(r.get('bytes'), int) or not 0 < r['bytes'] <= part_limit for r in rows):
        fail('Base part exceeds the pinned transport bound')
    if sum(r['bytes'] for r in rows) != expected['bytes']:
        fail('Base part sizes do not match the pinned ROM')
    for path, row in zip(parts, rows): check_file(path, row)
    with target.open('xb') as out:
        for path in parts:
            with path.open('rb') as src: shutil.copyfileobj(src, out, 8 * 2**20)
    check_file(target, expected)
    return target


def download_base_parts(policy, folder):
    row = policy['base_parts_manifest']
    manifest_file = download(row, folder)
    manifest = json.loads(manifest_file.read_text())
    prefix = 'https://github.com/' + policy['repository'] + '/releases/download/' + policy['seed_tag'] + '/'
    rows = manifest.get('parts', [])
    if not 2 <= len(rows) <= 64: fail('Require2..64 ordered base parts')
    parts = [download({'filename': r['name'], 'bytes': r['bytes'], 'sha256': r['sha256'], 'url': prefix + r['name']}, folder) for r in rows]
    base = join_base_parts(manifest, policy['assets']['base_rom'], parts, folder / policy['assets']['base_rom']['filename'])
    for path in parts: safe_unlink_created(path, folder)
    return base


def unpack_selected(archive, destination, names):
    for name in names:
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name: fail('Unsafe extraction selection')
        target = destination.joinpath(*p.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as src, target.open('xb') as out: shutil.copyfileobj(src, out, 8 * 2**20)


def parse_boot(data):
    if len(data) != 67108864 or data[:8] != b'ANDROID!': fail('Exact64MiB legacy boot image required')
    u32 = lambda off: struct.unpack_from('<I', data, off)[0]
    page = u32(36)
    if page != 2048 or u32(40) != 2 or u32(1644) != 1660 or u32(24) or u32(1632):
        fail('Unexpected cannon v2 boot header')
    align = lambda n: (n + page - 1) // page * page
    kend = page + u32(8); rstart = align(kend); rend = rstart + u32(16)
    dstart = align(rend); dend = dstart + u32(1648)
    if not page < kend <= rstart < rend <= dstart < dend <= len(data): fail('Boot payload bounds invalid')
    header = bytearray(data[:1660]); header[8:12] = bytes(4); header[576:608] = bytes(32)
    return bytes(header), data[page:kend], data[rstart:rend], data[dstart:dend]


def replace_assertions(original, old, new):
    text = original.decode('utf-8')
    for name in ('boot', 'vbmeta'):
        blocks = len(new[name]) // BLOCK
        prefix = 'range_sha1("/dev/block/by-name/' + name + '", "2,0,' + str(blocks) + '") == "'
        before = prefix + hashlib.sha1(old[name]).hexdigest() + '"'
        if text.count(before) != 1: fail('Exact base raw image readback assertion missing: ' + name)
        text = text.replace(before, prefix + hashlib.sha1(new[name]).hexdigest() + '"')
    return ('ui_print("Experimental EROFS CI package: this exact ZIP is not physically tested.");\n' + text).encode()


def parse_transfer(data, size):
    lines = data.decode('ascii').strip().splitlines()
    blocks = size // BLOCK
    if lines != ['4', str(blocks), '0', '0', 'new 2,0,' + str(blocks)]:
        fail('Only exact full contiguous BLOCKv4 new transfer is accepted')


def reconstruct(archive, name, size, target, brotli):
    parse_transfer(archive.read(name + '.transfer.list'), size)
    if archive.read(name + '.patch.dat') != b'': fail('Unexpected incremental patch payload')
    with target.open('xb') as out, tempfile_error(target.parent, name) as error:
        process = subprocess.Popen([brotli, '--decompress', '--stdout'], stdin=subprocess.PIPE, stdout=out, stderr=error)
        try:
            with archive.open(name + '.new.dat.br') as src:
                while data := src.read(8 * 2**20): process.stdin.write(data)
            process.stdin.close()
            if process.wait(timeout=180): fail('Brotli image reconstruction failed: ' + name)
        finally:
            if process.poll() is None: process.kill(); process.wait()
    if target.stat().st_size != size: fail('Reconstructed image size mismatch: ' + name)
    return sha(target)


def tempfile_error(folder, name):
    return (folder / (name + '.stderr.log')).open('xb')


def signature_footer(archive):
    size = archive.stat().st_size
    with archive.open('rb') as f:
        if size < 28: fail('Truncated whole-file signature')
        f.seek(-6, 2); start, marker, comment = struct.unpack('<HHH', f.read(6))
        if marker != 65535 or not 6 < start <= comment or comment + 22 > size: fail('Invalid whole-file signature footer')
        f.seek(size - comment - 22); eocd = f.read(comment + 22)
    if eocd[:4] != b'PK\x05\x06' or b'PK\x05\x06' in eocd[4:] or struct.unpack_from('<H', eocd, 20)[0] != comment:
        fail('Ambiguous ZIP signing boundary')
    return eocd[-start:-6], size - comment - 2


def verify_signature(archive, scratch, cert, name):
    signature, length = signature_footer(archive)
    der = scratch / (name + '.signature.der'); der.write_bytes(signature)
    command = ['openssl', 'cms', '-verify', '-binary', '-inform', 'DER', '-in', str(der), '-content', '/dev/stdin',
               '-CAfile', str(cert), '-purpose', 'any', '-out', '/dev/null']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        with archive.open('rb') as src:
            remaining = length
            while remaining:
                data = src.read(min(8 * 2**20, remaining))
                if not data: fail('Truncated signed content')
                process.stdin.write(data); remaining -= len(data)
        process.stdin.close()
        error = process.stderr.read(4096); code = process.wait(timeout=60)
        if code: fail('Whole-file signature verification rejected: ' + error.decode(errors='replace'))
    finally:
        if process.poll() is None: process.kill(); process.wait()
    return {'verified': True, 'signed_bytes': length, 'certificate_sha256': sha(cert),
            'method': 'OpenSSL CMS, exact Android recovery detached-signature boundary; trusted pinned public AOSP certificate'}


def avb_validate(scratch, base_top, new_top, avb_path):
    spec = importlib.util.spec_from_file_location('pinned_avbtool', avb_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    parser = module.Avb()
    def parsed(path):
        image = module.ImageHandler(str(path), read_only=True)
        try:
            footer, header, descriptors, _ = parser._parse_image(image)
            image.seek(footer.vbmeta_offset if footer else 0)
            blob = image.read(header.SIZE + header.authentication_data_block_size + header.auxiliary_data_block_size)
            offset = header.SIZE + header.authentication_data_block_size + header.public_key_offset
            return header, descriptors, blob, blob[offset:offset + header.public_key_size]
        finally: image._image.close()
    old_header, old_descriptors, _, old_key = parsed(base_top)
    header, descriptors, blob, key = parsed(new_top)
    nonboot = lambda ds: [d.encode() for d in ds if not (isinstance(d, module.AvbHashDescriptor) and d.partition_name == 'boot')]
    if nonboot(old_descriptors) != nonboot(descriptors): fail('Non-boot AVB descriptors changed')
    if key != old_key or any(getattr(header, k) != getattr(old_header, k) for k in ['algorithm_type', 'flags', 'rollback_index', 'rollback_index_location']):
        fail('Top AVB key/algorithm/flags/rollback policy changed')
    if module.lookup_algorithm_by_type(header.algorithm_type)[0] != 'SHA256_RSA4096' or not module.verify_vbmeta_signature(header, blob):
        fail('Actual top AVB RSA signature rejected')
    captured = io.StringIO(); fresh_chains, boot_hashes, inherited_dtbo = [], 0, False
    image = module.ImageHandler(str(new_top), read_only=True)
    try:
        with contextlib.redirect_stdout(captured):
            # The boot footer independently verifies its own complete payload.
            parser.verify_image(str(scratch / 'boot.img'), None, None, False, False)
            for desc in descriptors:
                if isinstance(desc, module.AvbChainPartitionDescriptor):
                    if desc.partition_name not in {'vbmeta_system', 'vbmeta_vendor'}: fail('Unexpected AVB child')
                    # Stock verifier checks exact key from top descriptor, child
                    # signature and all four freshly reconstructed hashtrees.
                    parser.verify_image(str(scratch / (desc.partition_name + '.img')), None, None, False, False, desc.public_key)
                    fresh_chains.append(desc.partition_name)
                elif isinstance(desc, module.AvbHashDescriptor) and desc.partition_name == 'dtbo':
                    # No DTBO payload is shipped or written by the pinned base.
                    # Equality to the pinned base descriptor is the honest
                    # inherited check; never claim fresh DTBO verification.
                    inherited_dtbo = True
                else:
                    if not desc.verify(str(scratch), '.img', {}, image, False): fail('Top descriptor verification failed')
                    if isinstance(desc, module.AvbHashDescriptor) and desc.partition_name == 'boot': boot_hashes += 1
        if set(fresh_chains) != {'vbmeta_system', 'vbmeta_vendor'} or boot_hashes != 1 or not inherited_dtbo:
            fail('Expected exact cannon AVB family missing')
    finally: image._image.close()
    return {'top_RSA_signature_fresh': True, 'top_key_algorithm_flags_rollback_unchanged': True,
            'all_non_boot_descriptors_byte_identical': True, 'boot_footer_and_top_hash_fresh': True,
            'fresh_child_signatures_and_four_logical_hashtrees': sorted(fresh_chains),
            'DTBO': 'Inherited exact descriptor from pinned verified base; no raw payload provided/written; NOT freshly read or rehashed',
            'verifier_output': captured.getvalue().replace(str(scratch), '[validation-images]')}


def safe_unlink_created(path, scratch):
    if path.is_symlink() or path.parent.resolve() != scratch.resolve() or not path.is_file():
        fail('Temporary cleanup boundary differs')
    path.unlink()


def package(base, erofs, toolkit_zip, work, policy, java, brotli):
    started = time.monotonic()
    for key, p in [('base_rom', base), ('erofs_inputs', erofs), ('signing_toolkit', toolkit_zip)]: check_file(p, policy['assets'][key])
    if shutil.disk_usage(work).free < 12_000_000_000: fail('Require12GB free before full image/AVB validation')
    scratch = work / 'scratch'; scratch.mkdir(); output = work / 'artifacts'; output.mkdir()
    tools = scratch / 'signing-tools'; tools.mkdir()
    avb_path = HERE / policy['avbtool']['path']
    if sha(avb_path) != policy['avbtool']['sha256']: fail('Pinned AOSP AVB source changed')
    with checked_zip(toolkit_zip) as z:
        manifest = json.loads(z.read('manifest.json'))
        for row in manifest['files']:
            if z.getinfo(row['path']).file_size != row['bytes'] or zip_sha(z, row['path']) != row['sha256']:
                fail('Signing toolkit member mismatch')
        unpack_selected(z, tools, ['signapk.jar', 'libconscrypt_openjdk_jni.so', 'testkey.pk8', 'testkey.x509.pem'])
    cert = tools / 'testkey.x509.pem'
    if sha(cert) != 'a4384ba815b9499a5ce349b4e33c1755278873fe2eac150a068823f526e6dbde': fail('Public AOSP certificate differs')
    if sha(tools / 'testkey.pk8') != '495675d32e89a149d5abe191f4e9c0e218b9068714e9b53a7c91e164a0741a23': fail('Public AOSP test key differs')
    verify_signature(base, scratch, cert, 'base')
    with checked_zip(erofs) as z:
        if set(z.namelist()) != {'boot.img', 'vbmeta.img', 'manifest.json', 'README.md'}: fail('Unexpected EROFS input scope')
        inputs = json.loads(z.read('manifest.json'))
        if (inputs['profile'] != 'rootless-erofs-kernel-only' or inputs['included_user_data_google_apps_root_modules_recovery_or_protected_partitions'] is not False
                or inputs['baseline_rom_zip_sha256'] != policy['assets']['base_rom']['sha256']
                or inputs['kernel_public_revision'] != policy['source_kernel_revision'] or inputs['kernel_source_tree'] != policy['source_kernel_tree']):
            fail('Rootless source/input proof differs')
        unpack_selected(z, scratch, ['boot.img', 'vbmeta.img'])
        for name, row in inputs['files'].items(): check_file(scratch / name, row)
    with checked_zip(base) as old:
        if old.read('META-INF/com/android/otacert') != cert.read_bytes(): fail('Base Recovery signing certificate differs')
        meta = old.read(META); meta_pb = old.read(META + '.pb')
        fields = dict(l.split('=', 1) for l in meta.decode().splitlines() if '=' in l)
        if (fields.get('ota-type') != 'BLOCK' or fields.get('post-sdk-level') != '37'
                or fields.get('pre-device') != 'cannon,cannong' or fields.get('post-security-patch-level') != '2026-10-01'
                or any('property-files' in k for k in fields) or fields.get('ota-wipe') == 'yes'):
            fail('Fixed manual-Recovery Android17 metadata differs')
        release = json.loads(old.read(RELEASE)); images = release['images']
        new_pair = {name: (scratch / (name + '.img')).read_bytes() for name in ('boot', 'vbmeta')}
        old_pair = {name: old.read(name + '.img') for name in ('boot', 'vbmeta')}
        before, after = parse_boot(old_pair['boot']), parse_boot(new_pair['boot'])
        if before[0] != after[0] or before[2:] != after[2:]: fail('Boot ramdisk/DTB/header changed outside kernel/image ID')
        if hashlib.sha256(after[1]).hexdigest() != inputs['kernel_image_sha256']: fail('Boot kernel does not match supplied source proof')
        if hashlib.sha256(after[2]).hexdigest() != inputs['ramdisk_sha256'] or hashlib.sha256(after[3]).hexdigest() != inputs['dtb_sha256']:
            fail('Actual source ramdisk/DTB hashes differ')
        operations = [l for l in old.read('dynamic_partitions_op_list').decode().splitlines() if l and not l.startswith('#')]
        if operations != ['resize ' + n + ' ' + str(s) for n, s in LOGICAL.items()]: fail('Unexpected dynamic OS operations')
        raw_images = []
        for name, size in LOGICAL.items():
            print('Reconstruct/validate ' + name, flush=True)
            target = scratch / (name + '.img'); h = reconstruct(old, name, size, target, brotli)
            if h != images[name]['sha256']: fail('Base logical image hash differs: ' + name)
            raw_images.append(target)
        for name in ('vbmeta_system', 'vbmeta_vendor'):
            unpack_selected(old, scratch, [name + '.img']); check_file(scratch / (name + '.img'), images[name])
        # DTBO is deliberately read-gated, not written or packaged by this OTA.
        # Its AVB hash descriptor is validated cryptographically below against
        # the inherited pinned descriptor, without claiming a new DTBO payload.
        base_top = scratch / 'base-vbmeta.img'; base_top.write_bytes(old_pair['vbmeta'])
        full_avb = avb_validate(scratch, base_top, scratch / 'vbmeta.img', avb_path)
        for p in raw_images: safe_unlink_created(p, scratch)
        new_script = replace_assertions(old.read(SCRIPT), old_pair, new_pair)
        for name in ('boot', 'vbmeta'): images[name] = {'bytes': len(new_pair[name]), 'sha256': hashlib.sha256(new_pair[name]).hexdigest(), 'written': True}
        kernel_source = {'repository': inputs['kernel_repository'], 'revision': inputs['kernel_public_revision'], 'tree': inputs['kernel_source_tree'], 'compiled_revision': inputs['kernel_development_revision']}
        release['kernel_source'] = kernel_source
        release['qualification'] = 'Experimental unrooted EROFS cached-image package; exact new full ZIP is physically untested. Vanilla OS payloads unchanged; no personal applications/modules or userdata formatting.'
        replacements = {'boot.img': new_pair['boot'], 'vbmeta.img': new_pair['vbmeta'], SCRIPT: new_script, RELEASE: (json.dumps(release, indent=2) + '\n').encode()}
        unsigned = scratch / 'unsigned.zip'
        with zipfile.ZipFile(unsigned, 'x') as z:
            for original in old.infolist():
                if original.filename in SKIPPED_SIGNATURES: continue
                info = copy.copy(original)
                if info.filename in replacements: z.writestr(info, replacements[info.filename]); continue
                with old.open(original) as src, z.open(info, 'w') as dst: shutil.copyfileobj(src, dst, 8 * 2**20)
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        signed = output / ('lineage-24.0-' + stamp + '-UNOFFICIAL-cannong-EROFS-CI-UNTESTED.zip')
        subprocess.run([java, '-Xmx2g', '-Djava.library.path=' + str(tools), '-jar', str(tools / 'signapk.jar'), '-w', str(cert), str(tools / 'testkey.pk8'), str(unsigned), str(signed)], check=True)
        signature = verify_signature(signed, scratch, cert, 'output')
        unchanged = {}
        with checked_zip(signed) as final:
            if set(final.namelist()) != (set(old.namelist()) - SKIPPED_SIGNATURES): fail('Final installer entry scope changed')
            if final.testzip() is not None: fail('Final ZIP CRC rejected')
            for name in old.namelist():
                if name in SKIPPED_SIGNATURES: continue
                if name in replacements:
                    if final.read(name) != replacements[name]: fail('Signed replacement bytes differ')
                else:
                    h = zip_sha(old, name)
                    if zip_sha(final, name) != h: fail('Unchanged OS/metadata entry differs: ' + name)
                    unchanged[name] = h
            if final.read(META) != meta or final.read(META + '.pb') != meta_pb: fail('Final text/protobuf metadata changed')
    check_file(base, policy['assets']['base_rom'])
    h = sha(signed)
    (output / (signed.name + '.sha256')).write_text(h + '  ' + signed.name + '\n')
    report = {'status': 'HOST_VALIDATED_FULL_EROFS_OTA_PHYSICAL_INSTALL_UNTESTED', 'sha256': h, 'bytes': signed.stat().st_size,
        'input_sha256': {k: v['sha256'] for k, v in policy['assets'].items()}, 'source_kernel': kernel_source,
        'whole_file_signature': signature, 'fresh_AVB_validation': full_avb, 'fresh_logical_images': LOGICAL,
        'unchanged_entry_sha256': unchanged, 'metadata_text_sha256': hashlib.sha256(meta).hexdigest(), 'metadata_proto_sha256': hashlib.sha256(meta_pb).hexdigest(),
        'changed_entries': sorted(replacements), 'duration_seconds': round(time.monotonic() - started, 2),
        'source_compilation_performed': False, 'Magisk_GApps_or_userdata_included': False, 'physical_install_tested': False,
        'qualification': 'Reuses pinned compiled unrooted EROFS images and verified vanilla full OTA. This is not a new Android/kernel source build. Exact resulting ZIP requires physical installation and acceptance testing.'}
    (output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    safe_unlink_created(unsigned, scratch)
    return signed, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work-dir', type=Path, required=True, help='New disposable directory, never an existing project/output')
    ap.add_argument('--base-rom', type=Path); ap.add_argument('--erofs-inputs', type=Path); ap.add_argument('--toolkit', type=Path)
    ap.add_argument('--java', default='java'); ap.add_argument('--brotli', default='brotli')
    a = ap.parse_args(); policy = json.loads((HERE / 'inputs.json').read_text())
    provided = [a.base_rom, a.erofs_inputs, a.toolkit]
    if any(provided) and not all(provided): fail('Provide all three local inputs, or none to download fixed public assets')
    if a.work_dir.exists(): fail('Use a new disposable work directory; existing data is never cleaned')
    a.work_dir.mkdir(parents=True); work = a.work_dir.resolve()
    if not all(provided):
        if shutil.disk_usage(work).free < 14_000_000_000: fail('Require14GB free before downloading public inputs')
        folder = work / 'downloads'; folder.mkdir()
        provided = [download_base_parts(policy, folder)] + [download(policy['assets'][k], folder) for k in ('erofs_inputs', 'signing_toolkit')]
    signed, report = package(*provided, work, policy, a.java, a.brotli)
    result = {'artifact_dir': str(signed.parent), 'zip_name': signed.name, 'sha256': report['sha256'], 'status': report['status']}
    if os.environ.get('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:
            for k, v in result.items(): f.write(k + '=' + v + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__': main()
