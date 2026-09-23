#!/bin/bash

OLD_PWD="$(pwd)"

SWITCH_DIR=$(realpath "$(dirname "$0")")
FLUXARA_DRIFT_DIR=$(dirname "${SWITCH_DIR}")

echo "Compiling FLUXARA_DRIFT"

if [[ ! -d "${FLUXARA_DRIFT_DIR}/cmake_build" ]]; then
  mkdir "${FLUXARA_DRIFT_DIR}/cmake_build"
fi
cd "${FLUXARA_DRIFT_DIR}/cmake_build"

"${DEVKITPRO}/portlibs/switch/bin/aarch64-none-elf-cmake" -G"Unix Makefiles" \
    -DCMAKE_INSTALL_PREFIX=/ -DNO_SHADERC=on \
    ../

make -j$(nproc) || exit 1
make install DESTDIR=./install || exit 1

# Build nro (executable for switch)
"${SWITCH_DIR}/package.sh"

echo "Building package"

rm -rf sdcard
mkdir sdcard
# Move data over
mv install/share/fluxaradrift/data sdcard/fluxara_drift-data
# Add executable
mkdir sdcard/switch
mv bin/fluxara_drift.nro sdcard/switch/fluxara_drift.nro

echo "Compressing"

# Zip up actual release:
cd sdcard
ZIP_PATH="${FLUXARA_DRIFT_DIR}/cmake_build/bin/FluxaraDrift-${PROJECT_VERSION}-switch.zip"
if [[ -f "${ZIP_PATH}" ]]; then
  rm "${ZIP_PATH}"
fi
zip -r "${ZIP_PATH}" .

# Recover old pwd
cd $OLD_PWD

echo "Done. Package available at ${ZIP_PATH}"
