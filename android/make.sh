#!/bin/sh
# Build the Android STK product from the same checkout as iOS Fluxara Drift.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$script_dir"
if [ "${1:-}" = clean ]; then
    exec ./gradlew clean
fi
case "${BUILD_TYPE:-debug}" in
    debug|Debug) task=assembleDebug ;;
    release|Release|beta) task=assembleRelease ;;
    *) echo "BUILD_TYPE must be debug or release" >&2; exit 1 ;;
esac
arch="${COMPILE_ARCH:-arm}"
case "$arch" in armv7) arch=armeabi-v7a ;; aarch64) arch=arm64-v8a ;; esac
# Signing remains external configuration; passwords never appear in command arguments.
if [ -n "${STK_KEYSTORE:-}" ]; then export ORG_GRADLE_PROJECT_motoricaReleaseStoreFile="$STK_KEYSTORE"; fi
if [ -n "${STK_STOREPASS:-}" ]; then
    export ORG_GRADLE_PROJECT_motoricaReleaseStorePassword="$STK_STOREPASS"
    export ORG_GRADLE_PROJECT_motoricaReleaseKeyPassword="$STK_STOREPASS"
fi
if [ -n "${STK_ALIAS:-}" ]; then export ORG_GRADLE_PROJECT_motoricaReleaseKeyAlias="$STK_ALIAS"; fi
if [ -n "${SDK_PATH:-}" ]; then export ANDROID_HOME="$SDK_PATH"; fi
exec ./gradlew --no-daemon "$task" "-Pcompile_arch=$arch" "-Pcpu_core=${CPU_CORE:--j4}" "$@"
