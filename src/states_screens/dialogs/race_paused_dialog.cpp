//  FluxaraDrift - a fun racing game with go-kart
//  Copyright (C) 2010-2015 Marianne Gagnon
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 3
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#include "states_screens/dialogs/race_paused_dialog.hpp"

#include <algorithm>
#include <cmath>
#include <string>

#include "audio/music_manager.hpp"
#include "audio/sfx_manager.hpp"
#include "challenges/story_mode_timer.hpp"
#include "config/user_config.hpp"
#include "graphics/irr_driver.hpp"
#include "guiengine/emoji_keyboard.hpp"
#include "guiengine/engine.hpp"
#include "guiengine/layout_manager.hpp"
#include "guiengine/scalable_font.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/CGUIEditBox.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/ribbon_widget.hpp"
#include "io/file_manager.hpp"
#include "karts/controller/controller.hpp"
#include "karts/kart.hpp"
#include "modes/overworld.hpp"
#include "modes/world.hpp"
#include "network/protocols/client_lobby.hpp"
#include "network/network_config.hpp"
#include "network/network_string.hpp"
#include "network/fluxara_drift_host.hpp"
#include "race/race_manager.hpp"
#include "states_screens/help/help_screen_1.hpp"
#include "states_screens/main_menu_screen.hpp"
#include "states_screens/race_gui_base.hpp"
#include "states_screens/race_gui_multitouch.hpp"
#include "states_screens/race_setup_screen.hpp"
#include "states_screens/options/options_screen_general.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"
#ifdef IOS_FLUXARA_DRIFT
#include "input/motorica_game_control_ios.hpp"
#include "input/motorica_standalone_training.hpp"
#include "states_screens/fluxara_home_screen.hpp"
#include "states_screens/fluxara_settings_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#endif

#include <IrrlichtDevice.h>
#include <IGUIEnvironment.h>
#include <IGUIElement.h>
#include <IVideoDriver.h>

#ifndef SERVER_ONLY
#include <ge_main.hpp>
#include <ge_vulkan_driver.hpp>
#endif

using namespace GUIEngine;
using namespace irr::core;
using namespace irr::gui;

#ifdef IOS_FLUXARA_DRIFT
namespace
{
// Fluxara's pause artwork and hit frames are defined on the complete 844 x
// 390 race viewport.  The inherited pause dialog is only 80 x 60 percent of
// that viewport, which clips native child buttons at its edges.  Keep every
// other inherited dialog size untouched; only the local Fluxara race pause
// receives a full-screen input container.
bool useFluxaraFullscreenPauseContainer()
{
    return World::getWorld() != nullptr &&
           dynamic_cast<OverWorld*>(World::getWorld()) == nullptr &&
           !NetworkConfig::get()->isNetworking();
}

// Keep the pause menu's control selector on exactly the same three-mode cycle
// as the inherited pause ribbon.  The chosen value is committed and the HUD
// recreated when this dialog closes.
void cycleTouchControls(int& controls)
{
    if (controls == MULTITOUCH_CONTROLS_STEERING_WHEEL)
        controls = MULTITOUCH_CONTROLS_ACCELEROMETER;
    else if (controls == MULTITOUCH_CONTROLS_ACCELEROMETER)
        controls = MULTITOUCH_CONTROLS_GYROSCOPE;
    else
        controls = MULTITOUCH_CONTROLS_STEERING_WHEEL;
}

irr::core::stringw controlModeLabel(int controls)
{
    switch (controls)
    {
    case MULTITOUCH_CONTROLS_ACCELEROMETER:
        return _C("fluxara", "TILT");
    case MULTITOUCH_CONTROLS_GYROSCOPE:
        return _C("fluxara", "GYROSCOPE");
    case MULTITOUCH_CONTROLS_UNDEFINED:
    case MULTITOUCH_CONTROLS_STEERING_WHEEL:
    default:
        return _C("fluxara", "STEERING WHEEL");
    }
}

/**
 * The game already renders the live track and HUD underneath a ModalDialog.
 * This child is deliberately only the translucent veil and Figma's pause
 * layers; it never replaces the running race with a precomposed screenshot.
 */
class FluxaraPauseVisual final : public IGUIElement
{
private:
    irr::video::ITexture* m_art[13];
    const int* m_touch_controls;

    static constexpr float kWidth = 844.0f;
    static constexpr float kHeight = 390.0f;

