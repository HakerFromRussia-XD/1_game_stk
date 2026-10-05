#!/usr/bin/env python3
"""Generate opt-in C++ protection with stock Apple Clang; never edit inputs.

This deliberately handles an allowlist of owned UI translation units, not
arbitrary C++. Token boundaries protect comments, includes and quoted text.
The control-flow pass accepts only checked, side-effect-free decision chains
and fails on source drift. Encryption raises inspection cost; keys are in the
app, so it provides no cryptographic secrecy.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

SCREENS = ('home', 'campaign', 'kart', 'race_setup', 'race_result', 'settings')
PUBLIC_TYPES = ('FluxaraHomeScreen', 'FluxaraCampaignScreen', 'FluxaraKartScreen',
                'FluxaraRaceSetupScreen', 'FluxaraSettingsScreen')
PRIVATE_NAMES = {
    'campaign': ('FluxaraTrackDownloadRequest', 'campaignTrack', 'drawTrackDownloadControl'),
    'race_result': ('art',),
}
FLOW_FUNCTIONS = ('nativeMode', 'laps', 'timed', 'arena', 'hasOfflineOpponents')
TOKEN = re.compile(
    r'(?P<directive>^[ \t]*\#(?:\\\r?\n|[^\n])*)'
    r'|(?P<comment>//[^\n]*|/\*.*?\*/)'
    r'|(?P<raw>(?:u8|u|U|L)?R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\(.*?\)(?P=delimiter)")'
    r'|(?P<string>(?:u8|u|U|L)?"(?:\\.|[^"\\])*")'
    r"|(?P<char>(?:u8|u|U|L)?'(?:\\.|[^'\\])*')"
    r'|(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)'
    r'|(?P<space>\s+)|(?P<other>.)', re.M | re.S)


@dataclass
class Token:
    kind: str
    text: str
    start: int
    end: int


def tokens(text):
    result = [Token(m.lastgroup, m.group(), m.start(), m.end())
              for m in TOKEN.finditer(text)]
    if ''.join(t.text for t in result) != text:
        raise ValueError('Lexer did not consume complete source')
    return result


def narrow_bytes(literal):
    """Decode C++ ordinary narrow string escapes without Python's semantics."""
    if not literal.startswith('"'):
        raise ValueError('Only ordinary narrow strings are accepted')
    text = literal[1:-1]
    output = bytearray()
    i = 0
    simple = {'a': 7, 'b': 8, 'f': 12, 'n': 10, 'r': 13, 't': 9, 'v': 11,
              '\\': 92, '"': 34, "'": 39, '?': 63}
    while i < len(text):
        c = text[i]
        i += 1
        if c != '\\':
            output.extend(c.encode('utf-8'))
            continue
        if i == len(text):
            raise ValueError('Unterminated escape')
        c = text[i]
        i += 1
        if c in simple:
            output.append(simple[c])
        elif c in '01234567':
            digits = c
            while i < len(text) and len(digits) < 3 and text[i] in '01234567':
                digits += text[i]
                i += 1
            number = int(digits, 8)
            if number > 255:
                raise ValueError('Octal escape exceeds one byte')
            output.append(number)
        elif c == 'x':
            start = i
            while i < len(text) and text[i] in '0123456789abcdefABCDEF':
                i += 1
            if start == i or int(text[start:i], 16) > 255:
                raise ValueError('Invalid narrow hexadecimal escape')
            output.append(int(text[start:i], 16))
        elif c in 'uU':
            width = 4 if c == 'u' else 8
            digits = text[i:i + width]
            if len(digits) != width or not re.fullmatch('[0-9a-fA-F]+', digits):
                raise ValueError('Invalid universal character name')
            output.extend(chr(int(digits, 16)).encode('utf-8'))
            i += width
        elif c == '\n':
            pass
        else:
            raise ValueError('Unsupported escape: ' + c)
    return bytes(output)


def opaque(name):
    return 'p_' + hashlib.sha256(('fluxara-v1:' + name).encode()).hexdigest()[:16]


class Pool:
    def __init__(self):
        self.values = {}

    def reference(self, value):
        name = opaque(value.hex())
        previous = self.values.setdefault(name, value)
        if previous != value:
            raise ValueError('String symbol collision')
        return 'FluxaraProtected::' + name + '()'

    def emit(self):
        header = ['#pragma once', 'namespace FluxaraProtected {']
        source = ['#include "protected_strings.hpp"', '#include <string>',
                  '#include <cstdint>', 'namespace FluxaraProtected {',
                  'namespace {',
                  '__attribute__((noinline)) std::string p_decode(',
                  '    const volatile unsigned char* data, std::size_t size, std::uint32_t key)',
                  '{', '    std::string result(size, \'\\0\');',
                  '    for (std::size_t i = 0; i < size; ++i) {',
                  '        key = key * 1664525u + 1013904223u;',
                  '        result[i] = static_cast<char>(data[i] ^ (key >> 24));',
                  '    }', '    return result;', '}', '}']
        for name, value in sorted(self.values.items()):
            initial = int(hashlib.sha256(value + b'fluxara-pool-v1').hexdigest()[:8], 16)
            key = initial
            encoded = []
            for byte in value:
                key = (key * 1664525 + 1013904223) & 0xffffffff
                encoded.append(byte ^ (key >> 24))
            header.append('const char* ' + name + '();')
            source.extend([
                'const char* ' + name + '() {',
                '    static const volatile unsigned char data[] = {' +
                ','.join(str(x) for x in encoded) + '};',
                '    static const std::string value = p_decode(data, sizeof(data), ' + str(initial) + 'u);',
                '    return value.c_str();', '}'])
        header.append('}')
        source.append('}')
        return '\n'.join(header) + '\n', '\n'.join(source) + '\n'


