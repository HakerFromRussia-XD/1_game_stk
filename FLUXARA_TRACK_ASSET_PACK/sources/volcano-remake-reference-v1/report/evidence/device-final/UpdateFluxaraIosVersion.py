#!/usr/bin/env python3
"""Keep iOS versions monotonic when packaged track art changes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib


def digest(directory):
    value = hashlib.sha256()
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            value.update(path.relative_to(directory).as_posix().encode())
            value.update(b'\0')
            value.update(hashlib.sha256(path.read_bytes()).digest())
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    resources = root / 'iosApp/FluxaraResources'
    state_path = root / 'iosApp/FluxaraBuildVersion.json'
    fingerprints = {
        'tracks/' + path.name: digest(path)
        for path in sorted((resources / 'tracks').iterdir()) if path.is_dir()
    }
    for name in ('library', 'textures'):
        fingerprints[name] = digest(resources / name)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        changed = sorted(key for key in fingerprints.keys() | state['fingerprints'].keys()
                         if fingerprints.get(key) != state['fingerprints'].get(key))
        if changed:
            state['build'] += 1
            major, minor, patch = map(int, state['marketingVersion'].split('.'))
            state['marketingVersion'] = f'{major}.{minor}.{patch + 1}'
    else:
        # Last recorded release is ios-unlisted-1.0.28 / ios-assets-1.0-build28.
        state = {'marketingVersion': '1.0.29', 'build': 29, 'history': []}
        changed = sorted(fingerprints)
    if changed:
        state['fingerprints'] = fingerprints
        state['history'].append({
            'version': state['marketingVersion'], 'build': state['build'],
            'changedResources': changed,
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        temporary = state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
        os.replace(temporary, state_path)
    if args.bundle:
        plist_path = args.bundle / 'Info.plist'
        with plist_path.open('rb') as stream:
            info = plistlib.load(stream)
        info['CFBundleShortVersionString'] = state['marketingVersion']
        info['CFBundleVersion'] = str(state['build'])
        with plist_path.open('wb') as stream:
            plistlib.dump(info, stream, fmt=plistlib.FMT_BINARY)
        # The manifest identifies the exact track-art revision in this bundle.
        (args.bundle / 'FluxaraTrackRevision.json').write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    print(f"set(IOS_MARKETING_VERSION {state['marketingVersion']})")
    print(f"set(IOS_BUILD_VERSION {state['build']})")


if __name__ == '__main__':
    main()
