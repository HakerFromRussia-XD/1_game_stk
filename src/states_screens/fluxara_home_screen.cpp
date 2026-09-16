//  Fluxara Drift - public iOS racing campaign home

#include "states_screens/fluxara_home_screen.hpp"

#include "config/player_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/options/options_screen_general.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/tracks_and_gp_screen.hpp"

using namespace GUIEngine;

FluxaraHomeScreen::FluxaraHomeScreen()
    : Screen("fluxara_home.stkgui")
{
}

void FluxaraHomeScreen::loadedFromFile()
{
}

void FluxaraHomeScreen::init()
{
    Screen::init();
    getWidget<ButtonWidget>("campaign")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void FluxaraHomeScreen::eventCallback(Widget*, const std::string& name,
                                      const int)
{
    if (name == "campaign")
        TracksAndGPScreen::getInstance()->push();
    else if (name == "settings")
        OptionsScreenGeneral::getInstance()->push();
}

bool FluxaraHomeScreen::onEscapePressed()
{
    return false;
}