def protect_text(text, pool, renames=None):
    renames = renames or {}
    stream = tokens(text)
    output = []
    count = 0
    i = 0
    while i < len(stream):
        t = stream[i]
        if t.kind == 'identifier' and t.text in renames:
            output.append(renames[t.text])
        elif t.kind == 'string' and t.text.startswith('"'):
            # Adjacent literals form one array, even with intervening comments.
            end = i + 1
            group = [t]
            while end < len(stream):
                j = end
                while j < len(stream) and stream[j].kind in ('space', 'comment'):
                    j += 1
                if j == len(stream) or stream[j].kind != 'string' or not stream[j].text.startswith('"'):
                    break
                group.append(stream[j])
                end = j + 1
            value = b''.join(narrow_bytes(s.text) for s in group)
            if len(value) >= 4:
                output.append(pool.reference(value))
                count += 1
            else:
                output.append(''.join(s.text for s in stream[i:end]))
            i = end
            continue
        else:
            output.append(t.text)
        i += 1
    return ''.join(output), count


def flow_body(name, original, result_type):
    clean = ''.join(t.text for t in tokens(original) if t.kind != 'comment').strip()
    branches = []
    if name == 'nativeMode':
        branch = re.compile(r'if\s*\((.*?)\)\s*return\s+([^;]+);', re.S)
        position = 0
        for match in branch.finditer(clean):
            if clean[position:match.start()].strip():
                raise ValueError('Unexpected nativeMode statement')
            condition, value = match.groups()
            # Only side-effect-free mode equality/disjunction chains qualify.
            if not re.fullmatch(r'\s*mode\s*==\s*"[a-z_]+"(?:\s*\|\|\s*mode\s*==\s*"[a-z_]+")*\s*', condition):
                raise ValueError('Unexpected nativeMode predicate')
            if not re.fullmatch(r'RaceManager::MINOR_MODE_[A-Z_0-9]+', value.strip()):
                raise ValueError('Unexpected nativeMode return')
            branches.append((condition, value.strip()))
            position = match.end()
        final = re.fullmatch(r'\s*return\s+(RaceManager::MINOR_MODE_[A-Z_0-9]+);\s*', clean[position:])
        if not final or not branches:
            raise ValueError('nativeMode no longer has the supported decision shape')
        fallback = final.group(1)
    else:
        final = re.fullmatch(r'return\s+(.*);', clean, re.S)
        if not final:
            raise ValueError('Unsupported boolean function: ' + name)
        expr = final.group(1).strip()
        allowed = r'mode\s*(?:==|!=)\s*"[a-z_]+"(?:\s*(?:\|\||&&)\s*mode\s*(?:==|!=)\s*"[a-z_]+")*'
        if not re.fullmatch(allowed, expr):
            raise ValueError('Unsupported boolean predicate: ' + name)
        if '&&' in expr:
            branches = [(expr, 'true')]
        else:
            branches = [(part.strip(), 'true') for part in expr.split('||')]
        fallback = 'false'
    mask = int(hashlib.sha256((name + ':mask').encode()).hexdigest()[:8], 16)
    states = [int(hashlib.sha256((name + ':' + str(i)).encode()).hexdigest()[:8], 16)
              for i in range(len(branches) + 1)]
    if len(set(states)) != len(states):
        raise ValueError('Dispatcher state collision')

    def protected_return(value):
        # Unsigned arithmetic avoids signed-overflow UB. Both volatile mask
        # reads observe the same process-local value; they defeat folding.
        return 'static_cast<' + result_type + '>((static_cast<std::uint32_t>(' + value + ') ^ mask) ^ mask)'

    blocks = []
    for i, (condition, value) in enumerate(branches):
        blocks.append((states[i], [
            '        case ' + str(states[i]) + 'u:',
            '            if (' + condition + ') return ' + protected_return(value) + ';',
            '            state = ' + str(states[i + 1]) + 'u ^ mask;',
            '            break;']))
    blocks.append((states[-1], ['        case ' + str(states[-1]) + 'u:',
                               '            return ' + protected_return(fallback) + ';']))
    lines = ['{', '    volatile std::uint32_t mask = ' + str(mask) + 'u;',
             '    volatile std::uint32_t state = ' + str(states[0]) + 'u ^ mask;',
             '    for (;;) {', '        switch (state ^ mask) {']
    for _, block in sorted(blocks):
        lines.extend(block)
    lines.extend(['        default: return ' + fallback + ';', '        }', '    }', '}'])
    return '\n'.join(lines)


