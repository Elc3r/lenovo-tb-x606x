#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Install five hash-pinned local binary inputs; never download or access a device."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile

HERE = Path(__file__).resolve().parents[1]


def allocated_sections(data):
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('Expected ELF64 little endian')
    start = struct.unpack_from('<Q', data, 40)[0]
    stride, count = struct.unpack_from('<HH', data, 58)
    result = []
    for i in range(count):
        header = struct.unpack_from('<IIQQQQIIQQ', data, start + i * stride)
        if header[2] & 2:
            offset, size = header[4:6]
            result.append((header[1], header[2], header[3], size,
                           data[offset:offset + size] if header[1] != 8 else b''))
    return result


def normalize(data, recipe):
    if hashlib.sha256(data).hexdigest() != recipe['input_sha256']:
        raise ValueError('Unsupported normalization input')
    cursor, chunks = 0, []
    for offset, old, new in recipe['edits']:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if offset < cursor or data[offset:offset + len(old)] != old:
            raise ValueError('Normalization preimage differs')
        chunks.extend([data[cursor:offset], new])
        cursor = offset + len(old)
    output = b''.join(chunks) + data[cursor:]
    if allocated_sections(data) != allocated_sections(output):
        raise ValueError('Normalization changed allocated ELF sections')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='prepared LineageOS source root')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--firmware-root', type=Path, help='locally extracted matching firmware, containing vendor/')
    source.add_argument('--private-cache', type=Path, help='local cache with blobs named by blobs.json')
    source.add_argument('--vendor-source', type=Path, help='pinned proprietary_vendor checkout; requires --beanpod')
    parser.add_argument('--beanpod', type=Path, help='locally extracted matching Beanpod service')
    parser.add_argument('--install', action='store_true', help='write verified inputs; default is check only')
    args = parser.parse_args()
    if (args.vendor_source is not None) != (args.beanpod is not None):
        parser.error('--vendor-source and --beanpod must be supplied together')
    root = args.root.resolve(strict=True)
    prepared = []
    recipes = json.loads((HERE / 'blob-normalization.json').read_text())
    for entry in json.loads((HERE / 'blobs.json').read_text()):
        if args.vendor_source:
            source_path = (args.beanpod if entry['name'] == 'keymaster-service' else
                           args.vendor_source / 'proprietary' / entry['firmware_path'])
        else:
            source_path = (args.firmware_root / entry['firmware_path'] if args.firmware_root else args.private_cache / entry['name'])
        data = source_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256'] and entry['name'] in recipes:
            data = normalize(data, recipes[entry['name']])
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Wrong binary input: ' + entry['name'])
        target = root / entry['destination']
        if not target.resolve().is_relative_to(root):
            raise ValueError('Output escapes source root')
        prepared.append((target, data, int(entry['mode'], 8)))
    for target, data, mode in prepared:
        if args.install:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                temporary.write(data)
                name = Path(temporary.name)
            try:
                name.chmod(mode)
                os.replace(name, target)
            finally:
                name.unlink(missing_ok=True)
        print('Installed:' if args.install else 'Verified:', target.relative_to(root))


if __name__ == '__main__':
    main()
