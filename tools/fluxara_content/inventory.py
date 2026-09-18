#!/usr/bin/env python3
"""Read-only XML/SPM resource inventory. Unresolved references are not runtime failures.

Parses SPM version1 texture tables (static and animated); does not prove rendering compatibility.
"""
import argparse
import json
import struct
from pathlib import Path
import xml.etree.ElementTree as ET

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.spm', '.b3d', '.ogg', '.music', '.wav'}


def inspect(folder, shared):
    files = [p for p in folder.rglob('*') if p.is_file()]
    local = {p.name.lower() for p in files}
    unresolved, errors = [], []
    descriptor = folder / ('track.xml' if (folder / 'track.xml').exists() else 'kart.xml')
    root = ET.parse(descriptor).getroot()
    for xml in files:
        if xml.suffix not in {'.xml', '.music'}:
            continue
        try:
            document = ET.parse(xml)
        except ET.ParseError as error:
            errors.append({'file': str(xml.relative_to(folder)), 'error': str(error)})
            continue
        for element in document.iter():
            for key, value in element.attrib.items():
                # Some attributes list several space-separated textures; preserve
                # filenames containing spaces when an exact local match exists.
                values = [value] if value.lower() in local else value.split()
                for ref in values:
                    if Path(ref).suffix.lower() not in EXTENSIONS:
                        continue
                    if (xml.parent / ref).is_file() or Path(ref).name.lower() in local:
                        continue
                    if Path(ref).name.lower() not in shared:
                        unresolved.append({'xml': str(xml.relative_to(folder)), 'attribute': key, 'reference': ref})
    mesh_textures, mesh_errors = {}, []
    for mesh in files:
        if mesh.suffix.lower() != '.spm':
            continue
        try:
            with mesh.open('rb') as stream:
                if stream.read(2) != b'SP':
                    raise ValueError('Not an SPM header')
                version, flags = stream.read(2)
                if version >> 3 != 1 or version & 7 not in {1, 2}:
                    raise ValueError('Unsupported SPM version')
                stream.read(24)  # bounding box
                count = struct.unpack('<H', stream.read(2))[0]
                textures = []
                for _ in range(count):
                    for _ in range(2):
                        size = stream.read(1)[0]
                        name = stream.read(size).decode('utf-8')
                        if name:
                            textures.append(name)
                mesh_textures[str(mesh.relative_to(folder))] = sorted(set(textures))
        except (ValueError, IndexError, struct.error) as error:
            mesh_errors.append({'mesh': str(mesh.relative_to(folder)), 'error': str(error)})
    mesh_missing = sorted({name for names in mesh_textures.values() for name in names
                           if Path(name).name.lower() not in local | shared})
    licenses = [str(p.relative_to(folder)) for p in files if any(s in p.name.lower() for s in ('license', 'licence', 'copying', 'credits'))]
    return {'id': folder.name, 'name': root.get('name'), 'version': root.get('version'),
            'bytes': sum(p.stat().st_size for p in files), 'files': len(files),
            'licenses': licenses, 'graph': (folder / 'graph.xml').exists(),
            'quads': (folder / 'quads.xml').exists(), 'xml_errors': errors,
            'unresolved_xml_references': unresolved, 'spm_textures': mesh_textures,
            'spm_errors': mesh_errors, 'unresolved_spm_textures': mesh_missing}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path)
    parser.add_argument('--shared', nargs='*', type=Path, default=[])
    args = parser.parse_args()
    shared = {p.name.lower() for root in args.shared for p in root.rglob('*') if p.is_file()}
    print(json.dumps({'scope': 'Static XML and SPM texture references; shared basename matches are candidates, not proof of runtime resolution.',
                      'items': [inspect(p, shared) for p in args.folders]}, indent=2))


if __name__ == '__main__':
    main()