    irr::core::recti rect(float x, float y, float w, float h) const
    {
        const auto size = irr_driver->getActualScreenSize();
        const float scale = std::min(size.Width / kWidth, size.Height / kHeight);
        const float left = (size.Width - kWidth * scale) * 0.5f;
        const float top = (size.Height - kHeight * scale) * 0.5f;
        return irr::core::recti(int(std::lround(left + x * scale)),
            int(std::lround(top + y * scale)),
            int(std::lround(left + (x + w) * scale)),
            int(std::lround(top + (y + h) * scale)));
    }

    void image(int index, float x, float y, float w, float h) const
    {
        auto* texture = m_art[index];
        if (!texture) return;
        const auto source = texture->getSize();
        draw2DImage(texture, rect(x, y, w, h),
                    irr::core::recti(0, 0, source.Width, source.Height),
                    nullptr, irr::video::SColor(255, 255, 255, 255), true);
    }

    // Match Figma's object-cover exactly.  The yellow pause surface is a
    // square source but its Figma frame is rectangular; drawing the full
    // square stretches its bevels.  Crop the source centrally before the
    // scale, preserving the original button geometry.
    void imageCover(int index, float x, float y, float w, float h) const
    {
        auto* texture = m_art[index];
        if (!texture) return;
        const auto source = texture->getSize();
        const float source_ratio = float(source.Width) / float(source.Height);
        const float target_ratio = w / h;
        irr::core::recti source_rect(0, 0, source.Width, source.Height);
        if (source_ratio > target_ratio)
        {
            const int visible_width = int(std::lround(source.Height * target_ratio));
            const int left = (source.Width - visible_width) / 2;
            source_rect = irr::core::recti(left, 0, left + visible_width,
                                            source.Height);
        }
        else if (source_ratio < target_ratio)
        {
            const int visible_height = int(std::lround(source.Width / target_ratio));
            const int top = (source.Height - visible_height) / 2;
            source_rect = irr::core::recti(0, top, source.Width,
                                            top + visible_height);
        }
        draw2DImage(texture, rect(x, y, w, h), source_rect, nullptr,
                    irr::video::SColor(255, 255, 255, 255), true);
    }

    // The play/restart and settings artwork lives in Figma as transparent
    // sprite sheets.  Keep those original textures intact and select their
    // Figma bounds here instead of exporting/masking a new per-icon PNG.
    // This preserves the antialiased blue glow around every contour.
    void imageSource(int index, float x, float y, float w, float h,
                     int source_x, int source_y, int source_w,
                     int source_h) const
    {
        auto* texture = m_art[index];
        if (!texture) return;
        draw2DImage(texture, rect(x, y, w, h),
                    irr::core::recti(source_x, source_y,
                                     source_x + source_w,
                                     source_y + source_h),
                    nullptr, irr::video::SColor(255, 255, 255, 255), true);
    }

    void label(const irr::core::stringw& text, float x, float y, float w,
               float h, float points) const
    {
        const auto size = irr_driver->getActualScreenSize();
        const float scale = std::min(size.Width / kWidth, size.Height / kHeight);
        auto* font = GUIEngine::getFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto sample = font->getDimension(L"M");
        const auto text_size = font->getDimension(text.c_str());
        font->setScale(std::min(points * scale / std::max(1u, sample.Height),
            w * scale / std::max(1u, text_size.Width)));
        const auto destination = rect(x, y, w, h);
        auto shadow = destination;
        shadow += irr::core::position2di(0, std::max(1, int(2 * scale)));
        font->draw(text.c_str(), shadow, irr::video::SColor(165, 7, 18, 58),
                   true, true);
        font->draw(text.c_str(), destination,
                   irr::video::SColor(255, 255, 255, 255), true, true);
        font->setScale(saved);
    }

public:
    FluxaraPauseVisual(IGUIEnvironment* environment, IGUIElement* parent,
                       const irr::core::recti& area,
                       const int* touch_controls)
        : IGUIElement(EGUIET_ELEMENT, environment, parent, -1, area),
          m_touch_controls(touch_controls)
    {
        const char* files[] = {
            "pause/panel", "pause/logo", "pause/button-continue",
            "pause/button-restart", "pause/button-settings", "pause/button-exit",
            "pause/icons-play-restart", "pause/icons-play-restart",
            "pause/icons-settings-source",
            "pause/icon-exit", "pause/checkers-left", "pause/checkers-right",
            "pause/star"
        };
        for (int i = 0; i < 13; ++i)
            m_art[i] = FluxaraUI::texture(files[i]);
        setNotClipped(true);
        setEnabled(false);
    }

