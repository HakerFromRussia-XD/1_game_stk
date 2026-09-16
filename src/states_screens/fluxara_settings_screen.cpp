// Fluxara Drift - iOS settings

#include "states_screens/fluxara_settings_screen.hpp"

#include "audio/music_manager.hpp"
#include "audio/sfx_manager.hpp"
#include "config/user_config.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/state_manager.hpp"

using namespace GUIEngine;

FluxaraSettingsScreen::FluxaraSettingsScreen()
    : Screen("fluxara_settings.stkgui")
{
}

void FluxaraSettingsScreen::loadedFromFile()
{
}

void FluxaraSettingsScreen::init()
{
    Screen::init();
    refreshLabels();
    getWidget<ButtonWidget>("music")->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}

void FluxaraSettingsScreen::tearDown()
{
    Screen::tearDown();
    user_config->saveConfig();
}

void FluxaraSettingsScreen::refreshLabels()
{
    getWidget<ButtonWidget>("music")->setLabel(
        UserConfigParams::m_music ? "Music: On" : "Music: Off");
    getWidget<ButtonWidget>("sound")->setLabel(
        UserConfigParams::m_sfx ? "Sound effects: On" : "Sound effects: Off");
}

void FluxaraSettingsScreen::eventCallback(Widget*, const std::string& name,
                                          const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }

    if (name == "music")
    {
        UserConfigParams::m_music = !UserConfigParams::m_music;
        if (UserConfigParams::m_music)
            music_manager->startMusic();
        else
            music_manager->stopMusic();
    }
    else if (name == "sound")
    {
        UserConfigParams::m_sfx = !UserConfigParams::m_sfx;
        SFXManager::get()->toggleSound(UserConfigParams::m_sfx);
    }
    else
    {
        return;
    }

    refreshLabels();
}

bool FluxaraSettingsScreen::onEscapePressed()
{
    StateManager::get()->escapePressed();
    return true;
}
