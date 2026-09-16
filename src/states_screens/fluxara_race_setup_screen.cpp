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

    getWidget<ButtonWidget>("novice")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void FluxaraRaceSetupScreen::eventCallback(Widget*, const std::string& name,
                                           const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
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

    FluxaraKartScreen::getInstance()->setRace(m_track,
                                               m_track->getActualNumberOfLap());
    FluxaraKartScreen::getInstance()->push();
}

bool FluxaraRaceSetupScreen::onEscapePressed()
{
    StateManager::get()->escapePressed();
    return true;
}
