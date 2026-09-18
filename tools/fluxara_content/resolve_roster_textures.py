#!/usr/bin/env python3
"""Restore exact texture aliases referenced by unchanged imported SPM files.

Image loader checks file contents after extension lookup (CNullDriver.cpp:1322),
so retaining PNG bytes at an SPM's historical DDS name does not require lossy
conversion or a mesh edit. Runtime rendering is still a separate check.
"""
import hashlib
import json
from pathlib import Path
import shutil

root = Path('iosApp/FluxaraResources/tracks')
repairs = [
    ('fluxara-user-maple-overpass', 'greyb1_dds_img.png', 'greyb1_dds_img'),
    ('fluxara-user-maple-overpass---short', 'greyb1_dds_img.png', 'greyb1_dds_img'),
    ('fluxara-user-skid-grounds', 'stripes.png', 'stripes.dds'),
    ('fluxara-user-motorsport-land', 'OBJ.png', 'OBJ.dds'),
]
evidence = []
for folder, original, alias in repairs:
    source, target = root / folder / original, root / folder / alias
    if target.exists() and source.read_bytes() != target.read_bytes():
        raise ValueError('Refusing to replace differing file: ' + str(target))
    shutil.copyfile(source, target)
    evidence.append({'source': str(source), 'destination': str(target), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                     'license': 'existing retained source-package license; bytes unchanged'})
source = root / 'fluxara-user-lap-catch/neocity_concrete.png'
target = root / 'fluxara-user-electro-station/neocity_concrete.png'
if target.exists() and source.read_bytes() != target.read_bytes():
    raise ValueError('Refusing to replace differing file: ' + str(target))
shutil.copyfile(source, target)
shutil.copyfile(root / 'fluxara-user-lap-catch/license.txt', target.parent / 'LICENSE-dependency-lap-catch.txt')
evidence.append({'source': str(source), 'destination': str(target), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                 'license': 'LICENSE-dependency-lap-catch.txt; original package says CC-BY4 textures or stock STK texture sources; preserve provenance, rights acceptance separate'})
Path('docs/fluxara-content/texture-dependency-repairs.json').write_text(json.dumps({'repairs': evidence}, indent=2)+'\n')
print(json.dumps({'exact_texture_copies': len(evidence), 'geometry_changes': 0}))
