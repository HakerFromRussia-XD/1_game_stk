#!/usr/bin/env python3
"""Behavioural and optimized-binary checks for the actual generated sources."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import tempfile
import time


def run(command, **kwargs):
    result = subprocess.run(command, text=True, capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('protection', root / 'tools/protect_fluxara_sources.py')
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    directory = args.output / 'generated'
    module.generate(root, directory)
    inputs = {x['path']: x['sha256'] for x in json.loads((directory / 'manifest.json').read_text())['inputs']}
    for relative, digest in inputs.items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest
    before = {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob('*') if p.is_file()}
    module.generate(root, directory)
    assert before == {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob('*') if p.is_file()}
    # A changed predicate must never silently receive a stale transformation.
    original = (root / 'src/states_screens/fluxara_event.hpp').read_text()
    try:
        module.protect_flow(original.replace('mode=="normal"', 'sideEffect(mode)', 1))
    except ValueError:
        pass
    else:
        raise AssertionError('Unsupported source drift was accepted')

    lexer_example = '#include "keep.hpp"\n// "keep comment"\nconst char* x="ab" /* join */ "cd";'
    pool = module.Pool()
    transformed, count = module.protect_text(lexer_example, pool)
    assert '#include "keep.hpp"' in transformed and '// "keep comment"' in transformed
    assert count == 1 and list(pool.values.values()) == [b'abcd']
    directive = '#define KEEP \\\n    "unchanged literal"\n'
    assert module.protect_text(directive, module.Pool()) == (directive, 0)
    assert module.narrow_bytes(r'"\x41\101\n\u0416"') == b'AA\n' + 'Ж'.encode()

    with tempfile.TemporaryDirectory(prefix='fluxara-protection-') as temporary:
        work = Path(temporary)
        flags = ['xcrun', 'clang++', '-std=c++11', '-O3', '-DNDEBUG', '-flto', '-DFLUXARA_PROTECTED_RELEASE=1',
                 '-fvisibility=hidden', '-fvisibility-inlines-hidden',
                 '-I' + str(root / 'src'), '-I' + str(root / 'lib/bullet/src'),
                 '-I' + str(root / 'lib/irrlicht/include'),
                 '-I' + str(root / 'lib/tinygettext/include'),
                 '-I' + str(root / 'dependencies-iphonesimulator/include'),
                 '-I' + str(directory)]
        wrapper = '''#include "HEADER"
extern "C" void FUNCTION(const std::string& mode, int* out) {
    out[0] = FluxaraModes::nativeMode(mode);
    out[1] = FluxaraModes::laps(mode);
    out[2] = FluxaraModes::timed(mode);
    out[3] = FluxaraModes::arena(mode);
    out[4] = FluxaraModes::hasOfflineOpponents(mode);
    out[5] = FluxaraModes::supportedOffline(mode);
}
'''
        baseline = work / 'baseline.cpp'
        protected = work / 'protected.cpp'
        baseline.write_text(wrapper.replace('HEADER', str(root / 'src/states_screens/fluxara_event.hpp'))
                            .replace('FUNCTION', 'baseline').replace('FluxaraModes::', 'BaselineModes::')
                            .replace('#include ', '#define FluxaraModes BaselineModes\n#include ', 1))
        protected.write_text(wrapper.replace('HEADER', str(directory / 'states_screens/fluxara_event.hpp'))
                             .replace('FUNCTION', 'protected_version'))
        # All declared modes, unknown names, case changes, embedded NUL and
        # randomized bytes exercise exact std::string comparison behaviour.
        values = ['normal', 'time_trial', 'ghost_geometry', 'follow_leader', 'lap_trial',
                  'three_strikes', 'free_for_all', 'soccer', 'capture_the_flag', 'egg_hunt',
                  '', 'NORMAL', 'Normal', 'normal ', ' normal', 'soccer\0', '\0normal', 'Ж']
        rng = random.Random(2794)
        cases = [v.encode() for v in values] + [rng.randbytes(rng.randrange(0, 35)) for _ in range(1000)]
        cases += [v.encode() + bytes([x]) for v in values[:10] for x in range(256)]
        arrays = ',\n'.join('std::string({' + ','.join('char(' + str(x) + ')' for x in v) + '})' for v in cases)
        harness = work / 'main.cpp'
        harness.write_text('''#include <string>
#include <vector>
#include <cstdio>
#include <chrono>
extern "C" void baseline(const std::string&, int*);
extern "C" void protected_version(const std::string&, int*);
int main() {
    const std::vector<std::string> cases = {''' + arrays + '''};
    for (const auto& value : cases) {
        int a[6], b[6]; baseline(value, a); protected_version(value, b);
        for (int i = 0; i < 6; ++i) if (a[i] != b[i]) return 1;
    }
    volatile int checksum = 0;
    for (int version = 0; version < 2; ++version) {
        const auto start = std::chrono::steady_clock::now();
        for (int n = 0; n < 100000; ++n) {
            int result[6];
            const auto& value = cases[n % 10];
            if (version) protected_version(value, result); else baseline(value, result);
            checksum += result[0];
        }
        const auto elapsed = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now()-start).count();
        std::printf("%s_us_per_call=%.6f\\n", version ? "protected" : "baseline", elapsed/100000);
    }
    return 0;
}
''')
        binary = args.output / 'mode-equivalence'
        run(flags + [str(baseline), str(protected), str(harness),
                     str(directory / 'protected_strings.cpp'), '-o', str(binary)])
        timings = run([str(binary)]).stdout

        # Decode every pool entry, including byte zero and multi-byte text.
        manifest = json.loads((directory / 'manifest.json').read_text())
        pool_main = work / 'pool.cpp'
        checks = []
        for item in manifest['strings']:
            value = bytes.fromhex(item['hex'])
            expected = ','.join(str(x) for x in value)
            checks.append('{ const unsigned char expected[] = {' + expected + '}; '
                          'if (std::memcmp(FluxaraProtected::' + item['symbol'] +
                          '(), expected, sizeof(expected)) != 0) return 1; }')
        pool_main.write_text('#include "protected_strings.hpp"\n#include <cstring>\nint main(){\n' +
                             '\n'.join(checks) + '\n}\n')
        run(flags + [str(pool_main), str(directory / 'protected_strings.cpp'), '-o', str(work / 'pool')])
        run([str(work / 'pool')])
        # Inspect the optimized decoder without a plaintext golden test table.
        isolated = args.output / 'decoder.o'
        run(flags + ['-c', str(directory / 'protected_strings.cpp'), '-o', str(isolated)])
        raw = isolated.read_bytes()
        for item in manifest['strings']:
            value = bytes.fromhex(item['hex'])
            if len(value) >= 12:
                assert value not in raw, 'Plaintext survived in optimized decoder: ' + value.hex()

        # Compile the real logging header; argument side effects remain even
        # though the diagnostic format and component disappear with -O3/LTO.
        log = work / 'log.cpp'
        log.write_text('''#include "utils/log.hpp"
Log::LogLevel Log::m_min_log_level = Log::LL_WARN;
void Log::printMessage(int, const char*, const char* f, VALIST a) { vprintf(f, a); }
int main(int argc, char**) {
    int effects=0;
    Log::info("DIAGNOSTIC_COMPONENT_SENTINEL_2794", "DIAGNOSTIC_TEXT_SENTINEL_2794 %d", ++effects);
    Log::debug("DIAGNOSTIC_COMPONENT_SENTINEL_2794", "DIAGNOSTIC_TEXT_SENTINEL_2794 %d", ++effects);
    Log::verbose("DIAGNOSTIC_COMPONENT_SENTINEL_2794", "DIAGNOSTIC_TEXT_SENTINEL_2794 %d", ++effects);
    if (effects!=3) return 2;
    Log::warn("warning", "warning survives\\n");
    Log::error("error", "error survives\\n");
    if (argc>1) Log::fatal("fatal", "fatal survives\\n");
    return 0;
}
''')
        log_binary = args.output / 'logging-check'
        run(flags + ['-DFLUXARA_PROTECTED_RELEASE=1', str(log), '-o', str(log_binary)])
        logs = run([str(log_binary)]).stdout
        assert logs == 'warning survives\nerror survives\n'
        fatal = subprocess.run([str(log_binary), 'fatal'], text=True, capture_output=True)
        assert fatal.returncode == 1 and 'fatal survives' in fatal.stdout
        assert b'DIAGNOSTIC_' not in log_binary.read_bytes()

    report = {'modeCases': len(cases), 'comparisonsPerCase': 6,
              'decodedPoolEntries': len(manifest['strings']), 'inputHashesUnchanged': True,
              'deterministicGeneration': True, 'sourceDriftRejected': True,
              'diagnosticStringsRemovedWithLTO': True, 'logArgumentSideEffectsRetained': True,
              'warningErrorFatalRetained': True, 'hostMicrobenchmark': timings.strip().splitlines(),
              'note': 'Host checks are not iOS runtime or graphics-performance acceptance.'}
    (args.output / 'tests.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
