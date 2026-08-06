#!/bin/sh
set -e

if [ -z "$TARGET_BUILD_DIR" ] || [ -z "$FULL_PRODUCT_NAME" ]; then
    exit 0
fi

SOURCE_DSYM="$TARGET_BUILD_DIR/$FULL_PRODUCT_NAME.dSYM"

# ARCHIVE_DSYMS_PATH is not exported by every Xcode/CMake archive invocation.
# Derive the archive's dSYMs directory from paths that Xcode does export so the
# symbol bundle is always included in the resulting .xcarchive.
if [ -n "$ARCHIVE_DSYMS_PATH" ]; then
    DSYMS_DIRECTORY="$ARCHIVE_DSYMS_PATH"
elif [ -n "$ARCHIVE_PRODUCTS_PATH" ]; then
    DSYMS_DIRECTORY="$(dirname "$ARCHIVE_PRODUCTS_PATH")/dSYMs"
elif [ -n "$INSTALL_ROOT" ] && [ "$(basename "$INSTALL_ROOT")" = "Products" ]; then
    DSYMS_DIRECTORY="$(dirname "$INSTALL_ROOT")/dSYMs"
else
    exit 0
fi

DESTINATION_DSYM="$DSYMS_DIRECTORY/$FULL_PRODUCT_NAME.dSYM"

if [ ! -d "$SOURCE_DSYM" ]; then
    exit 0
fi

mkdir -p "$DSYMS_DIRECTORY"
ditto "$SOURCE_DSYM" "$DESTINATION_DSYM"
