#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only full-OTA checks. No installation, build or device access."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_file(image, path):
    # debugfs is deliberately never invoked with -w.
    result = subprocess.run(['debugfs', '-R', 'cat ' + path, str(image)], check=True, capture_output=True)
    require(bool(result.stdout), 'Missing/empty payload file: ' + path)
    return result.stdout


def reconstruct(archive, directory, partition, size):
    transfer = archive.read(partition + '.transfer.list').decode().splitlines()
    require(len(transfer) >= 4 and transfer[0] == '4' and transfer[2:4] == ['0', '0'], 'Full v4 block OTA required')
    compressed = directory / (partition + '.br')
    with archive.open(partition + '.new.dat.br') as source, compressed.open('wb') as target:
        shutil.copyfileobj(source, target)
    data = directory / (partition + '.dat')
    subprocess.run(['brotli', '-d', '-o', str(data), str(compressed)], check=True)
    image = directory / (partition + '.img')
    with image.open('w+b') as target, data.open('rb') as source:
        target.truncate(size)
        previous = []
        for line in transfer[4:]:
            command, encoded = line.split()
            require(command in {'new', 'zero', 'erase'}, 'Unsupported transfer command')
            ranges = [int(v) for v in encoded.split(',')]
            require(ranges[0] == len(ranges) - 1 and ranges[0] % 2 == 0, 'Malformed ranges')
            for start, end in zip(ranges[1::2], ranges[2::2]):
                require(0 <= start < end <= size // 4096, 'Range outside partition')
                if command != 'new':
                    continue
                require(not any(start < b and a < end for a, b in previous), 'Overlapping new ranges')
                previous.append((start, end))
                target.seek(start * 4096)
                remaining = (end - start) * 4096
                while remaining:
                    chunk = source.read(min(remaining, 1024 * 1024))
                    require(bool(chunk), 'Truncated block data')
                    target.write(chunk)
                    remaining -= len(chunk)
        require(not source.read(1), 'Unused block data')
    return image


def boot_check(data):
    require(data[:8] == b'ANDROID!' and len(data) >= 1632, 'Invalid boot image')
    require(struct.unpack_from('<I', data, 40)[0] <= 2, 'Unsupported boot header')
    command = (data[64:576].split(b'\0')[0] + b' ' + data[608:1632].split(b'\0')[0]).decode()
    args = command.split()
    require([v for v in args if v.startswith('androidboot.selinux=')] == ['androidboot.selinux=enforcing'], 'Boot must select Enforcing')
    require(not {'selinux=0', 'enforcing=0'} & set(args), 'SELinux disabling flag')
    return command.strip()


def properties(text):
    return dict(line.split('=', 1) for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith('#') and '=' in line)


def expected_vendor(common, vendor_root):
    # Migration modules intentionally resolve original blob inputs relative to
    # the Android source root, so the caller runs from that root.
    result = {}
    boot = load(common / 'tools/validate_boot_migrations.py', 'boot_migrations')
    boot.COMMON = common
    boot.VENDOR = vendor_root
    result.update(boot.expected_payloads())
    codec = load(common / 'tools/prepare_codec_log_migration.py', 'codec_migration')
    media = load(common / 'tools/prepare_media_property_migration.py', 'media_migration')
    for libdir, architecture in [('lib', 'arm'), ('lib64', 'arm64')]:
        name = libdir + '/libvcodec_utility.so'
        result[name] = codec.prepare((vendor_root / name).read_bytes())[0]
        name = libdir + '/libMtkOmxCore.so'
        result[name] = media.prepare((vendor_root / name).read_bytes(), 'omx-core', architecture)[0]
    name = 'lib64/libcam.iopipe.so'
    result[name] = media.prepare((vendor_root / name).read_bytes(), 'camera-dump', 'arm64')[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--common', type=Path, help='override common tree for local export validation')
    parser.add_argument('--ota', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    common = (args.common or root / 'device/lenovo/mt6765-common').resolve(strict=True)
    package = args.ota.resolve(strict=True)
    require(not args.report.exists(), 'Report already exists')
    import os
    os.chdir(root)
    vendor_root = root / 'vendor/lenovo/mt6765-common/proprietary/vendor'
    expected = expected_vendor(common, vendor_root)
    km = load(common / 'tools/validate_keymaster.py', 'keymaster')
    ecm = load(common / 'tools/validate_ecm_export.py', 'ecm_export')
    identities = {}
    def record(name, content):
        identities[name] = hashlib.sha256(content).hexdigest()
    with tempfile.TemporaryDirectory(prefix='lenovo-ota-') as temporary, zipfile.ZipFile(package) as archive:
        directory = Path(temporary)
        require(archive.testzip() is None, 'ZIP CRC failure')
        assertion = archive.read('META-INF/com/google/android/updater-script').decode()
        require('getprop("ro.product.device") == "achilles6_row_data"' in assertion, 'Wrong OTA device assertion')
        boot = archive.read('boot.img')
        command = boot_check(boot)
        record('boot.img', boot)
        vendor = reconstruct(archive, directory, 'vendor', 838860800)
        system = reconstruct(archive, directory, 'system', 4085252096)
        def sysread(relative):
            # System-as-root layout used by this product.
            return read_file(system, '/system/' + relative)
        for relative, content in expected.items():
            actual = read_file(vendor, '/' + relative)
            require(actual == content, 'Wrong migrated payload: ' + relative)
            record('vendor/' + relative, actual)
        service = read_file(vendor, '/bin/hw/' + km.SERVICE)
        km.check_service(service)
        record('vendor/bin/hw/' + km.SERVICE, service)
        require(read_file(vendor, '/etc/init/' + km.SERVICE + '.rc') == (common / 'keymaster' / (km.SERVICE + '.rc')).read_bytes(), 'Wrong Keymaster rc')
        defaults = load(Path(__file__).with_name('verify_policy.py'), 'policy_checks')
        policy = read_file(vendor, '/etc/selinux/precompiled_sepolicy')
        contexts = [sysread('etc/selinux/plat_property_contexts'),
                    sysread('system_ext/etc/selinux/system_ext_property_contexts'),
                    read_file(vendor, '/etc/selinux/vendor_property_contexts')]
        vprops = read_file(vendor, '/build.prop').decode()
        sprops = sysread('build.prop').decode()
        file_contexts = b'\n'.join([sysread('etc/selinux/plat_file_contexts'),
                                     sysread('system_ext/etc/selinux/system_ext_file_contexts'),
                                     read_file(vendor, '/etc/selinux/vendor_file_contexts')])
        policy_result = defaults.verify(root, directory, policy, contexts, vprops, sprops, file_contexts)
        runtime = directory / 'runtime.apex'
        runtime.write_bytes(sysread('apex/com.android.runtime.apex'))
        runtime_image = directory / 'runtime.img'
        with zipfile.ZipFile(runtime) as apex, apex.open('apex_payload.img') as source, runtime_image.open('wb') as target:
            shutil.copyfileobj(source, target)
        ecm_result = ecm.verify_runtime(lambda name: read_file(runtime_image, '/' + name), lambda: sysread('bin/init'), directory)
        for relative in ['etc/selinux/vendor_property_contexts', 'etc/selinux/precompiled_sepolicy']:
            record('vendor/' + relative, read_file(vendor, '/' + relative))
    result = {'ota_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
              'boot_cmdline': command, 'verified_payload_sha256': identities,
              'policy': policy_result, 'ecm': ecm_result, 'device_tested': False,
              'scope': 'full block OTA, selected migrations, Beanpod, ECM private symbols/gates, boot flags, vendor default publication and selected MAC boundaries; not the historical 268-check suite'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as report:
        json.dump(result, report, indent=2)
        report.write('\n')
    print('Portable OTA checks passed; report:', args.report)


if __name__ == '__main__':
    main()
