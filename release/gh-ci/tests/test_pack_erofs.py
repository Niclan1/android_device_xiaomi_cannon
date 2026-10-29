# SPDX-License-Identifier: Apache-2.0
import hashlib
import copy
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import warnings
import zipfile

spec = importlib.util.spec_from_file_location('pack_erofs', Path(__file__).resolve().parents[1] / 'pack_erofs.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class GuardTests(unittest.TestCase):
    def test_zip_paths_and_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'test.zip'
            for names in [['../outside'], ['/absolute'], ['dir\\outside'], ['same', 'same']]:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    with zipfile.ZipFile(path, 'w') as z:
                        for name in names: z.writestr(name, b'x')
                with self.assertRaises(RuntimeError): m.checked_zip(path)

    def test_only_exact_contiguous_full_transfer_is_accepted(self):
        m.parse_transfer(b'4\n2\n0\n0\nnew 2,0,2\n', 8192)
        for value in [b'4\n2\n0\n0\nzero 2,0,2\n', b'4\n3\n0\n0\nnew 2,0,3\n', b'4\n2\n0\n0\nnew 2,0,1\nnew 2,1,2\n']:
            with self.assertRaises(RuntimeError): m.parse_transfer(value, 8192)

    def test_edify_changes_only_paired_hashes_and_notice(self):
        old = {'boot': b'a' * 4096, 'vbmeta': b'b' * 4096}
        new = {'boot': b'c' * 4096, 'vbmeta': b'd' * 4096}
        text = '\n'.join('assert(range_sha1("/dev/block/by-name/' + n + '", "2,0,1") == "' + hashlib.sha1(old[n]).hexdigest() + '");' for n in old) + '\n'
        changed = m.replace_assertions(text.encode(), old, new).decode()
        self.assertIn(hashlib.sha1(new['boot']).hexdigest(), changed)
        self.assertIn(hashlib.sha1(new['vbmeta']).hexdigest(), changed)
        self.assertNotIn(hashlib.sha1(old['boot']).hexdigest(), changed)
        self.assertTrue(changed.startswith('ui_print('))
        for forbidden in ['format(', 'delete(', 'run_program(', 'mount(', 'recovery.img', '/data/']:
            self.assertNotIn(forbidden, changed)
        with self.assertRaises(RuntimeError): m.replace_assertions((text + text).encode(), old, new)
        with self.assertRaises(RuntimeError): m.replace_assertions(b'no hashes', old, new)

    def test_temp_cleanup_refuses_outside_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); scratch = root / 'scratch'; scratch.mkdir()
            outside = root / 'input.zip'; outside.write_bytes(b'preserve')
            with self.assertRaises(RuntimeError): m.safe_unlink_created(outside, scratch)
            link = scratch / 'link'; link.symlink_to(outside)
            with self.assertRaises(RuntimeError): m.safe_unlink_created(link, scratch)
            own = scratch / 'own.img'; own.write_bytes(b'temporary'); m.safe_unlink_created(own, scratch)
            self.assertFalse(own.exists()); self.assertEqual(outside.read_bytes(), b'preserve')

    def test_size_and_full_hash_input_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'input'; p.write_bytes(b'abc')
            m.check_file(p, {'bytes': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()})
            with self.assertRaises(RuntimeError): m.check_file(p, {'bytes': 3, 'sha256': '0' * 64})
            with self.assertRaises(RuntimeError): m.check_file(p, {'bytes': 4, 'sha256': hashlib.sha256(b'abc').hexdigest()})

    def test_chunk_join_full_hash_order_and_manifest_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); paths = []; rows = []
            for i, data in enumerate([b'one', b'two', b'three', b'four', b'five']):
                p = root / ('part' + str(i)); p.write_bytes(data); paths.append(p)
                rows.append({'name': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            expected = {'filename': 'base.zip', 'bytes': 19, 'sha256': hashlib.sha256(b'onetwothreefourfive').hexdigest()}
            source = {'name': expected['filename'], 'bytes': expected['bytes'], 'sha256': expected['sha256']}
            manifest = {'format': 1, 'source': source, 'max_part_bytes': 67108864, 'parts': rows}
            self.assertEqual(m.join_base_parts(manifest, expected, paths, root / 'good').read_bytes(), b'onetwothreefourfive')
            with self.assertRaises(RuntimeError): m.join_base_parts(manifest, expected, paths[::-1], root / 'wrong-order')
            bad = copy.deepcopy(manifest); bad['source']['sha256'] = '0' * 64
            with self.assertRaises(RuntimeError): m.join_base_parts(bad, expected, paths, root / 'wrong-base')
            bad = copy.deepcopy(manifest); bad['parts'][4] = bad['parts'][0]
            with self.assertRaises(RuntimeError): m.join_base_parts(bad, expected, paths, root / 'duplicate')
            bad = copy.deepcopy(expected); bad['sha256'] = '0' * 64
            with self.assertRaises(RuntimeError): m.join_base_parts({'format': 1, 'source': {**source, 'sha256': bad['sha256']}, 'max_part_bytes': 67108864, 'parts': rows}, bad, paths, root / 'wrong-full-hash')
            paths[0].write_bytes(b'bad')
            with self.assertRaises(RuntimeError): m.join_base_parts(manifest, expected, paths, root / 'corrupt-part')

    def test_download_rejects_untrusted_names_and_urls_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            good = {'filename': 'part', 'bytes': 1, 'sha256': '0' * 64, 'url': 'https://github.com/owner/repo/releases/download/tag/part'}
            for field, value in [('filename', '../outside'), ('filename', '/outside'), ('filename', 'part\\outside'), ('url', 'http://github.com/part'), ('url', 'https://other.example/part'), ('bytes', 0), ('sha256', 'bad')]:
                bad = {**good, field: value}
                with self.assertRaises(RuntimeError): m.download(bad, Path(d))

    def test_release_stays_draft_until_exact_server_hashes_verified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name, data in [('candidate.zip', b'zip'), ('candidate.zip.sha256', b'sidecar'), ('validation.json', b'{}')]:
                (root / name).write_bytes(data)
            rows = [{'name': p.name, 'state': 'uploaded', 'size': p.stat().st_size, 'digest': 'sha256:' + m.sha(p)} for p in root.iterdir()]
            release = {'draft': True, 'prerelease': True, 'assets': rows}
            m.verify_uploaded_assets(root, release)
            for field, value in [('digest', 'sha256:' + '0' * 64), ('size', 0), ('state', 'starter')]:
                bad = copy.deepcopy(release); bad['assets'][0][field] = value
                with self.assertRaises(RuntimeError): m.verify_uploaded_assets(root, bad)
            for field in ['draft', 'prerelease']:
                with self.assertRaises(RuntimeError): m.verify_uploaded_assets(root, {**release, field: False})
            with self.assertRaises(RuntimeError): m.verify_uploaded_assets(root, {**release, 'assets': rows + [rows[0]]})
            (root / 'unexpected').write_bytes(b'preserve')
            with self.assertRaises(RuntimeError): m.verify_uploaded_assets(root, release)

    def test_signature_boundary_rejects_unsigned_and_fake_footer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'input.zip'
            for data in [b'bad', b'x' * 30, b'PK\x05\x06' + bytes(18) + struct.pack('<HHH', 7, 65535, 7)]:
                p.write_bytes(data)
                with self.assertRaises(RuntimeError): m.signature_footer(p)

    def test_boot_v2_bounds_and_non_kernel_payload(self):
        data = bytearray(67108864); data[:8] = b'ANDROID!'
        for offset, value in [(8, 4), (16, 4), (36, 2048), (40, 2), (1644, 1660), (1648, 4)]: struct.pack_into('<I', data, offset, value)
        data[2048:2052] = b'kern'; data[4096:4100] = b'cpio'; data[6144:6148] = b'dtb!'
        header, kernel, ramdisk, dtb = m.parse_boot(data)
        self.assertEqual((kernel, ramdisk, dtb), (b'kern', b'cpio', b'dtb!'))
        self.assertEqual(header[8:12], bytes(4))
        struct.pack_into('<I', data, 24, 1)
        with self.assertRaises(RuntimeError): m.parse_boot(data)


if __name__ == '__main__': unittest.main()
