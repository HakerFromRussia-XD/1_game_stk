// Fluxara Drift - iOS settings

#include "states_screens/fluxara_settings_screen.hpp"

#include "audio/music_manager.hpp"
#include "audio/sfx_manager.hpp"
#include "config/user_config.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"

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
    for (const char* id : {"back", "music", "sound"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<ButtonWidget>("back"), 21, 26, 50, 50);
    c.move(getWidget<ButtonWidget>("music"), 22, 105, 316, 105);
    c.move(getWidget<ButtonWidget>("sound"), 22, 235, 316, 105);
}

void FluxaraSettingsScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraSettingsScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    const auto label = [&c](const wchar_t* text, float x, float y,
                            float w, float h, float points,
                            irr::video::SColor color)
    {
        auto* font = GUIEngine::getTitleFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto sample = font->getDimension(L"M");
        font->setScale(points * c.scale / std::max(1u, sample.Height));
        const auto r = c.rect(x,y,w,h);
        auto shadow = r;
        shadow += irr::core::position2di(0,std::max(1,int(2*c.scale)));
        font->draw(text,shadow,irr::video::SColor(128,5,13,43),false,true);
        font->draw(text,r,color,false,true);
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
    c.image(m_art[5],21,26,50,50);
    c.image(m_art[6],32,36,25,31);
    label(L"SETTINGS",88,32,190,41,31,irr::video::SColor(255,255,255,255));
    for (int row = 0; row < 2; ++row)
    {
        const float y = row * 130.0f;
        const bool enabled = row == 0 ? bool(UserConfigParams::m_music)
                                      : bool(UserConfigParams::m_sfx);
        c.image(m_art[1],22,105+y,316,105);
        c.image(m_art[2],43,127+y,58,58);
        c.image(m_art[3+row],row == 0 ? 51 : 53,136+y,38,40);
        label(row == 0 ? L"MUSIC" : L"SOUND",117,128+y,110,30,20,
              irr::video::SColor(255,255,255,255));
        label(enabled ? L"ON" : L"OFF",118,157+y,120,20,13,
              irr::video::SColor(255,188,235,255));
        c.image(m_art[7],257,141+y,60,32);
        c.image(m_art[8],enabled ? 287 : 259,145+y,28,28);
    }
}

void FluxaraSettingsScreen::refreshLabels()
{
    // Visible labels are drawn from the live values in onDraw. Native widgets
    // provide interaction only, so their skin/text must stay suppressed.
    for (const char* id : {"back", "music", "sound"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
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
    // Persist immediately, including if iOS suspends before this screen closes.
    user_config->saveConfig();
}

bool FluxaraSettingsScreen::onEscapePressed()
{
    return true;
}
