#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Selected portable compiled-policy checks; not the historical mutation suite."""
from functools import lru_cache
import ctypes as c
from pathlib import Path
import re
import stat
import subprocess

PLATFORM_DEFAULTS = {
    'ro.config.notification_vol_steps': '25', 'ro.config.ring_vol_steps': '25',
    'fmradio.driver.enable': '0', 'lockscreen.rot_override': 'true',
    'persist.meta.dumpdata': '0', 'ro.have_aacencode_feature': '1',
    'ro.telephony.sim.count': '2', 'persist.radio.default.sim': '0',
    'persist.radio.mobile.data': '0,0', 'ro.sf.hwrotation': '0',
    'persist.sys.usb.config': 'adb',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def props(text):
    return dict(line.split('=', 1) for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith('#') and '=' in line)


def policy_access(text):
    attrs = {name: set() for name in re.findall(r'^\(typeattribute (\S+)\)$', text, re.M)}
    for name, body in re.findall(r'^\(typeattributeset (\S+) (.*)\)$', text, re.M):
        require(re.fullmatch(r'\([^()]*\)', body), 'Unsupported attribute expression')
        attrs[name] = set(body[1:-1].split())
    @lru_cache(None)
    def members(name):
        if name not in attrs:
            return frozenset([name])
        return frozenset().union(*(members(child) for child in attrs[name]))
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('(allow '):
            continue
        match = re.fullmatch(r'\(allow (\S+) (\S+) \((\S+) \(([^()]*)\)\)\)', line)
        require(match is not None, 'Unsupported allow syntax')
        source, target, kind, permissions = match.groups()
        rules.append((source, target, kind, set(permissions.split())))
    def allowed(source, target, kind, permission):
        return any(k == kind and permission in permissions and source in members(s)
                   and (target == source if t == 'self' else target in members(t))
                   for s, t, k, permissions in rules)
    return allowed


def lookup(root, directory, texts, names):
    base = root / 'out/soong/.intermediates/system/core/property_service'
    libraries = [base / 'libpropertyinfoserializer/libpropertyinfoserializer/linux_glibc_x86_64_static/libpropertyinfoserializer.a',
                 base / 'libpropertyinfoparser/libpropertyinfoparser/linux_glibc_x86_64_static/libpropertyinfoparser.a']
    binary = directory / 'property-lookup'
    command = [str(root / 'prebuilts/clang/host/linux-x86/clang-r416183b/bin/clang++'),
               '-stdlib=libc++', '-std=c++17', str(Path(__file__).with_name('property_lookup.cpp')),
               '-Isystem/core/property_service/libpropertyinfoserializer/include',
               '-Isystem/core/property_service/libpropertyinfoparser/include',
               *map(str, libraries), '-Lout/host/linux-x86/lib64',
               '-Wl,-rpath,' + str(root / 'out/host/linux-x86/lib64'), '-lbase', '-o', str(binary)]
    subprocess.run(command, check=True, capture_output=True, cwd=root)
    contexts = []
    for i, text in enumerate(texts):
        path = directory / f'property-contexts-{i}'
        path.write_bytes(text)
        contexts.append(str(path))
    output = subprocess.check_output([str(binary), *contexts], input='\n'.join(names) + '\n', text=True)
    result = {}
    for line in output.splitlines():
        name, context, kind = line.split('\t')
        result[name] = context.split(':')[2]
    require(set(result) == set(names), 'Incomplete property lookup')
    return result


def verify_sim_paths(root, directory, contexts):
    path = directory / 'sim-file-contexts'
    path.write_bytes(contexts)
    lib = c.CDLL(str(root / 'out/host/linux-x86/lib64/libselinux.so'), use_errno=True)
    class Opt(c.Structure):
        _fields_ = [('type', c.c_int), ('value', c.c_char_p)]
    lib.selabel_open.argtypes = [c.c_uint, c.POINTER(Opt), c.c_uint]
    lib.selabel_open.restype = c.c_void_p
    lib.selabel_lookup_raw.argtypes = [c.c_void_p, c.POINTER(c.c_char_p), c.c_char_p, c.c_int]
    lib.freecon.argtypes = [c.c_char_p]
    lib.selabel_close.argtypes = [c.c_void_p]
    handle = lib.selabel_open(0, (Opt * 1)(Opt(3, str(path).encode())), 1)
    require(bool(handle), 'Cannot open packaged file contexts')
    try:
        for mount in ('protect_f', 'protect_s'):
            name = '/mnt/vendor/' + mount + '/md/NA77_005'
            for probe, mode, expected in [(name, stat.S_IFREG, True), (name, stat.S_IFDIR, False),
                                          (name + '.backup', stat.S_IFREG, False)]:
                value = c.c_char_p()
                require(lib.selabel_lookup_raw(handle, c.byref(value), probe.encode(), mode) == 0, 'No context for ' + probe)
                actual = value.value.decode().split(':')[2]
                lib.freecon(value)
                require((actual == 'vendor_modem_na77_file') == expected, 'Wrong NA77 path scope: ' + probe)
    finally:
        lib.selabel_close(handle)


def verify(root, directory, policy, contexts, vendor_text, system_text, file_contexts):
    path = directory / 'policy.bin'
    path.write_bytes(policy)
    cil = directory / 'policy.cil'
    subprocess.run([str(root / 'out/host/linux-x86/bin/checkpolicy'), '-M', '-b', '-C', '-o', str(cil), str(path)], check=True, capture_output=True)
    allowed = policy_access(cil.read_text())
    permissive = subprocess.check_output([str(root / 'out/host/linux-x86/bin/sepolicy-analyze'), str(path), 'permissive'], text=True).split()
    require(set(permissive) <= {'su', 'backuptool'}, 'Unexpected permissive domain')
    vendor, system = props(vendor_text), props(system_text)
    require(not set(PLATFORM_DEFAULTS) & set(vendor), 'Platform defaults remain in vendor')
    require(all(system.get(k) == v for k, v in PLATFORM_DEFAULTS.items()), 'Relocated platform default changed')
    require(vendor.get('ro.vendor.mtk_md1_support') == '9', 'MD1 configuration missing')
    resolved = lookup(root, directory, contexts, sorted(vendor))
    denied = [key for key, target in resolved.items() if not allowed('vendor_init', target, 'property_service', 'set')]
    require(not denied, 'Unpublishable vendor defaults: ' + ', '.join(denied))
    for target in ['config_prop', 'default_prop', 'radio_prop', 'system_prop']:
        require(not allowed('vendor_init', target, 'property_service', 'set'), 'Private platform setter grant')
    for target in ['vendor_display_pipeline_prop', 'vendor_media_color_mode_prop', 'proc_meminfo']:
        for permission in ['open', 'read', 'getattr']:
            require(allowed('hal_camera_default', target, 'file', permission), 'Missing camera read: ' + target)
        require(not allowed('hal_camera_default', target, 'file', 'write'), 'Unexpected camera write')
    require(allowed('vold', 'vendor_mount_parent', 'dir', 'search'), 'Missing vold traversal')
    require(not allowed('vendor_bip', 'net_dns_prop', 'file', 'read'), 'BIP private DNS bypass')
    require(not allowed('vendor_nvram_daemon', 'block_device', 'blk_file', 'write'), 'Unexpected generic raw block write')
    for permission in ('getattr', 'open', 'read', 'write'):
        require(allowed('vendor_ccci_fsd', 'vendor_modem_na77_file', 'file', permission), 'Missing NA77 access: ' + permission)
    for permission in ('create', 'append', 'setattr', 'unlink', 'rename'):
        require(not allowed('vendor_ccci_fsd', 'vendor_modem_na77_file', 'file', permission), 'Excess NA77 access: ' + permission)
    require(not allowed('vendor_ccci_fsd', 'vendor_modem_protect_file', 'file', 'write'), 'Broadened protect-file writes')
    require(allowed('vendor_init', 'vendor_modem_na77_file', 'file', 'relabelto'), 'NA77 restorecon denied')
    require(allowed('vendor_gsm0710muxd', 'radio_device', 'dir', 'remove_name'), 'Missing mux cleanup')
    require(allowed('vendor_gsm0710muxd', 'radio_device', 'lnk_file', 'unlink'), 'Missing mux unlink')
    require(not allowed('vendor_gsm0710muxd', 'radio_device', 'chr_file', 'unlink'), 'Radio device deletion')
    verify_sim_paths(root, directory, file_contexts)
    return {'vendor_defaults': len(vendor), 'md1_support': '9', 'permissive_domains': permissive,
            'sim_existing_na77_and_mux_recovery': True,
            'scope': 'actual property trie/vendor-init publication, platform relocation, selected camera/storage/BIP/SIM recovery boundaries'}
