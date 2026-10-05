#!/usr/bin/env python3
"""Inspect a final protected Mach-O and matching dSYM without modifying them."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess


def command(*args):
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def uuids(path):
    return sorted(re.findall(r'UUID: ([A-Fa-f0-9-]+) \(([^)]+)\)',
                             command('xcrun', 'dwarfdump', '--uuid', str(path))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--dsym', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with (args.bundle / 'Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    executable = args.bundle / info['CFBundleExecutable']
    payload = executable.read_bytes()
    manifest = json.loads(args.manifest.read_text())
    failures = []
    renamed = list(manifest['renamedTypes'])
    renamed += [name for mapping in manifest['privateNames'].values() for name in mapping]
    # Ignore short common locals: "art" is present throughout other modules.
    original_type_residuals = [name for name in renamed if len(name) >= 12 and name.encode() in payload]
    if original_type_residuals:
        failures.append('Original protected C++ type/function names remain in binary')
    developer_paths = re.findall(rb'/Users/[^\x00\n\r]{1,240}', payload)
    if developer_paths:
        failures.append('Absolute developer paths remain in binary')
    load_commands = command('xcrun', 'otool', '-l', str(executable))
    if 'segname __DWARF' in load_commands:
        failures.append('Executable contains embedded DWARF')
    symbol_table = command('xcrun', 'nm', str(executable))
    local_symbols = []
    for line in symbol_table.splitlines():
        match = re.match(r'^[0-9a-fA-F]+\s+([a-z])\s+(.*)', line)
        if match and match.group(1) in 'tdbs':
            local_symbols.append(match.group(2))
    if local_symbols:
        failures.append('Local symbols remain after distribution stripping')
    debug_payload = [p for p in args.bundle.rglob('*') if p.is_file() and
                     (p.suffix in ('.o', '.a', '.c', '.h', '.cc', '.hh', '.cpp', '.hpp', '.cxx', '.hxx',
                                   '.m', '.mm', '.swift', '.pdb', '.xcconfig', '.pbxproj') or
                      p.name in ('manifest.json', 'protected_symbols.hpp', 'protected_strings.cpp'))]
    if debug_payload or any(p.is_dir() for p in args.bundle.rglob('*.dSYM')):
        failures.append('Source, mapping or debug artifacts are packaged in app')
    executable_uuids = uuids(executable)
    dsym_uuids = uuids(args.dsym)
    if not executable_uuids or executable_uuids != dsym_uuids:
        failures.append('dSYM UUID does not match executable')
    dwarf_files = list((args.dsym / 'Contents/Resources/DWARF').glob('*'))
    dsym_has_debug_info = bool(dwarf_files) and all(
        'sectname __debug_info' in command('xcrun', 'otool', '-l', str(p)) for p in dwarf_files)
    if not dsym_has_debug_info:
        failures.append('dSYM has no debug-info section')
    # Many values also occur in unprotected engine modules. Report their
    # presence explicitly; it is not evidence that the selected sites failed.
    shared_strings = [item['symbol'] for item in manifest['strings']
                      if bytes.fromhex(item['hex']) in payload]
    report = {'passed': not failures, 'failures': failures,
              'bundleIdentifier': info['CFBundleIdentifier'],
              'supportedPlatforms': info.get('CFBundleSupportedPlatforms'),
              'binaryBytes': len(payload), 'binarySha256': hashlib.sha256(payload).hexdigest(),
              'executableUUIDs': executable_uuids, 'dsymUUIDs': dsym_uuids,
              'dsymHasDebugInfo': dsym_has_debug_info,
              'originalProtectedSymbolNamesRemaining': original_type_residuals,
              'absoluteDeveloperPathsRemaining': [p.decode(errors='replace') for p in developer_paths],
              'localSymbolCount': len(local_symbols), 'unexpectedPackagedFiles': [str(p) for p in debug_payload],
              'protectedPoolValuesAlsoPresentElsewhere': len(shared_strings),
              'scope': 'Selected owned modules; common engine strings, imported APIs and resources remain inspectable.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
