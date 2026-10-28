#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Selected effective media-policy gates, independent of private audit tools."""
from functools import lru_cache
import re

CODEC_COMMANDS = {0x4d0b, 0x4d0d, 0x4d15, 0x4d16, 0x4d17, 0x4d18,
                  0x4d27, 0x4d28, 0x4d31, 0x4d33, 0x4d37}
GE_COMMANDS = {0x6764, 0x6765, 0x6766, 0x6769}
APPS = {'untrusted_app', 'untrusted_app_25', 'untrusted_app_27', 'untrusted_app_29'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(text, allowed, file_contexts, hwservice_contexts):
    attrs = {name: set() for name in re.findall(r'^\(typeattribute (\S+)\)$', text, re.M)}
    for name, body in re.findall(r'^\(typeattributeset (\S+) (.*)\)$', text, re.M):
        require(re.fullmatch(r'\([^()]*\)', body), 'Unsupported media attribute expression')
        attrs[name] = set(body[1:-1].split())
    @lru_cache(None)
    def members(name):
        return frozenset().union(*(members(n) for n in attrs[name])) if name in attrs else frozenset([name])
    expected = {
        ('mediacodec', 'vendor_vcodec_device', 'chr_file'): CODEC_COMMANDS,
        ('mediacodec', 'vendor_proc_ged', 'file'): GE_COMMANDS | {0x670e},
        ('vendor_mms', 'vendor_proc_ged', 'file'): GE_COMMANDS,
    }
    for app in APPS:
        expected[(app, 'vendor_proc_ged', 'file')] = GE_COMMANDS | {0x6700, 0x6703, 0x6704, 0x6705, 0x6709, 0x670d}
    actual = {key: set() for key in expected}
    owners = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('(allow '):
            m = re.fullmatch(r'\(allow (\S+) (\S+) \((\S+) \(([^()]*)\)\)\)', line)
            require(m is not None, 'Unsupported media allow expression')
            if m[3] == 'hwservice_manager' and 'add' in m[4].split() and 'vendor_mms_hwservice' in members(m[2]):
                owners.update(members(m[1]))
        if not line.startswith('(allowx '):
            continue
        m = re.fullmatch(r'\(allowx (\S+) (\S+) \(ioctl (\S+) (.*)\)\)', line)
        require(m is not None, 'Unsupported media ioctl expression')
        keys = [key for key in expected if key[0] in members(m[1]) and
                key[1] in members(m[2]) and key[2] == m[3]]
        if not keys:
            continue
        values = set()
        payload = m[4]
        for a, b in re.findall(r'\(range (0x[0-9a-f]+) (0x[0-9a-f]+)\)', payload):
            values.update(range(int(a, 16), int(b, 16) + 1))
        payload = re.sub(r'\(range 0x[0-9a-f]+ 0x[0-9a-f]+\)', '', payload)
        values.update(int(v, 16) for v in re.findall(r'0x[0-9a-f]+', payload))
        require(not re.sub(r'0x[0-9a-f]+|[()\s]', '', payload), 'Unsupported media ioctl values')
        for key in keys:
            actual[key].update(values)
    for key, wanted in expected.items():
        family = 0x4d if key[1] == 'vendor_vcodec_device' else 0x67
        require({n for n in actual[key] if n >> 8 == family} == wanted, 'Wrong codec/GE commands: ' + repr(key))
        require(allowed(*key, 'ioctl'), 'Missing media ioctl base permission: ' + repr(key))
    codec = 'vendor_vcodec_device'
    for permission in ('getattr', 'open', 'read', 'write', 'map', 'ioctl'):
        require(allowed('mediacodec', codec, 'chr_file', permission), 'Missing codec FD permission')
    for permission in ('create', 'unlink', 'execute', 'setattr'):
        require(not allowed('mediacodec', codec, 'chr_file', permission), 'Unexpected codec lifecycle permission')
    for app in APPS | {'isolated_app'}:
        for target in (codec, 'vendor_sw_sync_device'):
            for permission in ('open', 'read', 'write', 'map', 'ioctl'):
                require(not allowed(app, target, 'chr_file', permission), 'App raw media device access')
        require(not allowed(app, 'default_android_hwservice', 'hwservice_manager', 'find'), 'Generic app HAL discovery')
    for app in APPS:
        require(allowed(app, 'vendor_mms_hwservice', 'hwservice_manager', 'find'), 'Missing MMS client discovery')
        require(allowed(app, 'vendor_mms', 'binder', 'call') and allowed('vendor_mms', app, 'binder', 'call'), 'Missing MMS IPC contract')
    require(not allowed('isolated_app', 'vendor_mms_hwservice', 'hwservice_manager', 'find'), 'Isolated-app MMS discovery')
    require(owners == {'vendor_mms'}, 'Wrong MMS registration owner')
    require(allowed('init', 'vendor_mms', 'process', 'transition'), 'Missing MMS transition')
    require(allowed('vendor_mms', 'vendor_mms_exec', 'file', 'entrypoint'), 'Missing MMS entrypoint')
    for permission in ('getattr', 'open', 'read', 'ioctl'):
        require(allowed('vendor_mms', 'vendor_proc_ged', 'file', permission), 'Missing MMS GE FD access')
    for target in ('vendor_display_pipeline_prop', 'vendor_media_color_mode_prop'):
        for permission in ('getattr', 'open', 'read', 'map'):
            require(allowed('vendor_mms', target, 'file', permission), 'Missing MMS DP property read')
        require(not allowed('vendor_mms', target, 'property_service', 'set'), 'MMS property write')
    require(not allowed('mediacodec', 'default_prop', 'file', 'read'), 'Generic codec property access')
    rows = [line.split() for line in file_contexts.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    for path, target in [('/dev/Vcodec', codec), ('/dev/sw_sync', 'vendor_sw_sync_device')]:
        require([row for row in rows if 'u:object_r:' + target + ':s0' in row] ==
                [[path, '-c', 'u:object_r:' + target + ':s0']], 'Wrong media node context')
    services = [line.split() for line in hwservice_contexts.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    require([row for row in services if 'u:object_r:vendor_mms_hwservice:s0' in row] ==
            [['vendor.mediatek.hardware.mms::IMms', 'u:object_r:vendor_mms_hwservice:s0']], 'Wrong MMS interface context')
    return {'codec_and_ge_commands': True, 'mms_owner_and_app_boundaries': True,
            'hevc_cpu_count_query': True, 'runtime_verified_by_this_check': False}
