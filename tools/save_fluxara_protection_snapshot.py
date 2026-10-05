#!/usr/bin/env python3
"""Preserve the exact protection sources/maps outside the archived app."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_snapshot(destination, index, audit):
    """Check the retained files, not just the index describing them."""
    expected = {'generated/' + name: sha
                for name, sha in index['generatedFiles'].items()}
    expected.update({'original/' + item['path']: item['sha256']
                     for item in index['inputs']})
    expected['generator.py'] = index['generatorSha256']
    for name, sha in expected.items():
        path = destination / name
        if not path.is_file() or digest(path) != sha:
            raise ValueError('Retained protection file is missing or changed: ' + name)
    if json.loads((destination / 'binary-audit.json').read_text()) != audit:
        raise ValueError('Retained binary audit differs from the archived executable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    archive, build, root = (p.resolve() for p in (args.archive, args.build, args.root))
    # Xcode can finish writing archive metadata after its post-actions. The
    # final application and matching dSYM below are the required evidence.
    if archive.suffix != '.xcarchive' or not (archive / 'Products/Applications').is_dir():
        raise ValueError('Expected an Xcode application archive')
    generated = build / 'protected'
    manifest = json.loads((generated / 'manifest.json').read_text())
    for item in manifest['inputs']:
        if digest(root / item['path']) != item['sha256']:
            raise ValueError('Source changed since generation: ' + item['path'])
    apps = list((archive / 'Products/Applications').glob('*.app'))
    if len(apps) != 1:
        raise ValueError('Expected exactly one archived application')
    bundle = apps[0]
    dsym = archive / 'dSYMs' / (bundle.name + '.dSYM')
    with tempfile.TemporaryDirectory(prefix='fluxara-archive-audit-') as work:
        audit_path = Path(work) / 'audit.json'
        subprocess.run([
            sys.executable, str(root / 'tools/audit_fluxara_protection.py'),
            '--bundle', str(bundle), '--manifest', str(generated / 'manifest.json'),
            '--dsym', str(dsym), '--output', str(audit_path)], check=True,
            stdout=subprocess.PIPE, text=True)
        audit = json.loads(audit_path.read_text())
    source_files = sorted(p for p in generated.rglob('*') if p.is_file())
    index = {'binarySha256': audit['binarySha256'], 'executableUUIDs': audit['executableUUIDs'],
             'buildDirectory': str(build), 'sourceDirectory': str(root),
             'generatedFiles': {str(p.relative_to(generated)): digest(p) for p in source_files},
             'inputs': manifest['inputs'],
             'generatorSha256': digest(root / 'tools/protect_fluxara_sources.py'),
             'scope': 'Protection snapshot for symbolication; outside the distributed app.'}
    destination = archive / 'CodeProtection'
    if destination.exists():
        # Never replace a mapping belonging to a different archived executable.
        saved = json.loads((destination / 'snapshot.json').read_text())
        if saved != index:
            raise ValueError('Existing protection snapshot differs; choose a new archive path')
        verify_snapshot(destination, index, audit)
        print('Protection snapshot already matches ' + str(archive))
        return
    with tempfile.TemporaryDirectory(prefix='.protection-', dir=archive) as work:
        staging = Path(work) / 'CodeProtection'
        for path in source_files:
            target = staging / 'generated' / path.relative_to(generated)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        for item in manifest['inputs']:
            target = staging / 'original' / item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / item['path'], target)
        shutil.copy2(root / 'tools/protect_fluxara_sources.py', staging / 'generator.py')
        (staging / 'snapshot.json').write_text(json.dumps(index, indent=2) + '\n')
        (staging / 'binary-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
        staging.rename(destination)
    print('Saved protection snapshot: ' + str(destination))


if __name__ == '__main__':
    main()
