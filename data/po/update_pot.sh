# run this script from the root directory to re-generate the .pot file
#
# ./data/po/update_pot.sh
if [ -z "$PYTHON" ]; then
  PYTHON="python"
fi

CPP_FILE_LIST="`find ./src                 \
                     -name '*.cpp' -or     \
                     -name '*.c' -or       \
                     -name '*.hpp' -or     \
                     -name "*.h" | sort -n \
              `"
XML_FILE_LIST="`find ./data                        \
                     ../fluxara_drift-assets/tracks          \
                     ../fluxara_drift-assets/karts           \
                     ../fluxaradrift-assets/tracks \
                     ../fluxaradrift-assets/karts  \
                     ./android/res/values          \
                     -name 'achievements.xml' -or  \
                     -name 'skin_names.xml' -or    \
                     -name 'tips.xml' -or          \
                     -name 'kart.xml' -or          \
                     -name 'track.xml' -or         \
                     -name 'scene.xml' -or         \
                     -name '*.challenge' -or       \
                     -name '*.grandprix' -or       \
                     -name 'strings.xml' -or       \
                     -name '*.fluxara_driftgui' | sort -n    \
              `"
ANGELSCRIPT_FILE_LIST="`find ./data                        \
                             ../fluxara_drift-assets/tracks          \
                             ../fluxaradrift-assets/tracks \
                             -name '*.as' | sort -n        \
                      `"

echo "--------------------"
echo "    Source Files :"
echo "--------------------"
echo $CPP_FILE_LIST
echo $ANGELSCRIPT_FILE_LIST

echo "--------------------"
echo "    XML Files :"
echo "--------------------"
echo $XML_FILE_LIST

# XML Files
eval '$PYTHON ./data/po/extract_strings_from_XML.py $XML_FILE_LIST'



echo "---------------------------"
echo "    Generating .pot file..."

# XML Files
xgettext  -d fluxaradrift --keyword=_ --add-comments="I18N:" \
                               -p ./data/po -o fluxaradrift.pot \
                               --no-location --from-code=UTF-8 ./data/po/gui_strings.h \
                               --package-name=fluxaradrift

# C++ Files
xgettext  -j  -d fluxaradrift --keyword=_ --keyword=N_ --keyword=_LTR \
                               --keyword=_C:1c,2 --keyword=_P:1,2 \
                               --keyword=_CP:1c,2,3 --add-comments="I18N:" \
                               -p ./data/po -o fluxaradrift.pot $CPP_FILE_LIST \
                               --package-name=fluxaradrift

# Angelscript files (xgettext doesn't support AS so pretend it's c++)
xgettext  -j  -d fluxaradrift --keyword="translate" --add-comments="I18N:" \
                               -p ./data/po -o fluxaradrift.pot $ANGELSCRIPT_FILE_LIST \
                               --package-name=fluxaradrift --language=c++

# Desktop file and AppData
if [ "$1" = "--generate-google-play-msg" ]; then
    data/po/update_desktop_file_appdata.py "--generate-google-play-msg"
else
    data/po/update_desktop_file_appdata.py
fi

echo "    Done"
echo "---------------------------"
