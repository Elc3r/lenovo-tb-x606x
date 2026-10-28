#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Render a future GitHub overlay locally. Never creates or pushes repositories."""
import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--tree', choices=['lineage', 'twrp'], required=True)
    parser.add_argument('--revision', help='override branch/SHA; otherwise use the project-specific branch')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', args.owner):
        raise ValueError('Invalid GitHub owner')
    root = ET.Element('manifest')
    ET.SubElement(root, 'remote', name='tb-x606x', fetch=f'https://github.com/{args.owner}/')
    projects = ([('android_device_lenovo_mt6765-common', 'device/lenovo/mt6765-common'),
                 ('android_device_lenovo_achilles6_row_data', 'device/lenovo/achilles6_row_data')]
                if args.tree == 'lineage' else [('android_device_lenovo_X606X_twrp', 'device/lenovo/X606X')])
    for name, path in projects:
        if args.tree == 'lineage':
            ET.SubElement(root, 'remove-project', path=path, optional='true')
        revision = args.revision or ('lineage-19.1' if args.tree == 'lineage' else 'android-12.1-fbe')
        ET.SubElement(root, 'project', name=name, path=path, remote='tb-x606x', revision=revision)
    ET.indent(root)
    with args.output.open('xb') as output:
        output.write(ET.tostring(root, encoding='utf-8', xml_declaration=True))
    print('Wrote local XML only:', args.output)


if __name__ == '__main__':
    main()