    // This visual fills the entire viewport, but it is artwork only.  Irrlicht
    // hit-tests visible children before it checks their enabled state, so the
    // default rectangular hit area swallowed every touch intended for the four
    // native (invisible) action buttons underneath.
    bool isPointInside(const irr::core::position2d<irr::s32>&) const override
    {
        return false;
    }

    void draw() override
    {
        if (!IsVisible) return;
        const auto size = irr_driver->getActualScreenSize();
        // Figma: #030514 at 43% opacity.
        irr_driver->getVideoDriver()->draw2DRectangle(
            irr::video::SColor(110, 3, 5, 20),
            irr::core::recti(0, 0, size.Width, size.Height));

        // Exact 844 x 390 coordinates and exported alpha layers from the
        // current Figma 347:49 design (the prior Figma revision was shifted).
        image(0, 283.49f, 58.62f, 271.013f, 288.75f);
        image(1, 351.96f, 40.47f, 134.063f, 80.438f);
        image(2, 274.00f, 133.28f, 172.425f, 139.012f);
        image(3, 408.89f, 133.28f, 138.60f, 137.363f);
        // Figma node 347:92 is object-cover, not a stretched square.
        imageCover(4, 282.66f, 228.57f, 150.975f, 121.688f);
        image(5, 392.80f, 214.54f, 177.375f, 141.488f);
        imageSource(6, 341.65f, 172.06f, 37.95f, 37.95f,
                    20, 17, 124, 134);
        imageSource(7, 457.98f, 172.06f, 40.425f, 40.425f,
                    162, 16, 123, 134);
        imageSource(8, 331.75f, 249.19f, 49.088f, 44.55f,
                    320, 0, 260, 240);
        image(9, 457.98f, 246.31f, 54.037f, 54.037f);
        image(10, 305.76f, 115.54f, 72.188f, 69.30f);
        image(11, 456.74f, 112.24f, 75.488f, 72.60f);
        image(12, 328.04f, 118.43f, 41.662f, 41.662f);
        image(12, 468.29f, 118.43f, 41.662f, 41.662f);

        // Labels deliberately remain runtime text: they use the bundled
        // Baloo Cyrillic font and localize with the rest of the game.
        label(_C("fluxara", "PAUSE"), 373.00f, 129.16f, 92.40f, 20.625f, 20.625f);
        label(_C("fluxara", "CONTINUE"), 317.726f, 217.02f, 85.387f, 10.725f, 11.137f);
        label(_C("fluxara", "RESTART"), 436.527f, 217.02f, 85.387f, 10.725f, 11.137f);
        label(controlModeLabel(*m_touch_controls), 313.597f, 300.76f,
              85.387f, 10.725f, 11.137f);
        label(_C("fluxara", "EXIT"), 442.297f, 300.76f, 85.387f, 10.725f, 11.137f);
        IGUIElement::draw();
    }
};
}
#endif

// ----------------------------------------------------------------------------

RacePausedDialog::RacePausedDialog(const float percentWidth,
                                   const float percentHeight) :
#ifdef IOS_FLUXARA_DRIFT
    ModalDialog(useFluxaraFullscreenPauseContainer() ? 1.0f : percentWidth,
                useFluxaraFullscreenPauseContainer() ? 1.0f : percentHeight)
#else
    ModalDialog(percentWidth, percentHeight)
