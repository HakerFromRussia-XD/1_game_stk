#!/usr/bin/env python3
"""Smoke-test the exact installed Simulator build; no device fallback."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import time
import xml.etree.ElementTree as ET


def run(*args, timeout=20):
    return subprocess.run(args, check=True, text=True, capture_output=True, timeout=timeout).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulator', required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--screens-only', action='store_true')
    parser.add_argument('--disable-sound', action='store_true',
                        help='Isolate rendering/UI checks from the existing audio failure')
    parser.add_argument('--sample-seconds', type=float, default=8)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    executable = args.bundle / 'Fluxara Drift'
    installed = Path(run('xcrun', 'simctl', 'get_app_container', args.simulator,
                         'io.fluxara.drift', 'app').strip())
    binary_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    assert binary_hash == hashlib.sha256((installed / 'Fluxara Drift').read_bytes()).hexdigest(), \
        'Installed executable differs from requested bundle'
    cases = [('screen-' + screen, False, ['--fluxara-screen=' + screen])
             for screen in ('home', 'campaign', 'garage', 'settings')]
    if not args.screens_only:
        events = ET.parse(root / 'iosApp/FluxaraResources/fluxara-campaign.xml').getroot().findall('event')[:10]
        for event in events:
            # Stable event ID selects the real native mode in main.cpp. These
            # are launch/render probes, not completed races or campaign wins.
            cases.append((event.get('id'), True, ['--no-start-screen',
                          '--fluxara-event=' + event.get('id'), '--track=' + event.get('track'),
                          '--numkarts=7', '--laps=1']))
    report = {'label': args.label, 'simulator': args.simulator,
              'binarySha256': binary_hash, 'cases': [],
              'soundDisabled': args.disable_sound,
              'scope': 'Visible menus and ten starter-event launches; no completed races, Ghost replay, CTF or physical-device acceptance.'}
    for name, landscape, launch_args in cases:
        start = time.monotonic()
        stdout = output / (name + '.stdout')
        stderr = output / (name + '.stderr')
        response = run('xcrun', 'simctl', 'launch', '--terminate-running-process',
                       '--stdout=' + str(stdout), '--stderr=' + str(stderr), args.simulator,
                       'io.fluxara.drift', '--no-high-scores',
                       *(['--no-sound'] if args.disable_sound else []), *launch_args)
        pid = int(re.search(r': (\d+)', response).group(1))
        frame = output / (name + '.png')
        candidate = output / (name + '.loading.png')
        ready = False
        samples = []
        time.sleep(1)
        while time.monotonic() - start < 45:
            running = run('ps', '-p', str(pid), '-o', 'command=').strip()
            if 'Fluxara Drift.app/Fluxara Drift' not in running:
                raise RuntimeError('Expected app process disappeared: ' + name)
            run('xcrun', 'simctl', 'io', args.simulator, 'screenshot', str(candidate))
            width, height = map(int, run('magick', 'identify', '-format', '%w %h', str(candidate)).split())
            mean = float(run('magick', str(candidate), '-resize', '1x1!', '-colorspace', 'sRGB',
                             '-format', '%[fx:(r+g+b)*255]', 'info:'))
            if (width > height) == landscape and mean > 100:
                ready = True
                break
            time.sleep(0.5)
        if not ready:
            raise RuntimeError('No rendered frame in expected orientation: ' + name)
        ready_time = time.monotonic() - start
        end = time.monotonic() + args.sample_seconds
        while time.monotonic() < end:
            values = run('ps', '-p', str(pid), '-o', 'rss=,pcpu=').split()
            if len(values) != 2:
                raise RuntimeError('Process ended during sample: ' + name)
            samples.append({'rssKiB': int(values[0]), 'cpuPercent': float(values[1])})
            time.sleep(0.5)
        run('xcrun', 'simctl', 'io', args.simulator, 'screenshot', str(frame))
        entry = {'name': name, 'pid': pid, 'frame': str(frame),
                 'orientation': 'landscape' if landscape else 'portrait',
                 'firstRenderedFrameSeconds': ready_time,
                 'observedAliveSeconds': time.monotonic() - start,
                 'medianResidentKiB': statistics.median(s['rssKiB'] for s in samples),
                 'medianHostCpuPercent': statistics.median(s['cpuPercent'] for s in samples),
                 'samples': samples}
        report['cases'].append(entry)
        (output / 'runtime.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in entry.items() if k != 'samples'}), flush=True)
    report['passed'] = True
    (output / 'runtime.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
