// Fluxara Drift - iOS settings

#include "states_screens/fluxara_settings_screen.hpp"

#include "audio/music_manager.hpp"
#include "audio/sfx_manager.hpp"
#include "config/user_config.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/fluxara_home_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

#include <algorithm>
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
    const char* files[] = {"background", "card", "iconbase", "music",
                          "sound", "back", "backicon", "toggle", "knob"};
    for (int i = 0; i < 9; ++i)
        m_art[i] = FluxaraUI::texture(std::string("settings/") + files[i]);
    layoutControls();
    refreshLabels();
    getWidget<ButtonWidget>("music")->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}

void FluxaraSettingsScreen::tearDown()
{
    Screen::tearDown();
    user_config->saveConfig();
}

void FluxaraSettingsScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"back", "music", "sound", "controls",
                           "auto_accel", "difficulty"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<ButtonWidget>("back"), 21, 58, 50, 50);
    c.move(getWidget<ButtonWidget>("music"), 250, 163, 76, 52);
    c.move(getWidget<ButtonWidget>("sound"), 250, 293, 76, 52);
    // Figma settings cards start at y=105 and y=235.  Preserve that 25 px
    // breathing space for every extra live setting rather than compressing
    // the extended controls into the two-card reference layout.
    c.move(getWidget<ButtonWidget>("controls"), 22, 397, 316, 105);
    c.move(getWidget<ButtonWidget>("auto_accel"), 22, 527, 316, 105);
    c.move(getWidget<ButtonWidget>("difficulty"), 22, 657, 316, 105);
}

void FluxaraSettingsScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraSettingsScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    const auto label = [&c](const irr::core::stringw& text, float x, float y,
                            float w, float h, float points,
                            irr::video::SColor color)
    {
        auto* font = GUIEngine::getFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto sample = font->getDimension(L"M");
        font->setScale(points * c.scale / std::max(1u, sample.Height));
        const auto r = c.rect(x,y,w,h);
        auto shadow = r;
        shadow += irr::core::position2di(0,std::max(1,int(2*c.scale)));
        font->draw(text.c_str(),shadow,irr::video::SColor(128,5,13,43),false,true);
        font->draw(text.c_str(),r,color,false,true);
        font->setScale(saved);
    };
    GL32_draw2DRectangle(irr::video::SColor(255,16,53,126), c.rect(0,0,360,780));
    if (m_art[0])
    {
        const auto size = m_art[0]->getSize();
        draw2DImage(m_art[0], c.rect(0,0,360,780),
            irr::core::recti(0,0,size.Width,size.Height), nullptr,
            irr::video::SColor(77,255,255,255), true);
    }
    c.image(m_art[5],21,58,50,50);
    c.image(m_art[6],32,68,25,31);
    label(_C("fluxara", "SETTINGS"),88,69,190,38,31,irr::video::SColor(255,255,255,255));
    for (int row = 0; row < 2; ++row)
    {
        const float y = 32.0f + row * 130.0f;
        const bool enabled = row == 0 ? bool(UserConfigParams::m_music)
                                      : bool(UserConfigParams::m_sfx);
        c.image(m_art[1],22,105+y,316,105);
        c.image(m_art[2],43,127+y,58,58);
        c.image(m_art[3+row],row == 0 ? 51 : 53,136+y,38,40);
        label(row == 0 ? _C("fluxara", "MUSIC") : _C("fluxara", "SOUND"),117,128+y,110,30,20,
              irr::video::SColor(255,255,255,255));
        label(enabled ? _C("fluxara", "ON") : _C("fluxara", "OFF"),118,157+y,110,20,13,
              irr::video::SColor(255,188,235,255));
        c.image(m_art[7],257,141+y,60,32);
        c.image(m_art[8],enabled ? 287 : 259,141+y,28,28);
    }

    const bool wheel = int(UserConfigParams::m_multitouch_controls) ==
                       MULTITOUCH_CONTROLS_STEERING_WHEEL;
    const bool auto_accel = wheel &&
                            bool(UserConfigParams::m_multitouch_auto_acceleration);
    const int difficulty = std::max(0, std::min(2,
        int(UserConfigParams::m_difficulty)));
    const irr::core::stringw difficulty_names[] = {_C("fluxara", "NOVICE"), _C("fluxara", "STANDARD"), _C("fluxara", "EXPERT")};
    const irr::core::stringw row_titles[] = {_C("fluxara", "CONTROLS"), _C("fluxara", "AUTO DRIVE"), _C("fluxara", "DIFFICULTY")};
    const irr::core::stringw row_values[] = {
        wheel ? _C("fluxara", "STEERING WHEEL") : _C("fluxara", "TILT"),
        auto_accel ? _C("fluxara", "ON") : _C("fluxara", "OFF"),
        difficulty_names[difficulty]
    };
    const wchar_t* row_icons[] = {L"<>" , L"A", L"AI"};

    for (int row = 0; row < 3; ++row)
    {
        const float y = 397.0f + row * 130.0f;
        const bool dimmed = row == 1 && !wheel;
        c.image(m_art[1],22,y,316,105,false,dimmed ? 185 : 255);
        c.image(m_art[2],43,y+22,58,58,false,dimmed ? 185 : 255);
        c.label(row_icons[row],47,y+31,50,40,row == 0 ? 18 : 15);
        label(row_titles[row],117,y+24,125,30,18,
              irr::video::SColor(dimmed ? 170 : 255,255,255,255));
        label(row_values[row],118,y+55,176,23,13,
              irr::video::SColor(dimmed ? 150 : 255,188,235,255));
        if (row == 1)
        {
            c.image(m_art[7],257,y+37,60,32,false,dimmed ? 120 : 255);
            c.image(m_art[8],auto_accel ? 287 : 259,y+39,28,28,false,
                    dimmed ? 120 : 255);
        }
        else
        {
            label(L">",298,y+38,22,30,19,
                  irr::video::SColor(dimmed ? 120 : 255,255,255,255));
        }
    }
}

