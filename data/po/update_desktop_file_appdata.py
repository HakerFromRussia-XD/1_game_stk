#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys

def traslate_po(po, translation):
    search = 'msgid "' + translation + '"'
    idx = po.find(search)
    if idx == -1:
        return ''
    # 9 characters after msgid "xxx" for the translated message
    begin = idx + len(search) + 9
    # Search next " with newline
    end = po.find('"\n', begin)
    if end == -1:
        return ''
    return po[begin : end]

FLUXARA_DRIFT_DESCRIPTION = 'A 3D open-source kart racing game'
FLUXARA_DRIFT_DESKTOP_FILE_P1 = """[Desktop Entry]
"""
# Split it to avoid FluxaraDrift being translated
FLUXARA_DRIFT_DESKTOP_FILE_P2 = """Name=FluxaraDrift
Icon=fluxaradrift
StartupWMClass=fluxaradrift
"""
FLUXARA_DRIFT_DESKTOP_FILE_P3 = """#I18N: Generic name in desktop file entry, summary in AppData and short description in Google Play
GenericName=""" + FLUXARA_DRIFT_DESCRIPTION + """
Exec=fluxaradrift
Terminal=false
StartupNotify=false
Type=Application
Categories=Game;ArcadeGame;
#I18N: Keywords in desktop entry, translators please keep it separated with semicolons
Keywords=tux;game;race;
PrefersNonDefaultGPU=true
"""

desktop_file = open('fluxaradrift.desktop', 'w')
desktop_file.write(FLUXARA_DRIFT_DESKTOP_FILE_P1 + FLUXARA_DRIFT_DESKTOP_FILE_P3)
desktop_file.close()

FLUXARA_DRIFT_APPDATA_P1 = 'Karts. Nitro. Action! FluxaraDrift is a 3D open-source arcade racer \
with a variety of characters, tracks, and modes to play. \
Our aim is to create a game that is more fun than realistic, \
and provide an enjoyable experience for all ages.'
FLUXARA_DRIFT_APPDATA_P2 = 'We have several tracks with various themes for players to enjoy, \
from driving underwater, rural farmlands, jungles or even in space! \
Try your best while avoiding other karts as they may overtake you, \
but don\'t eat the bananas! Watch for bowling balls, plungers, bubble gum, \
and cakes thrown by your opponents.'
FLUXARA_DRIFT_APPDATA_P3 = 'You can do a single race against other karts, \
compete in one of several Grand Prix, \
try to beat the high score in time trials on your own, \
play battle mode against the computer or your friends, \
and more! For a greater challenge, join online and meet players from all over the world \
and prove your racing skills!'
# Used in google play only for now
FLUXARA_DRIFT_APPDATA_P4 = 'This game has no ads.'
# Used in google play beta only for now
FLUXARA_DRIFT_APPDATA_P5 = 'This is an unstable version of FluxaraDrift that contains latest improvements. \
It is released mainly for testing, to make stable FLUXARA_DRIFT as good as possible.'
FLUXARA_DRIFT_APPDATA_P6 = 'This version can be installed in parallel with the stable version on the device.'
FLUXARA_DRIFT_APPDATA_P7 = 'If you need more stability, consider using the stable version: %s'
FLUXARA_DRIFT_STABLE_URL = 'https://play.google.com/store/apps/details?id=org.fluxaradrift.fluxara_drift'

FLUXARA_DRIFT_APPDATA_FILE_1 = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<component type=\"desktop-application\">
  <id>net.fluxaradrift.FluxaraDrift</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0+</project_license>
  <launchable type="desktop-id">fluxaradrift.desktop</launchable>
"""
# Split it to avoid FluxaraDrift being translated
FLUXARA_DRIFT_APPDATA_FILE_2 = """  <name>FluxaraDrift</name>
"""
FLUXARA_DRIFT_APPDATA_FILE_3 = """  <summary>""" + FLUXARA_DRIFT_DESCRIPTION + """</summary>
  <description>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P1 + """
    </p>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P2 + """
    </p>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P3 + """
    </p>
"""
FLUXARA_DRIFT_APPDATA_FILE_4 = """    <p>
      """ + FLUXARA_DRIFT_APPDATA_P4 + """
    </p>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P5 + """
    </p>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P6 + """
    </p>
    <p>
      """ + FLUXARA_DRIFT_APPDATA_P7 + """
    </p>
"""
FLUXARA_DRIFT_APPDATA_FILE_5 = """  </description>
  <branding>
    <color type="primary" scheme_preference="light">#7c6e6e</color>
    <color type="primary" scheme_preference="dark">#392828</color>
  </branding>
  <screenshots>
    <screenshot type=\"default\">
      <image>https://fluxaradrift.net/assets/wiki/FLUXARA_DRIFT1.3_1.jpg</image>
      <caption>Normal Race</caption>
    </screenshot>
    <screenshot>
      <image>https://fluxaradrift.net/assets/wiki/FLUXARA_DRIFT1.3_5.jpg</image>
      <caption>Battle</caption>
    </screenshot>
    <screenshot>
      <image>https://fluxaradrift.net/assets/wiki/FLUXARA_DRIFT1.3_6.jpg</image>
      <caption>Soccer</caption>
    </screenshot>
  </screenshots>
  <developer_name>FluxaraDrift Team</developer_name>
  <update_contact>fluxaradrift-devel@lists.sourceforge.net</update_contact>
  <url type=\"homepage\">https://fluxaradrift.net</url>
  <url type=\"bugtracker\">https://github.com/fluxaradrift/fluxara_drift-code/issues</url>
  <url type=\"donation\">https://fluxaradrift.net/Donate</url>
  <url type=\"help\">https://fluxaradrift.net/Community</url>
  <url type=\"translate\">https://fluxaradrift.net/Translating_FLUXARA_DRIFT</url>
  <url type="faq">https://fluxaradrift.net/FAQ</url>
  <url type="vcs-browser">https://github.com/fluxaradrift/fluxara_drift-code</url>
  <url type="contribute">https://fluxaradrift.net/Community</url>
  <content_rating type=\"oars-1.1\">
    <content_attribute id=\"violence-cartoon\">mild</content_attribute>
    <content_attribute id=\"social-chat\">intense</content_attribute>
  </content_rating>
  <languages>
"""
FLUXARA_DRIFT_APPDATA_FILE_6 = """  </languages>
  <provides>
    <binary>fluxaradrift</binary>
  </provides>
  <supports>
    <control>pointing</control>
    <control>keyboard</control>
    <control>gamepad</control>
  </supports>
  <requires>
    <memory>1024</memory>
  </requires>
</component>
"""

