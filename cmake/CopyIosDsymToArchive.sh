#!/bin/sh
set -e

if [ -z "$ARCHIVE_DSYMS_PATH" ]; then
    exit 0
fi

if [ -z "$TARGET_BUILD_DIR" ] || [ -z "$FULL_PRODUCT_NAME" ]; then
    exit 0
fi

SOURCE_DSYM="$TARGET_BUILD_DIR/$FULL_PRODUCT_NAME.dSYM"
DESTINATION_DSYM="$ARCHIVE_DSYMS_PATH/$FULL_PRODUCT_NAME.dSYM"

if [ ! -d "$SOURCE_DSYM" ]; then
    exit 0
fi

mkdir -p "$ARCHIVE_DSYMS_PATH"
ditto "$SOURCE_DSYM" "$DESTINATION_DSYM"
