//  Motorica Kart standalone product hub

#include "states_screens/motorica_hub_screen.hpp"

#include "config/player_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "modes/overworld.hpp"
#include "states_screens/motorica_about_screen.hpp"
#include "states_screens/dialogs/message_dialog.hpp"
#include "states_screens/dialogs/download_assets.hpp"
#include "states_screens/options/options_screen_general.hpp"
#include "utils/extract_mobile_assets.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"
#ifdef IOS_STK
#include "input/motorica_game_control_ios.hpp"
#endif

using namespace GUIEngine;

MotoricaHubScreen::MotoricaHubScreen()
    : Screen("motorica_hub.stkgui")
{
}

void MotoricaHubScreen::loadedFromFile()
{
}

void MotoricaHubScreen::init()
{
    Screen::init();
    getWidget<ButtonWidget>("play")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void MotoricaHubScreen::eventCallback(Widget*, const std::string& name,
                                      const int)
{
    if (name == "play")
    {
#ifdef IOS_STK
        if (isMotoricaGameControlEnabledIOS() &&
            !ExtractMobileAssets::isFullAssetsInstalled())
        {
            new DownloadAssets();
            return;
        }
#endif
        PlayerManager::get()->enforceCurrentPlayer();
        OverWorld::enterOverWorld();
    }
    else if (name == "controls")
    {
        new MessageDialog(_(
            "Поворачивайте экранным рулём или наклоном устройства. "
            "Для ускорения и торможения используйте экранные педали. "
            "При запуске из Motorica Start источником управления становятся "
            "сигналы совместимого устройства."));
    }
    else if (name == "motorica_start")
    {
        new MessageDialog(_(
            "Подключите совместимое устройство в Motorica Start, дождитесь "
            "поступления сигналов и откройте Motorica Kart из раздела игр. "
            "В этом режиме сохраняются управление сигналами и пауза при "
            "потере соединения."));
    }
    else if (name == "settings")
    {
        OptionsScreenGeneral::getInstance()->push();
    }
    else if (name == "about")
    {
        MotoricaAboutScreen::getInstance()->push();
    }
}

bool MotoricaHubScreen::onEscapePressed()
{
    return false;
}