#endif
{
    m_target_team = KART_TEAM_NONE;
    m_self_destroy = false;
    m_from_overworld = false;
    m_fluxara_pause = false;
    m_touch_controls = UserConfigParams::m_multitouch_controls;
    m_vk_pbr_toggle = NULL;

    if (dynamic_cast<OverWorld*>(World::getWorld()) != NULL)
    {
        loadFromFile("overworld_dialog.fluxara_driftgui");
        m_from_overworld = true;
    }
    else if (!NetworkConfig::get()->isNetworking())
    {
#ifdef IOS_FLUXARA_DRIFT
        m_fluxara_pause = true;
        loadFromFile("fluxara_pause_dialog.fluxara_driftgui");
#else
        loadFromFile("race_paused_dialog.fluxara_driftgui");
#endif
    }
    else
    {
        loadFromFile("online/network_ingame_dialog.fluxara_driftgui");
    }

    if (!m_fluxara_pause)
    {
        GUIEngine::RibbonWidget* back_btn = getWidget<RibbonWidget>("backbtnribbon");
        back_btn->setFocusForPlayer( PLAYER_ID_GAME_MASTER );
    }

    if (NetworkConfig::get()->isNetworking())
    {
        music_manager->pauseMusic();
        SFXManager::get()->pauseAll();
        m_text_box->clearListeners();
        m_text_box->setTextBoxType(TBT_CAP_SENTENCES);
        // Unicode enter arrow
        getWidget("send")->setText(L"\u21B2");
        // Unicode smile emoji
        getWidget("emoji")->setText(L"\u263A");
        if (UserConfigParams::m_lobby_chat && UserConfigParams::m_race_chat)
        {
            m_text_box->setActive(true);
            getWidget("send")->setVisible(true);
            getWidget("emoji")->setVisible(true);
            m_text_box->addListener(this);
            auto cl = LobbyProtocol::get<ClientLobby>();
            if (cl && !cl->serverEnabledChat())
            {
                m_text_box->setActive(false);
                getWidget("send")->setActive(false);
                getWidget("emoji")->setActive(false);
                if (m_target_team != KART_TEAM_NONE)
                    getWidget("team")->setActive(false);
            }
        } // if race chat is enabled
        else
        {
            m_text_box->setActive(false);
            m_text_box->setText(
                _("Chat is disabled, enable in options menu."));
            getWidget("send")->setVisible(false);
            getWidget("emoji")->setVisible(false);
            if (m_target_team != KART_TEAM_NONE)
                getWidget("team")->setVisible(false);
        } // else (race chat disabled)
    } // if isNetworking
    else if (!RaceManager::get()->isBenchmarking())
    {
        World::getWorld()->schedulePause(WorldStatus::IN_GAME_MENU_PHASE);
    }

    if (!m_fluxara_pause && dynamic_cast<OverWorld*>(World::getWorld()) == NULL)
    {
        if (RaceManager::get()->isBenchmarking())
        {
            // Other buttons of the pause menu are removed in benchmark mode
            getWidget<IconButtonWidget>("backbtn")->setLabel(_("Back to the Performance Test"));
            getWidget<IconButtonWidget>("exit")->setLabel(_("Exit the Performance Test"));
        }
        else if (RaceManager::get()->isBattleMode() || RaceManager::get()->isCTFMode())
        {
            getWidget<IconButtonWidget>("backbtn")->setLabel(_("Back to Battle"));
            if (!NetworkConfig::get()->isNetworking())
            {
                if (getWidget<IconButtonWidget>("newrace"))
                    getWidget<IconButtonWidget>("newrace")->setLabel(
                        _("Setup New Game"));
                if (getWidget<IconButtonWidget>("restart"))
                    getWidget<IconButtonWidget>("restart")->setLabel(_("Restart Battle"));
            }
            getWidget<IconButtonWidget>("exit")->setLabel(_("Exit Battle"));
        }
        else
        {
            getWidget<IconButtonWidget>("backbtn")->setLabel(_("Back to Race"));
            if (!NetworkConfig::get()->isNetworking())
            {
                if (getWidget<IconButtonWidget>("newrace"))
                    getWidget<IconButtonWidget>("newrace")->setLabel(
                        _("Setup New Race"));
                if (getWidget<IconButtonWidget>("restart"))
                    getWidget<IconButtonWidget>("restart")->setLabel(_("Restart Race"));
            }
            getWidget<IconButtonWidget>("exit")->setLabel(_("Exit Race"));
        }
    }
    
#ifndef MOBILE_FLUXARA_DRIFT
    if (m_text_box && UserConfigParams::m_lobby_chat)
        m_text_box->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
#endif
}   // RacePausedDialog

// ----------------------------------------------------------------------------
RacePausedDialog::~RacePausedDialog()
{
    if (NetworkConfig::get()->isNetworking())
    {
        music_manager->resumeMusic();
        SFXManager::get()->resumeAll();
    }
    else if (!RaceManager::get()->isBenchmarking())
    {
        World::getWorld()->scheduleUnpause();
    }
    
    if (m_touch_controls != UserConfigParams::m_multitouch_controls)
    {
        UserConfigParams::m_multitouch_controls = m_touch_controls;
        
        if (World::getWorld() && World::getWorld()->getRaceGUI())
        {
            World::getWorld()->getRaceGUI()->recreateGUI();
        }

        user_config->saveConfig();
    }
}   // ~RacePausedDialog

// ----------------------------------------------------------------------------