void FluxaraSettingsScreen::refreshLabels()
{
    // Visible labels are drawn from the live values in onDraw. Native widgets
    // provide interaction only, so their skin/text must stay suppressed.
    for (const char* id : {"back", "music", "sound", "controls",
                           "auto_accel", "difficulty"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));

    getWidget<ButtonWidget>("auto_accel")->setActive(
        int(UserConfigParams::m_multitouch_controls) ==
        MULTITOUCH_CONTROLS_STEERING_WHEEL);
}

void FluxaraSettingsScreen::eventCallback(Widget*, const std::string& name,
                                          const int)
{
    if (name == "back")
    {
        // Settings is a valid direct-launch destination; its Back action
        // must not pop the only menu screen and exit to SpringBoard.
        StateManager::get()->resetAndGoToScreen(
            FluxaraHomeScreen::getInstance());
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
    else if (name == "controls")
    {
        if (int(UserConfigParams::m_multitouch_controls) ==
            MULTITOUCH_CONTROLS_STEERING_WHEEL)
        {
            UserConfigParams::m_multitouch_controls =
                MULTITOUCH_CONTROLS_ACCELEROMETER;
            UserConfigParams::m_multitouch_auto_acceleration = false;
        }
        else
        {
            UserConfigParams::m_multitouch_controls =
                MULTITOUCH_CONTROLS_STEERING_WHEEL;
        }
    }
    else if (name == "auto_accel")
    {
        UserConfigParams::m_multitouch_auto_acceleration =
            !UserConfigParams::m_multitouch_auto_acceleration;
    }
    else if (name == "difficulty")
    {
        UserConfigParams::m_difficulty =
            (std::max(0, std::min(2, int(UserConfigParams::m_difficulty))) + 1) % 3;
    }
    else
    {
        return;
    }

    refreshLabels();
    // Persist immediately, including if iOS suspends before this screen closes.
    user_config->saveConfig();
}

bool FluxaraSettingsScreen::onEscapePressed()
{
    return true;
}
