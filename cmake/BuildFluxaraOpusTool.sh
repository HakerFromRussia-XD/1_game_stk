#!/bin/sh
set -eu

source_file=$1
output_file=$2

# This is a packaging helper which executes on the Mac, but an Xcode
# iphoneos build exports SDKROOT and architecture variables into every custom
# build phase.  Ignore that device environment: compiling this helper against
# iPhoneOS headers produces a host binary that cannot run during packaging.
host_sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
compiler=$(/usr/bin/xcrun --sdk macosx --find clang)
unset SDKROOT PLATFORM_NAME EFFECTIVE_PLATFORM_NAME IPHONEOS_DEPLOYMENT_TARGET
unset ARCHS VALID_ARCHS

mkdir -p "$(dirname "$output_file")"

# This executable only runs while packaging on the Mac.  Current Intel
# Homebrew codec libraries require an x86_64 helper even when Xcode itself is
# arm64; Rosetta runs this one-off host tool transparently.
arch_flag=
if [ "$(uname -m)" = "arm64" ] && [ -d /usr/local/opt/opus ]; then
    arch_flag=-arch\ x86_64
fi

# shellcheck disable=SC2086
exec "$compiler" -isysroot "$host_sdk" $arch_flag -std=c11 -O2 "$source_file" \
    $(pkg-config --cflags --libs opus ogg) -o "$output_file"