appdata_file = open('net.fluxaradrift.FluxaraDrift.metainfo.xml', 'w')
appdata_file.write(FLUXARA_DRIFT_APPDATA_FILE_1 + FLUXARA_DRIFT_APPDATA_FILE_3 + FLUXARA_DRIFT_APPDATA_FILE_4 \
+ FLUXARA_DRIFT_APPDATA_FILE_5 + FLUXARA_DRIFT_APPDATA_FILE_6)
appdata_file.close()

os.system('xgettext -j -d fluxaradrift --add-comments=\"I18N:\" \
                    -p ./data/po -o fluxaradrift.pot \
                    --package-name=fluxaradrift fluxaradrift.desktop net.fluxaradrift.FluxaraDrift.metainfo.xml')

desktop_file = open('fluxaradrift.desktop', 'w')
desktop_file.write(FLUXARA_DRIFT_DESKTOP_FILE_P1 + FLUXARA_DRIFT_DESKTOP_FILE_P2 + FLUXARA_DRIFT_DESKTOP_FILE_P3)
desktop_file.close()

appdata = FLUXARA_DRIFT_APPDATA_FILE_1 + FLUXARA_DRIFT_APPDATA_FILE_2 + FLUXARA_DRIFT_APPDATA_FILE_3
# Skip google play message
appdata += FLUXARA_DRIFT_APPDATA_FILE_5

# Manually copy zh_TW to zh_HK for fallback
shutil.copyfile('./data/po/zh_TW.po', './data/po/zh_HK.po')
shutil.rmtree('./google_play_msg', ignore_errors = True)

lingas = open('./data/po/LINGUAS', 'w')
po_list = [f for f in os.listdir('./data/po/') if f.endswith('.po')]
po_list.sort(reverse = False);
fr_percentage = 0
for po_filename in po_list:
    po_file = open('./data/po/' + po_filename, 'r')
    po = po_file.read()
    po_file.close()
    # Remove all newlines in msgid
    po = po.replace('"\n"', '')

    cur_lang = po_filename.removesuffix('.po')
    if cur_lang != 'en':
        lingas.write(cur_lang + '\n')
        total_str = po.count('msgid "')
        untranslated_str = po.count('msgstr ""')
        translated_str = total_str - untranslated_str
        percentage = int(translated_str / total_str * 100.0)

        # Special handling for fr_CA, list has been sorted
        if cur_lang == 'fr':
            fr_percentage = percentage
        elif cur_lang == 'fr_CA':
            percentage = fr_percentage

        if percentage == 0:
            continue
        elif percentage != 100:
            appdata += '    <lang percentage="' + str(percentage) + '">' + cur_lang +'</lang>\n'
        else:
            appdata += '    <lang>' + cur_lang +'</lang>\n'

        if cur_lang != 'fr_CA' and len(sys.argv) == 2 and sys.argv[1] == '--generate-google-play-msg':
            desc = traslate_po(po, FLUXARA_DRIFT_DESCRIPTION)
            p1 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P1)
            p2 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P2)
            p3 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P3)
            p4 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P4)
            p5 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P5)
            p6 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P6)
            p7 = traslate_po(po, FLUXARA_DRIFT_APPDATA_P7)
            if desc and p1 and p2 and p3 and p4 and p5 and p6 and p7:
                os.makedirs('./google_play_msg/' + cur_lang)
                p7 = p7.replace('%s', FLUXARA_DRIFT_STABLE_URL)
                short = open('./google_play_msg/' + cur_lang + '/short.txt', 'w')
                short.write(desc)
                short.close()
                full = open('./google_play_msg/' + cur_lang + '/full.txt', 'w')
                full.write(p1 + '\n\n' + p2 + '\n\n' + p3 + '\n\n' + p4)
                full.close()
                full_beta = open('./google_play_msg/' + cur_lang + '/full_beta.txt', 'w')
                full_beta.write(p1 + '\n\n' + p2 + '\n\n' + p3 + '\n\n' + p4 +
                    '\n\n---\n\n' + p5 + '\n\n' + p6 + '\n\n' + p7)
                full_beta.close()

lingas.close()
appdata += FLUXARA_DRIFT_APPDATA_FILE_6
appdata_file = open('net.fluxaradrift.FluxaraDrift.metainfo.xml', 'w')
appdata_file.write(appdata)
appdata_file.close()

os.system('msgfmt --desktop -d data/po --template fluxaradrift.desktop -o data/fluxaradrift.desktop')
os.system('msgfmt --xml -d data/po --template net.fluxaradrift.FluxaraDrift.metainfo.xml -o data/net.fluxaradrift.FluxaraDrift.metainfo.xml')
os.remove('./fluxaradrift.desktop')
os.remove('./net.fluxaradrift.FluxaraDrift.metainfo.xml')
os.remove('./data/po/LINGUAS')
os.remove('./data/po/zh_HK.po')
