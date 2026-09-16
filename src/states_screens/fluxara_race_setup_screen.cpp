// Fluxara Drift - iOS race settings

#include "states_screens/fluxara_race_setup_screen.hpp"

#include "config/player_manager.hpp"
#include "config/user_config.hpp"
#include "graphics/stk_tex_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "race/race_manager.hpp"
#include "states_screens/fluxara_kart_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "tracks/track.hpp"

#include <algorithm>
#include <sstream>

using namespace GUIEngine;

FluxaraRaceSetupScreen::FluxaraRaceSetupScreen()
    : Screen("fluxara_race_setup.stkgui")
{
}

void FluxaraRaceSetupScreen::loadedFromFile()
{
}

void FluxaraRaceSetupScreen::setTrack(Track* track)
{
    m_track = track;
}

void FluxaraRaceSetupScreen::init()
{
    Screen::init();

    if (!m_track)
    {
        StateManager::get()->escapePressed();
        return;
    }

    getWidget<LabelWidget>("track-name")->setText(m_track->getName(), false);
    IconButtonWidget* preview = getWidget<IconButtonWidget>("track-preview");
    preview->setImage(STKTexManager::getInstance()->getTexture(
        m_track->getScreenshotFile(), "While loading Fluxara track preview:",
        m_track->getFilename()));
    preview->setFocusable(false);
    preview->m_tab_stop = false;

    RaceManager::get()->setMajorMode(RaceManager::MAJOR_MODE_SINGLE);
    RaceManager::get()->setMinorMode(RaceManager::MINOR_MODE_NORMAL_RACE);

    m_laps = std::max(1, std::min(9, m_track->getActualNumberOfLap()));
    const int saved_ai = int(UserConfigParams::m_num_karts_per_gamemode[
        RaceManager::MINOR_MODE_NORMAL_RACE]) - 1;
    m_ai_karts = std::max(1, std::min(7, saved_ai));
    updateRaceDetails();

    getWidget<ButtonWidget>("novice")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void FluxaraRaceSetupScreen::updateRaceDetails()
{
    std::ostringstream laps;
    laps << "Laps: " << m_laps;
    getWidget<ButtonWidget>("laps")->setText(
        core::stringw(laps.str().c_str()));

    std::ostringstream opponents;
    opponents << "Opponents: " << m_ai_karts;
    getWidget<ButtonWidget>("opponents")->setText(
        core::stringw(opponents.str().c_str()));
}

void FluxaraRaceSetupScreen::eventCallback(Widget*, const std::string& name,
                                           const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }

    if (name == "laps")
    {
        m_laps = m_laps >= 9 ? 1 : m_laps + 1;
        updateRaceDetails();
        return;
    }

    if (name == "opponents")
    {
        m_ai_karts = m_ai_karts >= 7 ? 1 : m_ai_karts + 1;
        updateRaceDetails();
        return;
    }

    RaceManager::Difficulty difficulty;
    if (name == "novice")
        difficulty = RaceManager::DIFFICULTY_EASY;
    else if (name == "standard")
        difficulty = RaceManager::DIFFICULTY_MEDIUM;
    else if (name == "expert")
        difficulty = RaceManager::DIFFICULTY_HARD;
    else
        return;

    RaceManager::get()->setMajorMode(RaceManager::MAJOR_MODE_SINGLE);
    RaceManager::get()->setMinorMode(RaceManager::MINOR_MODE_NORMAL_RACE);
    RaceManager::get()->setDifficulty(difficulty);
    UserConfigParams::m_difficulty = difficulty;
    RaceManager::get()->setNumLaps(m_laps);
    RaceManager::get()->setNumKarts(m_ai_karts + 1);
    UserConfigParams::m_num_laps = m_laps;
    UserConfigParams::m_num_karts_per_gamemode[
        RaceManager::MINOR_MODE_NORMAL_RACE] = m_ai_karts + 1;

    FluxaraKartScreen::getInstance()->setRace(m_track, m_laps,
                                               m_ai_karts + 1);
    FluxaraKartScreen::getInstance()->push();
}

bool FluxaraRaceSetupScreen::onEscapePressed()
{
    StateManager::get()->escapePressed();
    return true;
}