void RacePausedDialog::loadedFromFile()
{
#ifdef IOS_FLUXARA_DRIFT
    if (m_fluxara_pause)
        return;
    // The public iPhone flow must never expose the legacy race setup, help or
    // options screens from FLUXARA_DRIFT. Fluxara settings remain available from Home.
    if (!NetworkConfig::get()->isNetworking() &&
        dynamic_cast<OverWorld*>(World::getWorld()) == NULL)
    {
        GUIEngine::RibbonWidget* fluxara_choices =
            getWidget<GUIEngine::RibbonWidget>("choiceribbon");
        fluxara_choices->deleteChild("newrace");
        fluxara_choices->deleteChild("endrace");
        fluxara_choices->deleteChild("options");
        fluxara_choices->deleteChild("help");
    }
#else
    // disable the "restart" button in GPs
    if (RaceManager::get()->getMajorMode() == RaceManager::MAJOR_MODE_GRAND_PRIX)
    {
        GUIEngine::RibbonWidget* choice_ribbon =
            getWidget<GUIEngine::RibbonWidget>("choiceribbon");
#ifdef DEBUG
        const bool success = choice_ribbon->deleteChild("restart");
        assert(success);
#else
        choice_ribbon->deleteChild("restart");
#endif
    }
    // Remove "endrace" button for types not (yet?) implemented
    // Also don't show it unless the race has started. Prevents finishing in
    // a time of 0:00:00.
    if ((RaceManager::get()->getMinorMode() != RaceManager::MINOR_MODE_NORMAL_RACE  &&
         RaceManager::get()->getMinorMode() != RaceManager::MINOR_MODE_TIME_TRIAL ) ||
         World::getWorld()->isStartPhase() ||
         NetworkConfig::get()->isNetworking())
    {
        GUIEngine::RibbonWidget* choice_ribbon =
            getWidget<GUIEngine::RibbonWidget>("choiceribbon");
        choice_ribbon->deleteChild("endrace");
        // No restart in network game
        if (NetworkConfig::get()->isNetworking())
        {
            choice_ribbon->deleteChild("restart");
        }
    }

    // Remove all extraneous buttons in benchmark mode
    if (RaceManager::get()->isBenchmarking())
    {
        GUIEngine::RibbonWidget* choice_ribbon =
            getWidget<GUIEngine::RibbonWidget>("choiceribbon");
        choice_ribbon->deleteChild("newrace");
        choice_ribbon->deleteChild("restart");
        choice_ribbon->deleteChild("endrace");
        choice_ribbon->deleteChild("options");
        choice_ribbon->deleteChild("help");
    }
#endif
}

// ----------------------------------------------------------------------------

void RacePausedDialog::onEnterPressedInternal()
{
}   // onEnterPressedInternal

// ----------------------------------------------------------------------------

