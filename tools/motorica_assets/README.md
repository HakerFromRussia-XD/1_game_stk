# Motorica iOS asset packaging

The tracked source of Motorica-specific game data is
`motorica-assets-overlay/data`. Generated build trees and release archives are
not sources of truth.

## Generate and validate

```sh
python3 tools/motorica_assets/build_assets.py all
```

This command:

1. rebuilds the overlay from a compatible `stk-assets` checkout;
2. builds the minimal `build-motorica-ios-assets/assets/data` tree;
3. builds the full data-only ZIP under `dist/motorica-assets`;
4. generates the JSON manifest, SHA-256 file, C++ trusted manifest and size
   header;
5. verifies the minimal track/kart set, packaged AngelScript count, archive
   extensions, paths, required files and adjacent license files.

The release assets for build 28 are:

- `motorica-stk-full-assets-1.zip`
- `motorica-stk-full-assets-1.json`
- `motorica-stk-full-assets-1.sha256`

Upload them to the non-draft, non-prerelease GitHub Release tagged
`ios-assets-1.0-build28`. The application deliberately uses the immutable tag
URL. Any byte change requires a new tag, checksum, manifest and reviewed app
build.
