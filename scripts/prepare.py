#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check/apply pinned local patches. No network, build, ADB or flashing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--tree', choices=['lineage', 'twrp'], required=True)
    parser.add_argument('--apply', action='store_true', help='apply after all preflight checks pass')
    parser.add_argument('--platform-only', action='store_true', help='device forks are already installed; skip device patches')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    entries = json.loads((HERE / 'patches/series.json').read_text())
    pending = []
    for entry in entries:
        if entry['tree'] != args.tree:
            continue
        if args.platform_only and entry['project'].startswith('device/'):
            continue
        project = root / entry['project']
        patch = HERE / entry['patch']
        if hashlib.sha256(patch.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Patch identity changed: ' + str(patch))
        head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
        if head == entry.get('integrated_revision'):
            status = subprocess.check_output(['git', '-C', str(project), 'status', '--porcelain'], text=True)
            if status.strip():
                raise ValueError('Integrated source has uncommitted changes: ' + entry['project'])
            print('Pinned fork already integrated:', entry['project'])
            continue
        if head != entry['base']:
            raise ValueError('Wrong base revision: ' + entry['project'])
        reverse = subprocess.run(['git', '-C', str(project), 'apply', '--reverse', '--check', str(patch)], capture_output=True)
        if reverse.returncode == 0:
            print('Already applied:', entry['project'])
            continue
        status = subprocess.check_output(['git', '-C', str(project), 'status', '--porcelain'], text=True)
        if status.strip():
            raise ValueError('Unrelated/unrecognized worktree changes: ' + entry['project'])
        subprocess.run(['git', '-C', str(project), 'apply', '--check', str(patch)], check=True)
        pending.append((project, patch))
    for project, patch in pending:
        if args.apply:
            subprocess.run(['git', '-C', str(project), 'apply', str(patch)], check=True)
        print('Applied:' if args.apply else 'Ready:', project.relative_to(root))
    print('No builds or device commands executed.')


if __name__ == '__main__':
    main()