GUIEngine::EventPropagation
           RacePausedDialog::processEvent(const std::string& eventSource)
{
    if (m_fluxara_pause)
    {
        if (eventSource == "continue")
        {
            ModalDialog::dismiss();
            return GUIEngine::EVENT_BLOCK;
        }
        if (eventSource == "restart")
        {
            ModalDialog::dismiss();
            World::getWorld()->scheduleUnpause();
            RaceManager::get()->rerunRace();
            return GUIEngine::EVENT_BLOCK;
        }
        if (eventSource == "exit")
        {
            ModalDialog::dismiss();
            RaceManager::get()->exitRace();
            RaceManager::get()->setAIKartOverride("");
            StateManager::get()->resetAndGoToScreen(
                FluxaraHomeScreen::getInstance());
            return GUIEngine::EVENT_BLOCK;
        }
        if (eventSource == "settings")
        {
            cycleTouchControls(m_touch_controls);
            return GUIEngine::EVENT_BLOCK;
        }
        return GUIEngine::EVENT_BLOCK;
    }

    GUIEngine::RibbonWidget* choice_ribbon =
            getWidget<GUIEngine::RibbonWidget>("choiceribbon");
    GUIEngine::RibbonWidget* backbtn_ribbon =
            getWidget<GUIEngine::RibbonWidget>("backbtnribbon");

    if (eventSource == "send" && m_text_box)
    {
        m_target_team = KART_TEAM_NONE;
        handleChat(m_text_box->getText());
        return GUIEngine::EVENT_BLOCK;
    }
    if (eventSource == "team" && m_text_box)
    {
        handleChat(m_text_box->getText());
        return GUIEngine::EVENT_BLOCK;
    }
    else if (eventSource == "emoji" && m_text_box &&
        !ScreenKeyboard::isActive())
    {
        EmojiKeyboard* ek = new EmojiKeyboard(1.0f, 0.40f,
            m_text_box->getIrrlichtElement<CGUIEditBox>());
        ek->init();
        return GUIEngine::EVENT_BLOCK;
    }
    else if (eventSource == "backbtnribbon")
    {
        const std::string& selection =
            backbtn_ribbon->getSelectionIDString(PLAYER_ID_GAME_MASTER);
            
        if (selection == "backbtn")
        {
            // unpausing is done in the destructor so nothing more to do here
            ModalDialog::dismiss();
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "touch_device")
        {
            IrrlichtDevice* irrlicht_device = irr_driver->getDevice();
            assert(irrlicht_device != NULL);
            bool accelerometer_available = irrlicht_device->isAccelerometerAvailable();
            bool gyroscope_available = irrlicht_device->isGyroscopeAvailable() && accelerometer_available;
    
            if (m_touch_controls == MULTITOUCH_CONTROLS_STEERING_WHEEL)
            {
                m_touch_controls = MULTITOUCH_CONTROLS_ACCELEROMETER;
            }
            else if (m_touch_controls == MULTITOUCH_CONTROLS_ACCELEROMETER)
            {
                m_touch_controls = MULTITOUCH_CONTROLS_GYROSCOPE;
            }
            else if (m_touch_controls == MULTITOUCH_CONTROLS_GYROSCOPE)
            {
                m_touch_controls = MULTITOUCH_CONTROLS_STEERING_WHEEL;
            }
            
            if (m_touch_controls == MULTITOUCH_CONTROLS_ACCELEROMETER &&
                !accelerometer_available)
            {
                m_touch_controls = MULTITOUCH_CONTROLS_STEERING_WHEEL;
            }
            else if (m_touch_controls == MULTITOUCH_CONTROLS_GYROSCOPE &&
                !gyroscope_available)
            {
                m_touch_controls = MULTITOUCH_CONTROLS_STEERING_WHEEL;
            }
            
            updateTouchDeviceIcon();
            
            return GUIEngine::EVENT_BLOCK;
        }
    }
    else if (eventSource == "choiceribbon")
    {
        const std::string& selection =
            choice_ribbon->getSelectionIDString(PLAYER_ID_GAME_MASTER);

        if (selection == "exit")
        {
            bool from_overworld = m_from_overworld;
            ModalDialog::dismiss();
            if (FLUXARA_DRIFTHost::existHost())
            {
                FLUXARA_DRIFTHost::get()->shutdown();
            }
            RaceManager::get()->exitRace();
            RaceManager::get()->setAIKartOverride("");

            // If a benchmark is exited early through the pause menu, disable benchmarking mode
            if (RaceManager::get()->isBenchmarking())
                RaceManager::get()->setBenchmarking(false);

            if (NetworkConfig::get()->isNetworking())
            {
                StateManager::get()->resetAndSetStack(
                    NetworkConfig::get()->getResetScreens().data());
                NetworkConfig::get()->unsetNetworking();
            }
            else
            {
#ifdef IOS_FLUXARA_DRIFT
                StateManager::get()->resetAndGoToScreen(
                    FluxaraHomeScreen::getInstance());
#else
                StateManager::get()->resetAndGoToScreen(MainMenuScreen::getInstance());

                // Pause story mode timer when quitting story mode
                if (from_overworld)
                    story_mode_timer->pauseTimer(/*loading screen*/ false);

                if (RaceManager::get()->raceWasStartedFromOverworld())
                {
                    OverWorld::enterOverWorld();
                }
#endif
            }
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "help")
        {
            GE::GEVulkanDriver* vk_pbr_toggle = m_vk_pbr_toggle;
            dismiss();
#ifndef SERVER_ONLY
            if (vk_pbr_toggle)
            {
                UserConfigParams::m_dynamic_lights = !UserConfigParams::m_dynamic_lights;
                GE::getGEConfig()->m_pbr = UserConfigParams::m_dynamic_lights;
                vk_pbr_toggle->updateDriver(false/*scale_changed*/, true/*pbr_changed*/);
            }
            else
            {
                HelpScreen1::getInstance()->push();
            }
#endif
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "options")
        {
            dismiss();
#ifndef SERVER_ONLY
            OptionsScreenGeneral::getInstance()->push();
#endif
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "restart")
        {
            ModalDialog::dismiss();
            World::getWorld()->scheduleUnpause();
            RaceManager::get()->rerunRace();
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "newrace")
        {
            ModalDialog::dismiss();
            if (NetworkConfig::get()->isNetworking())
            {
                // back lobby
                NetworkString back(PROTOCOL_LOBBY_ROOM);
                back.setSynchronous(true);
                back.addUInt8(LobbyProtocol::LE_CLIENT_BACK_LOBBY);
                FLUXARA_DRIFTHost::get()->sendToServer(&back, true);
            }
            else
            {
                World::getWorld()->scheduleUnpause();
                RaceManager::get()->exitRace();
                Screen* new_stack[] =
                    {
                        MainMenuScreen::getInstance(),
                        RaceSetupScreen::getInstance(),
                        NULL
                    };
                StateManager::get()->resetAndSetStack(new_stack);
            }
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "endrace")
        {
            ModalDialog::dismiss();
            if (RaceManager::get()->getMajorMode() == RaceManager::MAJOR_MODE_GRAND_PRIX)
                RaceManager::get()->addSkippedTrackInGP();
            World::getWorld()->getRaceGUI()->removeReferee();
            World::getWorld()->endRaceEarly();
            return GUIEngine::EVENT_BLOCK;
        }
        else if (selection == "selectkart")
        {
            dynamic_cast<OverWorld*>(World::getWorld())->scheduleSelectKart();
            ModalDialog::dismiss();
            return GUIEngine::EVENT_BLOCK;
        }
    }
    return GUIEngine::EVENT_LET;
}   // processEvent