def protect_flow(text):
    changes = []
    for name in FLOW_FUNCTIONS:
        signature = re.search(r'inline\s+([A-Za-z_][\w:]*)\s+' + name +
                              r'\(const std::string& mode\)\s*\{', text)
        if not signature:
            raise ValueError('Missing expected function: ' + name)
        start = signature.end() - 1
        depth = 0
        end = None
        for t in tokens(text[start:]):
            if t.kind == 'other' and t.text == '{':
                depth += 1
            elif t.kind == 'other' and t.text == '}':
                depth -= 1
                if depth == 0:
                    end = start + t.end
                    break
        if end is None:
            raise ValueError('Unbalanced function: ' + name)
        body = flow_body(name, text[start + 1:end - 1], signature.group(1))
        declaration = text[signature.start():start].replace('inline ', 'inline __attribute__((noinline)) ', 1)
        changes.append((signature.start(), end, declaration + body))
    for start, end, replacement in sorted(changes, reverse=True):
        text = text[:start] + replacement + text[end:]
    return '#include <cstdint>\n' + text


def write_changed(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != data:
        path.write_text(data)


def generate(root, output):
    root = root.resolve()
    destination = output.resolve()
    protected_directories = [root / name for name in ('src', 'lib', 'data', 'iosApp', 'cmake', 'tools', 'docs')]
    if (destination == root or destination in root.parents or
            any(destination == path or path in destination.parents for path in protected_directories)):
        raise ValueError('Output must be a separate build directory')
    pool = Pool()
    manifest = {'format': 1, 'configuration': 'ReleaseProtected', 'inputs': [],
                'renamedTypes': {name: opaque(name) for name in PUBLIC_TYPES},
                'flowFunctions': list(FLOW_FUNCTIONS), 'privateNames': {}}
    for screen in SCREENS:
        relative = 'src/states_screens/fluxara_' + screen + '_screen.cpp'
        original = (root / relative).read_text()
        renames = {name: opaque(name) for name in PRIVATE_NAMES.get(screen, ())}
        identifiers = {t.text for t in tokens(original) if t.kind == 'identifier'}
        if not set(renames) <= identifiers:
            raise ValueError('Private symbol allowlist drift: ' + relative)
        transformed, count = protect_text(original, pool, renames)
        # DWARF must name the actual generated file: flow transformations
        # change line counts, so pretending these are original-source lines
        # would produce misleading crash locations. Keep the generated snapshot.
        prefix = '#include "protected_strings.hpp"\n'
        write_changed(output / relative, '#ifdef FLUXARA_PROTECTED_RELEASE\n' + prefix + transformed +
                      '\n#else\n#include "' + (root / relative).as_posix() + '"\n#endif\n')
        manifest['inputs'].append({'path': relative, 'sha256': hashlib.sha256(original.encode()).hexdigest(),
                                   'stringSites': count})
        manifest['privateNames'][relative] = renames
    relative = 'src/states_screens/fluxara_event.hpp'
    original = (root / relative).read_text()
    transformed, count = protect_text(protect_flow(original), pool)
    write_changed(output / 'states_screens/fluxara_event.hpp',
                  '#include "protected_strings.hpp"\n' + transformed)
    manifest['inputs'].append({'path': relative, 'sha256': hashlib.sha256(original.encode()).hexdigest(),
                               'stringSites': count})
    header, source = pool.emit()
    write_changed(output / 'protected_strings.hpp', header)
    write_changed(output / 'protected_strings.cpp', '#ifdef FLUXARA_PROTECTED_RELEASE\n' + source + '\n#endif\n')
    symbols = ['#pragma once', '#ifdef FLUXARA_PROTECTED_RELEASE']
    for old, new in manifest['renamedTypes'].items():
        symbols.append('#define ' + old + ' ' + new)
    symbols.append('#endif')
    write_changed(output / 'protected_symbols.hpp', '\n'.join(symbols) + '\n')
    # Keep reversible mappings and plaintext audit data outside the app.
    manifest['strings'] = [{'symbol': name, 'hex': value.hex(), 'size': len(value)}
                           for name, value in sorted(pool.values.items())]
    write_changed(output / 'manifest.json', json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'stringSites': sum(x['stringSites'] for x in manifest['inputs']),
                      'uniqueStrings': len(pool.values), 'flowFunctions': list(FLOW_FUNCTIONS)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    generate(args.root, args.output)


if __name__ == '__main__':
    main()
