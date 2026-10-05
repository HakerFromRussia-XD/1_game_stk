# Fluxara iOS code protection

`ReleaseProtected` is an additional build configuration, exposed by the
**Fluxara Protected** Xcode scheme. Its Archive and Profile actions select
`ReleaseProtected`; the normal scheme keeps its existing Release action.
Debug and ordinary Release compile the original readable sources through
generated wrappers. Android and third-party library APIs are unaffected.

## Implemented passes, in order

1. Diagnostic `Log::info`, `debug` and `verbose` calls become inline no-ops
   in the protected configuration. C++ still evaluates their arguments and
   preserves side effects. Warnings, errors and fatal termination remain.
   Dead-code stripping, hidden internal C++ symbols, full LTO and distribution
   symbol stripping apply to the main executable. Macro source paths are
   remapped; real source/debug information is retained in the external dSYM.
2. A token-aware generator creates protected copies of the six Fluxara UI
   translation units and `fluxara_event.hpp`. Ordinary narrow literals of at
   least four bytes are pooled and encoded. A decoder reading volatile bytes
   prevents compile-time recovery of plaintext. Each value is initialized
   once with thread-safe C++11 static initialization and retains a stable
   `const char*` address. No keys are secret; this is reverse-engineering
   friction, not encryption of credentials or a server-authentication system.
3. Five internal UI types and allowlisted private helpers are renamed in the
   compiled copies. Five pure mode-selection/predicate functions use a
   flattened dispatcher, reordered states, volatile state loads and unsigned
   XOR expressions. This pass works with stock Apple Clang. It does not
   install or assume a custom LLVM compiler/pass plug-in. It rejects source
   shapes it cannot transform safely rather than silently using old logic.
4. The existing Xcode archive/signing pipeline packages the compiled result.
   No executable patching occurs after signing. The external dSYM and the
   `protected/` source snapshot and mapping must be retained with each exact build.
   DWARF refers to the generated files, whose line numbers include transformed
   statements. Keep that snapshot outside the app, alongside its archive/dSYM.
   The protected scheme's Archive post-action audits the completed app/dSYM
   and writes `CodeProtection/` inside the `.xcarchive`, next to `Products/`
   and `dSYMs/`. It contains generated sources, readable module inputs, the
   generator, hashes and a reversible mapping. Nothing is added to the app.
   Reusing an archive verifies the retained files and binary audit again;
   missing or altered mappings, sources and generator files cause an error.

## Boundaries

Protection covers selected owned UI/mode modules and diagnostic logging in
the main executable. It does not obfuscate the complete engine, Swift/ObjC
runtime metadata, shaders, XML, images, API imports or third-party code.
Resource identifiers retain exactly the same values at runtime. Some pooled
values also occur in unprotected engine code and remain visible there.
License/provenance files are not renamed or concealed by this pass.

The generated manifest intentionally contains reversible identifier mappings,
input hashes and original string bytes. It stays in the build directory and
must never be copied into the app. No generated-source archive is a substitute
for keeping the original source and the matching dSYM.

## Verification

Run the behavioural and optimized-code checks:

```sh
python3 tools/test_fluxara_protection.py --output /absolute/path/to/checks
```

They compile both the original and actual generated mode functions with
Apple Clang, compare recognized/unknown/embedded-NUL/randomized inputs, test
every pooled string, check deterministic generation and rejected source drift,
and verify diagnostic elimination while retaining side effects and fatal exit.
The reported CPU microbenchmark is a host result, not iOS/FPS acceptance.

After the complete Xcode build/archive finishes, inspect the exact app:

```sh
python3 tools/audit_fluxara_protection.py \
  --bundle '/absolute/path/Fluxara Drift.app' \
  --manifest /absolute/path/build/protected/manifest.json \
  --dsym '/absolute/path/Fluxara Drift.app.dSYM' \
  --output /absolute/path/binary-audit.json
```

This checks the final Mach-O for original protected names, developer paths,
local symbols and embedded DWARF; checks for accidentally packaged source/map
files; and requires both a matching dSYM UUID and actual debug information.
It reports shared plaintext values instead of claiming whole-app secrecy.

Configure simulator validation explicitly in its own build directory with
`FLUXARA_IOS_PLATFORM=iphonesimulator`, `CMAKE_OSX_SYSROOT=iphonesimulator`
and the simulator dependencies. Build with the **Fluxara Protected** scheme,
`-configuration ReleaseProtected`, `-sdk iphonesimulator` and an explicit
Simulator destination. Simulator results do not establish a distributable
App Store archive, device signing or physical-device performance.

Compare a normal Release and ReleaseProtected built from the same source and
resources, then verify Home/Campaign/Garage/Settings, representative race modes,
loading, memory, and frame behaviour. Preserve source hashes, build logs,
binary audit, screenshots and runtime measurements with the release evidence.

The October 2–3 validation transformed 391 literal sites into 185 pooled values
and checked 3,578 mode inputs against the original functions. All five
transformed functions retained XOR/state operations and conditional branches
in the final LTO-linked archive. The executable decreased from 33,595,776 to
26,090,272 bytes. The controlled Simulator counter medians were 130 for Release
and 123 for the final protected executable, with one run per version. This
measurement does not establish a statistically reliable performance difference.
Of 4,380 resource files, 4,379 matched byte for byte; `Assets.car` had different
archive/thinning metadata but identical rendition metadata and content digests.

The runtime probe accepts `--disable-sound` for isolated UI/rendering checks.
During the October 2–3, 2026 comparison, both ordinary Release and the protected
build exhibited `queue_new_buffer_items_recursive` crashes in the MojoAL music
thread. Initial launch/render checks passed, but they do not establish audio or
release readiness. Controlled frame/longer UI checks used `--no-sound`; the
audio issue needs separate investigation before distribution.
