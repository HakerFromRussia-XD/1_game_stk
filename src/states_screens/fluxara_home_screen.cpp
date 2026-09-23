//  Fluxara Drift - public iOS racing campaign home

#include "states_screens/fluxara_home_screen.hpp"

#include "config/player_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/fluxara_campaign_screen.hpp"
#include "states_screens/fluxara_kart_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "states_screens/fluxara_settings_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

using namespace GUIEngine;

FluxaraHomeScreen::FluxaraHomeScreen()
    : Screen("fluxara_home.fluxara_driftgui")
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
    // Match the full Figma 19:2 coral surface; the lower rounded part is
    // visible and must be tappable too.
    c.move(getWidget<ButtonWidget>("campaign"), 28, 563, 304, 109);
    // Centre the pair as one visual group.  The prior Figma-export bounds
    // carried a right-side crop, which made the two visible controls appear
    // 12 px too far to the right on device.
    c.move(getWidget<ButtonWidget>("garage"), 71, 651, 109, 109);
    c.move(getWidget<ButtonWidget>("settings"), 177, 647, 109, 109);
}

void FluxaraHomeScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraHomeScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    if (!c.isStable())
    {
        FluxaraUI::transitionBackdrop(m_art[0]);
        return;
    }
    c.image(m_art[0], 0, 0, 360, 780, true);
    c.image(m_art[1], 10, 77, 340, 204);
    c.image(m_art[2], 71, 651, 109, 109);
    c.image(m_art[3], 28, 563, 304, 109);
    c.image(m_art[4], 177, 647, 109, 109);
    c.image(m_art[5], 114, 586, 43, 48);
    c.image(m_art[6], 99, 671, 54, 46);
    c.image(m_art[7], 210, 674, 51, 46);
    c.label(_C("fluxara", "PLAY"), 139, 588, 130, 34, 27);
    c.label(_C("fluxara", "GARAGE"), 81, 709, 89, 18, 12);
    c.label(_C("fluxara", "SETTINGS"), 190, 711, 91, 18, 11);
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
