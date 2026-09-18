//  Fluxara Drift - public iOS racing campaign home

#include "states_screens/fluxara_home_screen.hpp"

#include "config/player_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/fluxara_campaign_screen.hpp"
#include "states_screens/fluxara_kart_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "states_screens/fluxara_settings_screen.hpp"
#include "states_screens/state_manager.hpp"

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
    const char* files[] = {"home-background", "home-logo", "button-garage",
        "button-play", "button-settings", "icon-play", "icon-garage", "icon-settings"};
    for (int i = 0; i < 8; ++i)
        m_art[i] = FluxaraUI::texture(std::string("home/") + files[i]);
    layoutControls();
    getWidget<ButtonWidget>("campaign")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void FluxaraHomeScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"campaign", "garage", "settings"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<ButtonWidget>("campaign"), 28, 563, 304, 95);
    c.move(getWidget<ButtonWidget>("garage"), 83, 651, 109, 109);
    c.move(getWidget<ButtonWidget>("settings"), 189, 647, 109, 109);
}

void FluxaraHomeScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraHomeScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    c.image(m_art[0], 0, 0, 360, 780, true);
    c.image(m_art[1], 10, 77, 340, 204);
    c.image(m_art[2], 83, 651, 109, 109);
    c.image(m_art[3], 28, 563, 304, 109);
    c.image(m_art[4], 189, 647, 109, 109);
    c.image(m_art[5], 114, 586, 43, 48);
    c.image(m_art[6], 111, 671, 54, 46);
    c.image(m_art[7], 222, 674, 51, 46);
    c.label(L"PLAY", 139, 588, 130, 34, 27);
    c.label(L"GARAGE", 93, 709, 89, 18, 12);
    c.label(L"SETTINGS", 202, 711, 91, 18, 11);
}

void FluxaraHomeScreen::eventCallback(Widget*, const std::string& name,
                                      const int)
{
    if (name == "campaign")
        FluxaraCampaignScreen::getInstance()->push();
    else if (name == "garage")
    {
        FluxaraKartScreen::getInstance()->setRace(nullptr, 3, 4);
        FluxaraKartScreen::getInstance()->push();
    }
    else if (name == "settings")
        FluxaraSettingsScreen::getInstance()->push();
}

bool FluxaraHomeScreen::onEscapePressed()
{
    return false;
}
