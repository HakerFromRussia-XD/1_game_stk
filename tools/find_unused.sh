#!/bin/bash

echo "Searching for unused fluxara_driftgui files"
echo "---------------------------------"
cd data/gui
l=""
for i in $(find . -iname "*.fluxara_driftgui"); do
    s=$(basename $i)
    x=$(find ../../src/states_screens -type f -exec grep -H $s \{} \; | wc -l)
    echo -n "."
    if [ $x == "0" ]; then
        l="$l $i"
    fi
done
echo

for i in $l; do
    echo "$i appears to be not used."
done

echo "done"



