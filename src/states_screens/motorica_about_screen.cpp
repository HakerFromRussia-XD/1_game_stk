//  Motorica Kart product and open-source information

#include "states_screens/motorica_about_screen.hpp"

#include "online/link_helper.hpp"
#include "states_screens/credits.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/string_utils.hpp"

using namespace GUIEngine;

namespace
{
const char* MOTORICA_SOURCE_URL =
    "https://github.com/HakerFromRussia-XD/1_game_stk";
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

    getWidget("about_description")->setText(StringUtils::utf8ToWide(
        "Motorica Kart — постоянный игровой модуль для тренировки управления. "
        "При запуске из Motorica Start он принимает сигналы совместимого "
        "устройства. Проект основан на открытом исходном коде SuperTuxKart; "
        "лицензии и авторство исходного проекта сохранены."));
    getWidget("source")->setText(StringUtils::utf8ToWide(
        "Исходный код проекта"));
    getWidget("credits")->setText(StringUtils::utf8ToWide(
        "Лицензии и авторы"));

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
    else if (name == "credits")
    {
        CreditsScreen::getInstance()->reset();
        CreditsScreen::getInstance()->push();
    }
}
