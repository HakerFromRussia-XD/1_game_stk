#!/bin/sh
# Xcode signs the executable before CMake's iOS resource overlay.  Seal the
# final, curated app bundle with that same provisioning identity afterwards.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <Fluxara Drift.app>" >&2
    exit 64
fi

bundle=$1
[ -d "$bundle" ] || {
    echo "missing Fluxara iOS bundle: $bundle" >&2
    exit 66
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
entitlements="$script_dir/../data/FluxaraDrift-iOS.entitlements"
[ -f "$entitlements" ] || {
    echo "missing Fluxara iOS entitlements: $entitlements" >&2
    exit 66
}

# The existing signature remains readable even when resource copies made it
# invalid.  Its first Apple Development authority is exactly the identity
# selected by Xcode for this provisioned build.
identity=$(/usr/bin/codesign -dvv "$bundle" 2>&1 | /usr/bin/sed -n \
    's/^Authority=\(Apple Development:.*\)$/\1/p' | /usr/bin/head -n 1)
# A generic iphoneos build intentionally has no run destination and Xcode can
# skip its initial CodeSign phase. The project has one provisioned identity;
# use it only as a fallback, then sign the final resource overlay with the
# explicit Fluxara entitlements.
[ -n "$identity" ] || identity=$(/usr/bin/security find-identity -v -p \
    codesigning | /usr/bin/sed -n \
    's/.*"\(Apple Development: Denis Oskhin (BFZT7C5H4Z)\)".*/\1/p' | \
    /usr/bin/head -n 1)
[ -n "$identity" ] || {
    echo "could not determine Xcode's Apple Development identity" >&2
    exit 65
}

/usr/bin/codesign --force --sign "$identity" \
    --entitlements "$entitlements" \
    --preserve-metadata=identifier,requirements "$bundle"
/usr/bin/codesign --verify --deep --strict --verbose=2 "$bundle"

echo "FLUXARA_IOS_BUNDLE_RESIGNED identity=$identity bundle=$bundle"
