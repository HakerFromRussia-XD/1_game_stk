// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "guiengine/widgets/dynamic_ribbon_widget.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "states_screens/fluxara_race_setup_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "tracks/track.hpp"
#include "tracks/track_manager.hpp"

using namespace GUIEngine;

FluxaraCampaignScreen::FluxaraCampaignScreen()
    : Screen("fluxara_campaign.stkgui")
{
}

void FluxaraCampaignScreen::loadedFromFile()
{
}

void FluxaraCampaignScreen::init()
{
    Screen::init();

    DynamicRibbonWidget* cards = getWidget<DynamicRibbonWidget>("tracks");
    cards->clearItems();

    for (int i = 0; i < (int)track_manager->getNumberOfTracks(); ++i)
    {
        Track* track = track_manager->getTrack(i);
        if (track->isArena() || track->isSoccer() || track->isInternal())
            continue;

        cards->addItem(track->getName(), track->getIdent(),
                       track->getScreenshotFile(), 0,
                       IconButtonWidget::ICON_PATH_TYPE_ABSOLUTE);
    }

    cards->updateItemDisplay();
}

void FluxaraCampaignScreen::eventCallback(Widget* widget,
                                          const std::string& name,
                                          const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }

    if (name != "tracks")
        return;

    DynamicRibbonWidget* cards = dynamic_cast<DynamicRibbonWidget*>(widget);
    if (!cards)
        return;

    const std::string selection =
        cards->getSelectionIDString(PLAYER_ID_GAME_MASTER);
    if (selection == RibbonWidget::NO_ITEM_ID)
        return;

    Track* track = track_manager->getTrack(selection);
    if (!track)
        return;

    FluxaraRaceSetupScreen::getInstance()->setTrack(track);
    FluxaraRaceSetupScreen::getInstance()->push();
}

bool FluxaraCampaignScreen::onEscapePressed()
{
    StateManager::get()->escapePressed();
    return true;
}
