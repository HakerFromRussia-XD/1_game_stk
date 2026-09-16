// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "graphics/stk_tex_manager.hpp"
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

    m_tracks.clear();

    for (int i = 0; i < (int)track_manager->getNumberOfTracks(); ++i)
    {
        Track* track = track_manager->getTrack(i);
        if (track->isArena() || track->isSoccer() || track->isInternal())
            continue;

        m_tracks.push_back(track->getIdent());
    }

    m_selected_track = 0;
    updateTrackCard();
}

void FluxaraCampaignScreen::updateTrackCard()
{
    if (m_tracks.empty())
    {
        getWidget<LabelWidget>("track-name")->setText("No circuit available",
                                                        false);
        return;
    }

    Track* track = track_manager->getTrack(m_tracks[m_selected_track]);
    if (!track)
        return;

    getWidget<LabelWidget>("track-name")->setText(track->getName(), false);
    IconButtonWidget* preview = getWidget<IconButtonWidget>("track-preview");
    preview->setImage(STKTexManager::getInstance()->getTexture(
        track->getScreenshotFile(), "While loading Fluxara track card:",
        track->getFilename()));
    preview->setFocusable(false);
    preview->m_tab_stop = false;
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

    if (name == "previous" && !m_tracks.empty())
    {
        m_selected_track = m_selected_track == 0 ?
            unsigned(m_tracks.size() - 1) : m_selected_track - 1;
        updateTrackCard();
        return;
    }

    if (name == "next" && !m_tracks.empty())
    {
        m_selected_track = (m_selected_track + 1) % unsigned(m_tracks.size());
        updateTrackCard();
        return;
    }

    if (name != "choose" || m_tracks.empty())
        return;

    Track* track = track_manager->getTrack(m_tracks[m_selected_track]);
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
