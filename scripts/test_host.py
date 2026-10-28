#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline tests; optional --root enables pinned vendor-input migration tests."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
SOURCE_ROOT = None
COMMON = None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ota = load(HERE / 'scripts/verify_ota.py', 'ota')
policy = load(HERE / 'scripts/verify_policy.py', 'policy')
blobs = load(HERE / 'scripts/prepare_blobs.py', 'blobs')


class PortableTests(unittest.TestCase):
    def test_boot_flags(self):
        data = bytearray(1660)
        data[:8] = b'ANDROID!'
        struct.pack_into('<I', data, 40, 2)
        text = b'androidboot.selinux=enforcing'
        data[64:64 + len(text)] = text
        self.assertIn('enforcing', ota.boot_check(bytes(data)))
        for text in [b'androidboot.selinux=permissive', b'androidboot.selinux=enforcing selinux=0',
                     b'androidboot.selinux=enforcing androidboot.selinux=permissive']:
            data[64:576] = text.ljust(512, b'\0')
            with self.assertRaises(ValueError):
                ota.boot_check(bytes(data))

    def test_property_parser(self):
        self.assertEqual(policy.props('# comment\na=1\na=2\nb=x=y\n'), {'a': '2', 'b': 'x=y'})

    def test_attribute_access_and_absence(self):
        text = '(typeattribute readers)\n(typeattributeset readers (camera codec))\n(allow readers target (file (read open)))\n'
        allowed = policy.policy_access(text)
        self.assertTrue(allowed('camera', 'target', 'file', 'read'))
        self.assertFalse(allowed('app', 'target', 'file', 'read'))
        self.assertFalse(allowed('camera', 'target', 'file', 'write'))
        with self.assertRaises(ValueError):
            policy.policy_access('(typeattribute readers)\n(typeattributeset readers (and (a) (b)))\n')

    def test_patch_hashes(self):
        for entry in json.loads((HERE / 'patches/series.json').read_text()):
            self.assertEqual(hashlib.sha256((HERE / entry['patch']).read_bytes()).hexdigest(), entry['sha256'])

    def test_manifest_renderer(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'overlay.xml'
            command = ['python3', str(HERE / 'scripts/render_manifest.py'), '--owner', 'example-owner',
                       '--tree', 'lineage', '--output', str(target)]
            subprocess.run(command, check=True, capture_output=True)
            self.assertIn('android_device_lenovo_mt6765-common', target.read_text())
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_four_metadata_normalizations(self):
        if SOURCE_ROOT is None:
            self.skipTest('requires --root for local pinned vendor inputs')
        recipes = json.loads((HERE / 'blob-normalization.json').read_text())
        entries = json.loads((HERE / 'blobs.json').read_text())
        for entry in entries:
            if entry['name'] not in recipes:
                continue
            relative = entry['destination'].split('vendor/lenovo/mt6765-common/')[1]
            original = subprocess.check_output(['git', '-C', str(SOURCE_ROOT / 'vendor/lenovo/mt6765-common'), 'show', 'HEAD:' + relative])
            result = blobs.normalize(original, recipes[entry['name']])
            self.assertEqual(hashlib.sha256(result).hexdigest(), entry['sha256'])
            damaged = b'!' + original[1:]
            with self.assertRaises(ValueError):
                blobs.normalize(damaged, recipes[entry['name']])

    def test_blob_install_preflight_and_exact_outputs(self):
        if SOURCE_ROOT is None:
            self.skipTest('requires --root for local pinned inputs')
        entries = json.loads((HERE / 'blobs.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'target'
            cache = Path(temporary) / 'cache'
            root.mkdir()
            cache.mkdir()
            for entry in entries:
                (cache / entry['name']).write_bytes((SOURCE_ROOT / entry['destination']).read_bytes())
            bad = cache / entries[-1]['name']
            good = bad.read_bytes()
            bad.write_bytes(b'corrupted')
            command = ['python3', str(HERE / 'scripts/prepare_blobs.py'), '--root', str(root),
                       '--private-cache', str(cache), '--install']
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertFalse(list(root.iterdir()))
            bad.write_bytes(good)
            subprocess.run(command, check=True, capture_output=True)
            for entry in entries:
                output = root / entry['destination']
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), entry['sha256'])
                self.assertEqual(output.stat().st_mode & 0o777, int(entry['mode'], 8))

    def test_actual_migrations_and_unknown_revision_rejection(self):
        if SOURCE_ROOT is None:
            self.skipTest('requires --root for local pinned vendor inputs')
        vendor = SOURCE_ROOT / 'vendor/lenovo/mt6765-common/proprietary/vendor'
        migrated = ota.expected_vendor(COMMON, vendor)
        self.assertEqual(len(migrated), 12)
        for path, data in migrated.items():
            self.assertEqual(data, (SOURCE_ROOT / 'out/target/product/achilles6_row_data/vendor' / path).read_bytes())
        for relative in ['graphics-storage/migrate.py', 'camera-storage/migrate.py', 'ecm-consumer/migrate.py']:
            module = load(COMMON / relative, relative.replace('/', '_'))
            with self.assertRaises(ValueError):
                module.migrate(b'unsupported input')

    def test_sim_regular_file_label_scope(self):
        if SOURCE_ROOT is None:
            self.skipTest('requires --root with the built product and host libraries')
        product = SOURCE_ROOT / 'out/target/product/achilles6_row_data'
        contexts = b'\n'.join(path.read_bytes() for path in [
            product / 'system/etc/selinux/plat_file_contexts',
            product / 'system/system_ext/etc/selinux/system_ext_file_contexts',
            product / 'vendor/etc/selinux/vendor_file_contexts'])
        with tempfile.TemporaryDirectory() as temporary:
            policy.verify_sim_paths(SOURCE_ROOT, Path(temporary), contexts)
            bad, count = re.subn(rb'(/mnt/vendor/protect_\[fs\]/md/NA77_005)\s+--\s+', rb'\1 ', contexts)
            self.assertEqual(count, 1)
            with self.assertRaises(ValueError):
                policy.verify_sim_paths(SOURCE_ROOT, Path(temporary), bad)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--common', type=Path)
    args, remainder = parser.parse_known_args()
    SOURCE_ROOT = args.root.resolve() if args.root else None
    COMMON = args.common.resolve() if args.common else (SOURCE_ROOT / 'device/lenovo/mt6765-common' if SOURCE_ROOT else None)
    unittest.main(argv=['test_host.py', *remainder])
