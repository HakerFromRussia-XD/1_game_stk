#!/usr/bin/env python3
"""Run one bounded Simulator AI lap and retain evidence; never restart the app.

The output directory must be new. Completion requires ProfileWorld summary,
four kart result rows, no fatal log marker, and successful console process exit.
This is AI lap evidence, not visual acceptance or physical-device performance.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time


def completion(log):
    rows = []
    for line in log.splitlines():
        match = re.search(r'profile:\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+', line)
        if match and 1 <= int(match[3]) <= 4 and 1 <= int(match[4]) <= 4 and float(match[5]) > 0:
            rows.append({'kart': match[1], 'controller': match[2], 'start': int(match[3]),
                         'end': int(match[4]), 'time': float(match[5])})
    return {'frame_summary': bool(re.search(r'Number of frames: \d+ time .*Average FPS:', log)),
            'aggregate_summary': bool(re.search(r'profile:\s+min [\d.]+\s+max [\d.]+\s+av [\d.]+', log)),
            'kart_results': rows, 'fatal_marker': bool(re.search(r'\[fatal\]|SIGSEGV|EXC_BAD_ACCESS', log, re.I))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('udid', 'bundle-id', 'track', 'kart', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--timeout', type=float, default=240)
    parser.add_argument('--capture-interval', type=float, default=15)
    parser.add_argument('--render-driver', choices=('vulkan', 'opengl'), default='vulkan')
    parser.add_argument('--rtt-scale', type=int, default=50)
    args = parser.parse_args()
    if args.timeout <= 0 or args.capture_interval <= 0:
        parser.error('Timeout and capture interval must be positive')
    if not 1 <= args.rtt_scale <= 100:
        parser.error('RTT scale must be between 1 and 100')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = ['xcrun', 'simctl', 'launch', '--console', args.udid, args.bundle_id,
               '--track=' + args.track, '--kart=' + args.kart, '--numkarts=4',
               '--profile-laps=1', '--race-now', '--log=0', '--logbuffer=1',
               '--render-driver=' + args.render_driver,
               '--rtt-scale=' + str(args.rtt_scale), '--shadows=0', '--fps-debug']
    evidence = {'command': command, 'track': args.track, 'kart': args.kart,
                'status': 'running', 'captures': [], 'timeout_seconds': args.timeout,
                'scope': 'Simulator AI lap only; screenshot review and physical-device performance remain separate.'}
    def save():
        (out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    save()
    started = time.monotonic()
    next_capture = args.capture_interval
    timed_out = False
    with (out / 'console.log').open('x') as console:
        process = subprocess.Popen(command, stdout=console, stderr=subprocess.STDOUT)
        while process.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed >= args.timeout:
                timed_out = True
                # Stop only this console observer, not the simulator/device or app.
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break
            if elapsed >= next_capture:
                destination = out / ('lap-%03d.png' % elapsed)
                capture_command = ['xcrun', 'simctl', 'io', args.udid, 'screenshot', str(destination)]
                try:
                    capture = subprocess.run(capture_command, capture_output=True, text=True, timeout=20)
                    evidence['captures'].append({'command': capture_command, 'elapsed': elapsed,
                                                 'returncode': capture.returncode, 'stderr': capture.stderr})
                except subprocess.TimeoutExpired:
                    evidence['captures'].append({'command': capture_command, 'elapsed': elapsed, 'error': 'capture timeout'})
                next_capture += args.capture_interval
                save()
            time.sleep(0.5)
    evidence.update({'elapsed': time.monotonic() - started, 'console_exit': process.returncode,
                     'timed_out': timed_out, 'completion': completion((out / 'console.log').read_text(errors='replace'))})
    result = evidence['completion']
    four_rows = len(result['kart_results']) == 4 and {r['start'] for r in result['kart_results']} == {1, 2, 3, 4}
    passed = not timed_out and process.returncode == 0 and result['frame_summary'] and result['aggregate_summary'] and four_rows and not result['fatal_marker']
    evidence['status'] = 'lap_completion_observed' if passed else 'completion_not_proven'
    save()
    print(json.dumps(evidence, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