// ----------------------------------------------------------------------------
void RacePausedDialog::beforeAddingWidgets()
{
    if (m_fluxara_pause)
        return;
    GUIEngine::RibbonWidget* choice_ribbon =
        getWidget<GUIEngine::RibbonWidget>("choiceribbon");

    bool showSetupNewRace = RaceManager::get()->raceWasStartedFromOverworld();
    int index = choice_ribbon->findItemNamed("newrace");
    if (index != -1)
        choice_ribbon->setItemVisible(index, !showSetupNewRace);

#ifdef IOS_FLUXARA_DRIFT
    if (isMotoricaStandaloneModeIOS() && m_from_overworld)
    {
        index = choice_ribbon->findItemNamed("selectkart");
        if (index != -1)
            choice_ribbon->setItemVisible(index, false);
    }
#endif

    // Disable in game menu to avoid timer desync if not racing in network
    // game
    if (NetworkConfig::get()->isNetworking() &&
        !(World::getWorld()->getPhase() == WorldStatus::MUSIC_PHASE ||
        World::getWorld()->getPhase() == WorldStatus::RACE_PHASE))
    {
        index = choice_ribbon->findItemNamed("help");
        if (index != -1)
        {
#ifndef SERVER_ONLY
            m_vk_pbr_toggle = GE::getVKDriver();
            if (m_vk_pbr_toggle)
            {
                IconButtonWidget* hw = getWidget<IconButtonWidget>("help");
                IconButtonWidget* ew = getWidget<IconButtonWidget>("exit");
                hw->m_properties[PROP_ID] = "exit";
                ew->m_properties[PROP_ID] = "help";
            }
            else
                choice_ribbon->setItemVisible(index, false);
#endif
        }
        index = choice_ribbon->findItemNamed("options");
        if (index != -1)
            choice_ribbon->setItemVisible(index, false);
        index = choice_ribbon->findItemNamed("newrace");
        if (index != -1)
            choice_ribbon->setItemVisible(index, false);
    }
    if (NetworkConfig::get()->isNetworking())
    {
        int id = 0;
        for (auto& kart : World::getWorld()->getKarts())
        {
            if (!World::getWorld()->hasTeam())
                break;
            // Handle only 1st local player even splitscreen
            if (kart->getController()->isLocalPlayerController())
            {
                m_target_team =
                    RaceManager::get()->getKartInfo(id).getKartTeam();
                break;
            }
            id++;
        }
        if (m_target_team == KART_TEAM_RED)
        {
            getWidget("team")->setVisible(true);
            getWidget("team")->m_properties[GUIEngine::PROP_WIDTH] = "7%";
            getWidget("team_space")->m_properties[GUIEngine::PROP_WIDTH] = "1%";
            getWidget("team")->setText(StringUtils::utf32ToWide({0x1f7e5}));
        }
        else if (m_target_team == KART_TEAM_BLUE)
        {
            getWidget("team")->setVisible(true);
            getWidget("team")->m_properties[GUIEngine::PROP_WIDTH] = "7%";
            getWidget("team_space")->m_properties[GUIEngine::PROP_WIDTH] = "1%";
            getWidget("team")->setText(StringUtils::utf32ToWide({0x1f7e6}));
        }
        else
        {
            getWidget("team")->m_properties[GUIEngine::PROP_WIDTH] = "0%";
            getWidget("team_space")->m_properties[GUIEngine::PROP_WIDTH] = "0%";
            getWidget("team")->setVisible(false);
        }
        LayoutManager::calculateLayout(m_widgets, this);
        m_text_box = getWidget<TextBoxWidget>("chat");
    }
    else
        m_text_box = NULL;
        
    bool has_multitouch_gui = false;
    
    if (World::getWorld() && World::getWorld()->getRaceGUI() &&
        World::getWorld()->getRaceGUI()->getMultitouchGUI() &&
        !World::getWorld()->getRaceGUI()->getMultitouchGUI()->isSpectatorMode())
    {
        has_multitouch_gui = true;
    }
    
    IrrlichtDevice* irrlicht_device = irr_driver->getDevice();
    assert(irrlicht_device != NULL);
    bool accelerometer_available = irrlicht_device->isAccelerometerAvailable();
    
    if (!has_multitouch_gui || !accelerometer_available)
    {
        GUIEngine::RibbonWidget* backbtn_ribbon =
                            getWidget<GUIEngine::RibbonWidget>("backbtnribbon");
        backbtn_ribbon->removeChildNamed("touch_device");
    }

}   // beforeAddingWidgets

