//  Motorica Kart product and open-source information

#include "states_screens/motorica_about_screen.hpp"

#include "online/link_helper.hpp"
#include "states_screens/dialogs/message_dialog.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

#include "SDL_clipboard.h"

using namespace GUIEngine;

namespace
{
const char* MOTORICA_SOURCE_URL =
    "https://github.com/HakerFromRussia-XD/1_game_stk";

bool useRussian()
{
    if (translations == nullptr)
        return false;
    const std::string code = translations->getCurrentLanguageNameCode();
    return code == "ru" || code.find("ru_") == 0 || code.find("ru-") == 0;
}

core::stringw localized(const char* russian, const char* english)
{
    return StringUtils::utf8ToWide(useRussian() ? russian : english);
}
}

MotoricaAboutScreen::MotoricaAboutScreen()
    : Screen("motorica_about.stkgui")
{
}

void MotoricaAboutScreen::loadedFromFile()
{
}

void MotoricaAboutScreen::init()
{
    Screen::init();

    getWidget("about_description")->setText(localized(
        "Motorica Signal Lab — самостоятельный тренажёр точности, реакции "
        "и удержания сигнала. Motorica Kart основан на открытом исходном "
        "коде SuperTuxKart; лицензии и авторство исходного проекта сохранены.",
        "Motorica Signal Lab is a standalone trainer for precision, reaction "
        "and signal holding. Motorica Kart is based on the open-source "
        "SuperTuxKart project; its licenses and attribution are preserved."));
    getWidget("source")->setText(localized(
        "Открыть исходный код проекта", "Open Project Source Code"));
    getWidget("copy_source")->setText(localized(
        "Скопировать адрес репозитория", "Copy Repository URL"));

    getWidget("source")->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}

void MotoricaAboutScreen::eventCallback(Widget*, const std::string& name,
                                        const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
    }
    else if (name == "source")
    {
        Online::LinkHelper::openURL(MOTORICA_SOURCE_URL);
    }
    else if (name == "copy_source")
    {
        if (SDL_SetClipboardText(MOTORICA_SOURCE_URL) == 0)
        {
            new MessageDialog(localized(
                "Адрес репозитория скопирован.",
                "The repository URL was copied."));
        }
        else
        {
            new MessageDialog(StringUtils::utf8ToWide(MOTORICA_SOURCE_URL));
        }
    }
}
