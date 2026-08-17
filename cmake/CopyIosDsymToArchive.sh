#!/bin/sh
set -e

if [ -z "$TARGET_BUILD_DIR" ] || [ -z "$FULL_PRODUCT_NAME" ]; then
    exit 0
fi

SOURCE_EXECUTABLE="$TARGET_BUILD_DIR/$EXECUTABLE_PATH"

# ARCHIVE_DSYMS_PATH is not exported by every Xcode/CMake archive invocation.
# Derive the archive's dSYMs directory from paths that Xcode does export so the
# symbol bundle is always included in the resulting .xcarchive.
if [ -n "$ARCHIVE_DSYMS_PATH" ]; then
    DSYMS_DIRECTORY="$ARCHIVE_DSYMS_PATH"
elif [ -n "$ARCHIVE_PRODUCTS_PATH" ]; then
    DSYMS_DIRECTORY="$(dirname "$ARCHIVE_PRODUCTS_PATH")/dSYMs"
elif [ "$ACTION" = "install" ] && [ -n "$DSTROOT" ] &&
     [ "$(basename "$DSTROOT")" = "InstallationBuildProductsLocation" ]; then
    # CMake overrides CONFIGURATION_BUILD_DIR, so Xcode generates the dSYM in
    # the repository instead of the ArchiveIntermediates product directory.
    # Place it where Xcode's archive collector expects installed symbols.
    DSYMS_DIRECTORY="$(dirname "$DSTROOT")/BuildProductsPath/${CONFIGURATION}${EFFECTIVE_PLATFORM_NAME}"
elif [ -n "$DSTROOT" ] && [ "$(basename "$DSTROOT")" = "Products" ]; then
    DSYMS_DIRECTORY="$(dirname "$DSTROOT")/dSYMs"
elif [ -n "$INSTALL_ROOT" ] && [ "$(basename "$INSTALL_ROOT")" = "Products" ]; then
    DSYMS_DIRECTORY="$(dirname "$INSTALL_ROOT")/dSYMs"
elif [ -n "$DWARF_DSYM_FOLDER_PATH" ] &&
     echo "$DWARF_DSYM_FOLDER_PATH" | grep -q '\.xcarchive/'; then
    DSYMS_DIRECTORY="$DWARF_DSYM_FOLDER_PATH"
else
    exit 0
fi

DESTINATION_DSYM="$DSYMS_DIRECTORY/$FULL_PRODUCT_NAME.dSYM"

if [ ! -f "$SOURCE_EXECUTABLE" ]; then
    exit 0
fi

# CMake's post-build rule runs before Xcode's own GenerateDSYMFile step. Build
# symbols from this exact executable, rather than reusing a possibly stale
# Release-iphoneos dSYM left by a previous archive.
DSYM_TEMP_DIR="$(mktemp -d "$TARGET_TEMP_DIR/motorica-dsym.XXXXXX")"
trap 'rm -rf "$DSYM_TEMP_DIR"' EXIT
SOURCE_DSYM="$DSYM_TEMP_DIR/$FULL_PRODUCT_NAME.dSYM"
/usr/bin/dsymutil "$SOURCE_EXECUTABLE" -o "$SOURCE_DSYM"

mkdir -p "$DSYMS_DIRECTORY"
ditto "$SOURCE_DSYM" "$DESTINATION_DSYM"