// ----------------------------------------------------------------------------
void RacePausedDialog::init()
{
    if (m_fluxara_pause)
    {
        m_irrlicht_window->setDrawBackground(false);
        m_fade_background = false;
        for (const char* id : {"continue", "restart", "settings", "exit"})
            FluxaraUI::rasterHitTarget(getWidget<GUIEngine::ButtonWidget>(id));
#ifdef IOS_FLUXARA_DRIFT
        new FluxaraPauseVisual(GUIEngine::getGUIEnv(), m_irrlicht_window,
            irr::core::recti(0, 0, m_area.getWidth(), m_area.getHeight()),
            &m_touch_controls);
#endif
        return;
    }
    m_touch_controls = UserConfigParams::m_multitouch_controls;
    updateTouchDeviceIcon();
#ifndef SERVER_ONLY
    if (m_vk_pbr_toggle)
    {
        IconButtonWidget* widget = getWidget<IconButtonWidget>("help");
        widget->setLabel(UserConfigParams::m_dynamic_lights ?
            _("Disable advanced pipeline") : _("Enable advanced pipeline"));
        widget->setImage(irr_driver->getTexture(FileManager::GUI_ICON,
            "options_video.png"));
        widget = getWidget<IconButtonWidget>("exit");
        widget->setImage(irr_driver->getTexture(FileManager::GUI_ICON,
            "main_quit.png"));
    }
#endif
}   // init

// ----------------------------------------------------------------------------
void RacePausedDialog::handleChat(const irr::core::stringw& text)
{
    if (auto cl = LobbyProtocol::get<ClientLobby>())
    {
        if (!text.empty())
        {
            if (text[0] == L'/' && text.size() > 1)
            {
                std::string cmd = StringUtils::wideToUtf8(text);
                cl->handleClientCommand(cmd.erase(0, 1));
            }
            else
                cl->sendChat(text, m_target_team);
        }
    }
    m_self_destroy = true;
}   // onEnterPressed

// ----------------------------------------------------------------------------
bool RacePausedDialog::onEnterPressed(const irr::core::stringw& text)
{
    // Assume enter for non team chat
    m_target_team = KART_TEAM_NONE;
    handleChat(text);
    return true;
}   // onEnterPressed

// ----------------------------------------------------------------------------
void RacePausedDialog::updateTouchDeviceIcon()
{
    GUIEngine::RibbonWidget* backbtn_ribbon =
                            getWidget<GUIEngine::RibbonWidget>("backbtnribbon");
    GUIEngine::IconButtonWidget* widget = (IconButtonWidget*)backbtn_ribbon->
                                                findWidgetNamed("touch_device");
    if (!widget)
        return;
                                                  
    switch (m_touch_controls)
    {
    case MULTITOUCH_CONTROLS_UNDEFINED:
    case MULTITOUCH_CONTROLS_STEERING_WHEEL:
        widget->setLabel(_("Steering wheel"));
        widget->setImage(irr_driver->getTexture(FileManager::GUI_ICON,
                                                "android/steering_wheel.png"));
        break;
    case MULTITOUCH_CONTROLS_ACCELEROMETER:
        widget->setLabel(_("Accelerometer"));
        widget->setImage(irr_driver->getTexture(FileManager::GUI_ICON,
                                                "android/accelerator_icon.png"));
        break;
    case MULTITOUCH_CONTROLS_GYROSCOPE:
        widget->setLabel(_("Gyroscope"));
        widget->setImage(irr_driver->getTexture(FileManager::GUI_ICON,
                                                "android/gyroscope_icon.png"));
        break;
    default:
        break;
    }
}   // updateTouchDeviceIcon
