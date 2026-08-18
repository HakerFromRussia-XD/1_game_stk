//  SuperTuxKart - a fun racing game with go-kart
//  Copyright (C) 2014-2015 SuperTuxKart-Team
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

#include "states_screens/race_gui_multitouch.hpp"

using namespace irr;

#include <algorithm>

#include "config/user_config.hpp"
#include "graphics/camera/camera.hpp"
#include "graphics/camera/camera_debug.hpp"
#include "graphics/2dutils.hpp"
#include "graphics/irr_driver.hpp"
#include "graphics/material.hpp"
#include "guiengine/scalable_font.hpp"
#include "input/device_manager.hpp"
#include "input/motorica_game_control.hpp"
#ifdef IOS_STK
#include "input/motorica_standalone_training.hpp"
#endif
#include "input/multitouch_device.hpp"
#include "items/powerup.hpp"
#include "karts/abstract_kart.hpp"
#include "karts/controller/kart_control.hpp"
#include "modes/world.hpp"
#include "network/protocols/client_lobby.hpp"
#include "states_screens/race_gui_base.hpp"
#include "utils/log.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

#include <IrrlichtDevice.h>

#ifdef IOS_STK
namespace
{
bool motoricaUseRussian()
{
    if (translations == nullptr)
        return false;
    const std::string code = translations->getCurrentLanguageNameCode();
    return code == "ru" || code.find("ru_") == 0 ||
           code.find("ru-") == 0;
}

std::string motoricaExerciseLabel(StandaloneExerciseID exercise,
                                  bool russian)
{
    if (exercise == StandaloneExerciseID::Precision)
        return russian ? "ТОЧНОСТЬ" : "PRECISION";
    if (exercise == StandaloneExerciseID::Reaction)
        return russian ? "РЕАКЦИЯ" : "REACTION";
    return russian ? "УДЕРЖАНИЕ" : "SIGNAL HOLD";
}

std::string motoricaPhaseLabel(const std::string& phase, bool russian)
{
    if (phase == "disconnected") return russian ? "НЕТ СИГНАЛА" : "NO SIGNAL";
    if (phase == "calibration_rest") return russian ? "КАЛИБРОВКА: ПОКОЙ" : "CALIBRATION: REST";
    if (phase == "calibration_open") return russian ? "КАЛИБРОВКА: ОТКРЫТИЕ" : "CALIBRATION: OPEN";
    if (phase == "calibration_close") return russian ? "КАЛИБРОВКА: ЗАКРЫТИЕ" : "CALIBRATION: CLOSE";
    if (phase == "control") return russian ? "УПРАВЛЕНИЕ" : "CONTROL";
    if (phase == "signal_lost") return russian ? "ПОТЕРЯ СИГНАЛА — ПАУЗА" : "SIGNAL LOST — PAUSED";
    if (phase == "restored") return russian ? "СИГНАЛ ВОССТАНОВЛЕН" : "SIGNAL RESTORED";
    if (phase == "manual") return russian ? "РУЧНЫЕ СИГНАЛЫ" : "MANUAL SIGNALS";
    return russian ? "ЭКРАН / ГИРОСКОП" : "TOUCH / GYROSCOPE";
}
}
#endif

//-----------------------------------------------------------------------------
/** The multitouch GUI constructor
 */
RaceGUIMultitouch::RaceGUIMultitouch(RaceGUIBase* race_gui)
{
    m_race_gui = race_gui;
    m_gui_action = false;
    m_is_spectator_mode = false;
    m_height = 0;
    m_steering_wheel_tex = NULL;
    m_steering_wheel_tex_mask_up = NULL;
    m_steering_wheel_tex_mask_down = NULL;
    m_accelerator_tex = NULL;
    m_accelerator_handle_tex = NULL;
    m_accelerator_icon_tex = NULL;
    m_pause_tex = NULL;
    m_nitro_tex = NULL;
    m_nitro_empty_tex = NULL;
    m_wing_mirror_tex = NULL;
    m_thunderbird_reset_tex = NULL;
    m_drift_tex = NULL;
    m_bg_button_tex = NULL;
    m_bg_button_focus_tex = NULL;
    m_gui_action_tex = NULL;
    m_up_tex = NULL;
    m_down_tex = NULL;
    m_screen_tex = NULL;

    m_device = input_manager->getDeviceManager()->getMultitouchDevice();

    init();
}   // RaceGUIMultitouch

//-----------------------------------------------------------------------------
/** The multitouch GUI destructor
 */
RaceGUIMultitouch::~RaceGUIMultitouch()
{
    close();
}   // ~RaceGUIMultitouch

//-----------------------------------------------------------------------------
/** Sets the multitouch race gui to its initial state
 */
void RaceGUIMultitouch::reset()
{
    if (m_device != NULL)
    {
        m_device->reset();
    }
}   // reset

//-----------------------------------------------------------------------------
/** Recreate multitouch race gui when config was changed
 */
void RaceGUIMultitouch::recreate()
{
    close();
    reset();
    init();
}   // recreate


//-----------------------------------------------------------------------------
/** Clears all previously created buttons in the multitouch device
 */
void RaceGUIMultitouch::close()
{
    if (m_device)
    {
        m_device->clearButtons();

        if (m_device->isAccelerometerActive())
        {
            m_device->deactivateAccelerometer();
        }

        if (m_device->isGyroscopeActive())
        {
            m_device->deactivateGyroscope();
        }
    }
}   // close

//-----------------------------------------------------------------------------
/** Initializes multitouch race gui
 */
void RaceGUIMultitouch::init()
{
    if (UserConfigParams::m_multitouch_scale > 1.6f)
    {
        UserConfigParams::m_multitouch_scale = 1.6f;
    }
    else if (UserConfigParams::m_multitouch_scale < 0.8f)
    {
        UserConfigParams::m_multitouch_scale = 0.8f;
    }
    
    m_steering_wheel_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                                  "android/steering_wheel.png");
    m_accelerator_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                               "android/accelerator.png");
    m_accelerator_handle_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                               "android/accelerator_handle.png");
    m_accelerator_icon_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                               "android/accelerator_icon.png");
    m_pause_tex = irr_driver->getTexture(FileManager::GUI_ICON, "android/pause.png");
    m_nitro_tex = irr_driver->getTexture(FileManager::GUI_ICON, "android/nitro.png");
    m_nitro_empty_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                                     "android/nitro_empty.png");
    m_wing_mirror_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                                     "android/wing_mirror.png");
    m_thunderbird_reset_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                               "android/thunderbird_reset.png");
    m_drift_tex = irr_driver->getTexture(FileManager::GUI_ICON, "android/drift.png");
    m_bg_button_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                                  "android/blur_bg_button.png");
    m_bg_button_focus_tex = irr_driver->getTexture(FileManager::GUI_ICON,
                                            "android/blur_bg_button_focus.png");
    m_gui_action_tex = irr_driver->getTexture(FileManager::GUI_ICON,"challenge.png");
    m_up_tex = irr_driver->getTexture(FileManager::GUI_ICON, "up.png");
    m_down_tex = irr_driver->getTexture(FileManager::GUI_ICON, "down.png");
    m_screen_tex = irr_driver->getTexture(FileManager::GUI_ICON, "screen_other.png");
    m_steering_wheel_tex_mask_up = irr_driver->getTexture(FileManager::GUI_ICON,
                                        "android/steering_wheel_mask_up.png");
    m_steering_wheel_tex_mask_down = irr_driver->getTexture(FileManager::GUI_ICON,
                                        "android/steering_wheel_mask_down.png");

    auto cl = LobbyProtocol::get<ClientLobby>();
    
    if (cl && cl->isSpectator())
    {
        createSpectatorGUI();
        m_is_spectator_mode = true;
    }
    else
    {
        createRaceGUI();
    }
}

//-----------------------------------------------------------------------------
/** Determines the look of multitouch race GUI interface
 */
void RaceGUIMultitouch::createRaceGUI()
{
    if (m_device == NULL)
        return;

#ifdef IOS_STK
    if (MotoricaStandaloneTraining::get()->usesSimulatedSignals())
    {
        const int width = irr_driver->getActualScreenSize().Width;
        const int height = irr_driver->getActualScreenSize().Height;
        const int size = std::max(62, (int)(height * 0.13f));
        const int gap = std::max(16, (int)(height * 0.035f));
        const int total = size * 4 + gap * 3;
        const int start_x = (width - total) / 2;
        const int y = height - size - gap;
        m_device->addButton(BUTTON_ESCAPE, gap, gap, size, size);
        for (int index = 0; index < 4; index++)
        {
            m_device->addButton(BUTTON_CUSTOM,
                start_x + index * (size + gap), y, size, size,
                onMotoricaSignalButtonPress);
        }
        m_height = size + gap * 2;
        return;
    }
#endif
        
    if (UserConfigParams::m_multitouch_controls == MULTITOUCH_CONTROLS_ACCELEROMETER)
    {
        m_device->activateAccelerometer();
    }
    if (UserConfigParams::m_multitouch_controls == MULTITOUCH_CONTROLS_GYROSCOPE)
    {
        m_device->activateAccelerometer();
        m_device->activateGyroscope();
    }

    const float scale = UserConfigParams::m_multitouch_scale;

    int w = irr_driver->getActualScreenSize().Width;
    if (w - irr_driver->getDevice()->getRightPadding() > 0)
        w -= irr_driver->getDevice()->getRightPadding();

    const int h = irr_driver->getActualScreenSize().Height;
    const float btn_size = 0.125f * h * scale;
    const float btn2_size = 0.35f * h * scale;
    const float margin = 0.075f * h * scale;
    const float margin_top = 0.3f * h;
    const float col_size = (btn_size + margin);

    const float small_ratio = 0.75f;
    const float btn_small_size = small_ratio * btn_size;
    const float margin_small = small_ratio * margin;
    const float col_small_size = small_ratio * col_size;

    float left_padding = 0.0f;
    if (irr_driver->getDevice()->getLeftPadding() > 0)
        left_padding = irr_driver->getDevice()->getLeftPadding();

    float first_column_x = w - 2 * col_size;
    float second_column_x = w - 1 * col_size;
    float steering_wheel_margin = 0.6f * margin;
    float steering_wheel_x = steering_wheel_margin;
    steering_wheel_x += left_padding;
    float steering_wheel_y = h - steering_wheel_margin - btn2_size;
    float steering_accel_margin = margin;
    float steering_accel_x = steering_accel_margin;
    steering_accel_x += left_padding;
    float steering_accel_y = h - steering_accel_margin - btn2_size;

    if (UserConfigParams::m_multitouch_inverted)
    {
        first_column_x = margin + 1 * col_size + left_padding;
        second_column_x = margin + left_padding;
        steering_wheel_x = w - btn2_size - steering_wheel_margin;
        steering_accel_x = w - btn2_size / 2 - steering_accel_margin;
    }

    m_height = (unsigned int)(3 * col_size + margin / 2);
    
    if (UserConfigParams::m_multitouch_controls == MULTITOUCH_CONTROLS_ACCELEROMETER ||
        UserConfigParams::m_multitouch_controls == MULTITOUCH_CONTROLS_GYROSCOPE)
    {
        m_device->addButton(BUTTON_UP_DOWN,
                    int(steering_accel_x), int(steering_accel_y),
                    int(btn2_size / 2), int(btn2_size));
    }
    else
    {
        m_device->addButton(BUTTON_STEERING,
                            int(steering_wheel_x), int(steering_wheel_y),
                            int(btn2_size), int(btn2_size));
    }

    m_device->addButton(BUTTON_ESCAPE,
                        int(margin_top), int(margin_small),
                        int(btn_small_size), int(btn_small_size));
    m_device->addButton(BUTTON_RESCUE,
                        int(margin_top + col_small_size), int(margin_small),
                        int(btn_small_size), int(btn_small_size));
    m_device->addButton(BUTTON_UP,
                        int(second_column_x), int(h - 3 * col_size),
                        int(btn_size), int(btn_size));
    m_device->addButton(BUTTON_NITRO,
                        int(second_column_x), int(h - 2 * col_size),
                        int(btn_size), int(btn_size));
    m_device->addButton(BUTTON_SKIDDING,
                        int(second_column_x), int(h - 1 * col_size),
                        int(btn_size), int(btn_size));
    m_device->addButton(BUTTON_FIRE,
                        int(first_column_x),  int(h - 2 * col_size),
                        int(btn_size), int(btn_size));
    m_device->addButton(BUTTON_LOOK_BACKWARDS,
                        int(first_column_x), int(h - 1 * col_size),
                        int(btn_size), int(btn_size));
} // createRaceGUI

//-----------------------------------------------------------------------------
/** Determines the look of spectator GUI interface
 */
void RaceGUIMultitouch::createSpectatorGUI()
{
    if (m_device == NULL)
        return;
        
    const float scale = UserConfigParams::m_multitouch_scale;

    const int h = irr_driver->getActualScreenSize().Height;
    const float btn_size = 0.125f * h * scale;
    const float margin = 0.075f * h * scale;
    const float margin_top = 0.3f * h;

    const float small_ratio = 0.75f;
    const float btn_small_size = small_ratio * btn_size;
    const float margin_small = small_ratio * margin;
    
    m_height = (unsigned int)(btn_size + 2 * margin);
    
    m_device->addButton(BUTTON_ESCAPE,
                        int(margin_top), int(margin_small),
                        int(btn_small_size), int(btn_small_size));
                        
    m_device->addButton(BUTTON_CUSTOM,
                    int(margin), int(h - margin - btn_size),
                    int(btn_size), int(btn_size), onCustomButtonPress);
    
    m_device->addButton(BUTTON_CUSTOM,
                    int(margin * 2 + btn_size), int(h - margin - btn_size),
                    int(btn_size), int(btn_size), onCustomButtonPress);
                    
    m_device->addButton(BUTTON_CUSTOM,
                    int(margin * 3 + btn_size * 2), int(h - margin - btn_size),
                    int(btn_size), int(btn_size), onCustomButtonPress);

    m_device->addButton(BUTTON_CUSTOM,
                    int(margin * 4 + btn_size * 3), int(h - margin - btn_size),
                    int(btn_size), int(btn_size), onCustomButtonPress);
} // createSpectatorGUI

//-----------------------------------------------------------------------------
/** Callback function when custom button is pressed
 */
void RaceGUIMultitouch::onCustomButtonPress(unsigned int button_id,
                                            bool pressed)
{
    if (!pressed)
        return;
        
    auto cl = LobbyProtocol::get<ClientLobby>();
    
    if (!cl || !cl->isSpectator())
        return;

    switch (button_id)
    {
    case 1:
        cl->changeSpectateTarget(PA_STEER_LEFT, Input::MAX_VALUE,
                                 Input::IT_KEYBOARD);
        break;
    case 2:
        cl->changeSpectateTarget(PA_STEER_RIGHT, Input::MAX_VALUE,
                                 Input::IT_KEYBOARD);
        break;
    case 3:
        cl->changeSpectateTarget(PA_LOOK_BACK, Input::MAX_VALUE,
                                 Input::IT_KEYBOARD);
        break;
    case 4:
        cl->changeSpectateTarget(PA_ACCEL, Input::MAX_VALUE,
                                 Input::IT_KEYBOARD);
        break;
    }
}

//-----------------------------------------------------------------------------
void RaceGUIMultitouch::onMotoricaSignalButtonPress(unsigned int button_id,
                                                    bool pressed)
{
#ifdef IOS_STK
    MotoricaStandaloneTraining* training = MotoricaStandaloneTraining::get();
    switch (button_id)
    {
    case 1:
        training->setManualSignal(true, pressed);
        break;
    case 2:
        training->setManualSignal(false, pressed);
        break;
    case 3:
        if (pressed)
            training->toggleConnection();
        break;
    case 4:
        if (pressed)
            training->toggleScript();
        break;
    default:
        break;
    }
#else
    (void)button_id;
    (void)pressed;
#endif
}

//-----------------------------------------------------------------------------
/** Draws the buttons for multitouch race GUI.
 *  \param kart The kart for which to show the data.
 *  \param viewport The viewport to use.
 *  \param scaling Which scaling to apply to the buttons.
 */
void RaceGUIMultitouch::draw(const AbstractKart* kart,
                             const core::recti &viewport,
                             const core::vector2df &scaling)
{
#ifndef SERVER_ONLY
    if (m_device == NULL)
        return;

    for (unsigned int i = 0; i < m_device->getButtonsCount(); i++)
    {
        MultitouchButton* button = m_device->getButton(i);

        core::rect<s32> btn_pos(button->x, button->y, button->x + button->width,
                                button->y + button->height);
                                
        core::rect<s32> btn_pos_bg((int)(button->x - button->width * 0.2f),
                                   (int)(button->y - button->height * 0.2f),
                                   (int)(button->x + button->width * 1.2f),
                                   (int)(button->y + button->height * 1.2f));
                                   
        const core::position2d<s32> pos_zero = core::position2d<s32>(0,0);

        if (button->type == MultitouchButtonType::BUTTON_STEERING)
        {
            MotoricaGameControl* emg = MotoricaGameControl::get();
            emg->flushConnectionRestoreUi();
            emg->flushConnectionLossUi();
            const bool emg_connected = emg->isConnected();
            float steering_axis = button->axis_x;
            if (!button->pressed && emg_connected &&
                UserConfigParams::m_motorica_emg_steering)
                steering_axis = emg->getSteeringAxis();

            video::SColor color((unsigned)-1);
            video::ITexture* btn_texture = m_steering_wheel_tex;
            core::rect<s32> coords(pos_zero, btn_texture->getSize());
            draw2DImageRotationColor(btn_texture, btn_pos, coords, NULL,
                (button->axis_y >= 0 ? -1 : 1) * steering_axis, color);
            AbstractKart* k = NULL;
            Camera* c = Camera::getActiveCamera();
            if (c)
                k = c->getKart();
            if (k)
            {
                float accel = k->getControls().getAccel();
                core::rect<s32> mask_coords(pos_zero, m_steering_wheel_tex_mask_up->getSize());
                color.setAlpha(core::clamp((int)(accel >= 0.0f ? accel * 128.0f : 0), 0, 255));
                draw2DImageRotationColor(m_steering_wheel_tex_mask_up, btn_pos, mask_coords, NULL,
                    (button->axis_y >= 0 ? -1 : 1) * steering_axis, color);
                color.setAlpha(k->getControls().getBrake() ? 128 : 0);
                draw2DImageRotationColor(m_steering_wheel_tex_mask_down, btn_pos, mask_coords, NULL,
                    (button->axis_y >= 0 ? -1 : 1) * steering_axis, color);
            }

            const int alpha = emg_connected ? 190 : 85;
            const int bar_width = std::max(6, (int)(button->width * 0.08f));
            const int bar_height = std::max(24, (int)(button->height * 0.56f));
            const int gap = std::max(4, (int)(button->width * 0.03f));
            const int bar_top = button->y + (button->height - bar_height) / 2;
            const int screen_width = irr_driver->getActualScreenSize().Width;
            const int left_x = core::clamp(button->x - gap - bar_width, 0,
                                           std::max(0, screen_width - bar_width));
            const int right_x = core::clamp(button->x + button->width + gap, 0,
                                            std::max(0, screen_width - bar_width));
            const int open_level = emg->getOpenLevel();
            const int close_level = emg->getCloseLevel();
            const uint64_t emg_seq = emg->getSeq();
            const int left_fill = core::clamp((open_level * bar_height) / 255,
                                              0, bar_height);
            const int right_fill = core::clamp((close_level * bar_height) / 255,
                                               0, bar_height);
            static uint64_t last_logged_emg_seq = (uint64_t)-1;
            if (emg_seq != last_logged_emg_seq &&
                (!emg_connected || emg_seq <= 3 || emg_seq % 30 == 0))
            {
                last_logged_emg_seq = emg_seq;
                Log::info("MotoricaGameControl",
                    "[BLE stk-game debug] gui seq=%llu open=%d close=%d connected=%d fill=%d/%d",
                    (unsigned long long)emg_seq, open_level, close_level,
                    emg_connected ? 1 : 0, left_fill, right_fill);
            }
            core::rect<s32> left_bg(left_x, bar_top, left_x + bar_width,
                                    bar_top + bar_height);
            core::rect<s32> right_bg(right_x, bar_top, right_x + bar_width,
                                     bar_top + bar_height);
            GL32_draw2DRectangle(video::SColor(alpha, 10, 18, 28), left_bg);
            GL32_draw2DRectangle(video::SColor(alpha, 10, 18, 28), right_bg);
            core::rect<s32> left_value(left_x, bar_top + bar_height - left_fill,
                                       left_x + bar_width,
                                       bar_top + bar_height);
            core::rect<s32> right_value(right_x, bar_top + bar_height - right_fill,
                                        right_x + bar_width,
                                        bar_top + bar_height);
            GL32_draw2DRectangle(video::SColor(alpha, 255, 192, 0), left_value);
            GL32_draw2DRectangle(video::SColor(alpha, 0, 186, 255), right_value);
            // float x = (float)(button->x) + (float)(button->width) / 2.0f *
            //                                          (button->axis_x + 1.0f);
            // float y = (float)(button->y) + (float)(button->height) / 2.0f *
            //                                          (button->axis_y + 1.0f);
            // float w = (float)(button->width) / 20.0f;
            // float h = (float)(button->height) / 20.0f;

            // core::rect<s32> pos2(int(round(x - w)), int(round(y - h)),
            //                      int(round(x + w)), int(round(y + h)));

            // draw2DImage(btn_texture, pos2, coords, NULL, NULL, true);
        }
        if (button->type == MultitouchButtonType::BUTTON_UP_DOWN)
        {
            video::ITexture* btn_texture = m_accelerator_tex;
            core::rect<s32> coords(pos_zero, btn_texture->getSize());
            draw2DImage(btn_texture, btn_pos, coords, NULL, NULL, true);
            AbstractKart* k = NULL;
            Camera* c = Camera::getActiveCamera();
            if (c)
                k = c->getKart();
            if (k)
            {
                float upper_corner;
                if (k->getControls().getBrake())
                {
                    upper_corner = button->y + button->height - button->width / 2;
                }
                else
                {
                    upper_corner = button->y + button->height / 2 - button->width / 4;
                    upper_corner -= (int)((float)(button->height / 2 - button->width / 4) * (k->getControls().getAccel()));
                }
                core::rect<s32> handle_pos(button->x, upper_corner, button->x + button->width / 2,
                                           upper_corner + button->width / 2);
                core::rect<s32> handle_coords(pos_zero, m_accelerator_handle_tex->getSize());
                draw2DImage(m_accelerator_handle_tex, handle_pos, handle_coords, NULL, NULL, true);
            }
        }
        else
        {
            bool can_be_pressed = true;
            video::ITexture* btn_texture = NULL;

            switch (button->type)
            {
            case MultitouchButtonType::BUTTON_ESCAPE:
                btn_texture = m_pause_tex;
                break;
            case MultitouchButtonType::BUTTON_FIRE:
            {
                const Powerup* powerup = kart->getPowerup();
                if (m_gui_action == true)
                {
                    btn_texture = m_gui_action_tex;
                }
                else if (powerup->getType() != PowerupManager::POWERUP_NOTHING
                         && !kart->hasFinishedRace())
                {
                    btn_texture = powerup->getIcon()->getTexture();
                }
                else
                {
                    can_be_pressed = false;
                    btn_texture = NULL;
                }
                break;
            }
            case MultitouchButtonType::BUTTON_NITRO:
            {
                if (kart->getEnergy() > 0)
                {
                    btn_texture = m_nitro_tex;
                }
                else
                {
                    can_be_pressed = false;
                    btn_texture = m_nitro_empty_tex;
                }
                break;
            }
            case MultitouchButtonType::BUTTON_LOOK_BACKWARDS:
                btn_texture = m_wing_mirror_tex;
                break;
            case MultitouchButtonType::BUTTON_RESCUE:
                btn_texture = m_thunderbird_reset_tex;
                break;
            case MultitouchButtonType::BUTTON_SKIDDING:
                btn_texture = m_drift_tex;
                break;
            case MultitouchButtonType::BUTTON_UP:
                btn_texture = m_accelerator_icon_tex;
                break;
            case MultitouchButtonType::BUTTON_CUSTOM:
                if (button->id == 1)
                {
                    btn_texture = m_up_tex;
                }
                else if (button->id == 2)
                {
                    btn_texture = m_down_tex;
                }
                else if (button->id == 3)
                {
                    btn_texture = m_wing_mirror_tex;
                }
                else if (button->id == 4)
                {
                    btn_texture = m_screen_tex;
                }
                break;
            default:
                break;
            }

            if (btn_texture)
            {
                video::ITexture* btn_bg = (can_be_pressed && button->pressed) ?
                                                        m_bg_button_focus_tex :
                                                        m_bg_button_tex;
                core::rect<s32> coords_bg(pos_zero, btn_bg->getSize());
                draw2DImage(btn_bg, btn_pos_bg, coords_bg, NULL, NULL, true);

                core::rect<s32> coords(pos_zero, btn_texture->getSize());
                draw2DImage(btn_texture, btn_pos, coords, NULL, NULL, true);
            }

#ifdef IOS_STK
            if (button->type == MultitouchButtonType::BUTTON_CUSTOM &&
                MotoricaStandaloneTraining::get()->usesSimulatedSignals())
            {
                const bool russian = motoricaUseRussian();
                const char* label = button->id == 1 ?
                    (russian ? "ОТКР" : "OPEN") : button->id == 2 ?
                    (russian ? "ЗАКР" : "CLOSE") : button->id == 3 ?
                    (russian ? "СВЯЗЬ" : "LINK") :
                    (russian ? "АВТО" : "AUTO");
                core::rect<s32> label_rect(button->x - button->width / 3,
                    button->y + button->height * 3 / 4,
                    button->x + button->width * 4 / 3,
                    button->y + button->height * 5 / 4);
                GUIEngine::getSmallFont()->draw(
                    StringUtils::utf8ToWide(label), label_rect,
                    video::SColor(255, 235, 241, 255), true, true);
            }
#endif

            if (button->type == MultitouchButtonType::BUTTON_NITRO &&
                m_race_gui != NULL)
            {
                float scale = UserConfigParams::m_multitouch_scale *
                    (float)(irr_driver->getActualScreenSize().Height) / 760.0f;

                m_race_gui->drawEnergyMeter(int(button->x + button->width * 1.15f),
                                            int(button->y + button->height * 1.15f),
                                            kart, viewport,
                                            core::vector2df(scale, scale));
            }
            else if (button->type == MultitouchButtonType::BUTTON_FIRE &&
                     kart->getPowerup()->getNum() > 1 &&
                     !kart->hasFinishedRace() &&
                     m_gui_action == false)
            {
                gui::ScalableFont* font = GUIEngine::getHighresDigitFont();
                core::rect<s32> pos((int)(button->x),
                                    (int)(button->y),
                                    (int)(button->x + button->width/2),
                                    (int)(button->y + button->height/2));
                font->setScale(UserConfigParams::m_multitouch_scale);
                font->setBlackBorder(true);
                font->draw(core::stringw(kart->getPowerup()->getNum()), pos,
                           video::SColor(255, 255, 255, 255));
                font->setScale(1.0f);
                font->setBlackBorder(false);
            }
        }
    }

#ifdef IOS_STK
    MotoricaStandaloneTraining* training = MotoricaStandaloneTraining::get();
    if (training->isActive())
    {
        const int width = irr_driver->getActualScreenSize().Width;
        const int height = irr_driver->getActualScreenSize().Height;
        const float world_time = World::getWorld()->getTime();
        const float demo_elapsed = training->getDemoElapsed(world_time);
        const float exercise_elapsed = training->getExerciseElapsed(world_time);
        const SimulatedSignalFrame& signal = training->getSignal();
        core::rect<s32> panel(width / 2 - width / 4, height / 35,
                              width / 2 + width / 4, height / 5);
        GL32_draw2DRectangle(video::SColor(205, 8, 16, 35), panel);

        const bool russian = motoricaUseRussian();
        std::string title = "SIGNAL LAB | " + motoricaExerciseLabel(
            training->getExercise(), russian);
        if (training->usesSimulatedSignals())
        {
            title += " | ";
            title += motoricaPhaseLabel(training->getPhaseName(demo_elapsed),
                                        russian);
        }
        title += " | " + StringUtils::toString(
            training->getProgressCount(exercise_elapsed)) + "/" +
            StringUtils::toString(training->getProgressTotal());
        gui::ScalableFont* font = GUIEngine::getSmallFont();
        core::rect<s32> title_rect(panel.UpperLeftCorner.X,
            panel.UpperLeftCorner.Y + 4, panel.LowerRightCorner.X,
            panel.UpperLeftCorner.Y + height / 18);
        font->draw(StringUtils::utf8ToWide(title), title_rect,
            video::SColor(255, 193, 255, 56), true, true);

        if (training->usesSimulatedSignals())
        {
            const int bar_y = panel.UpperLeftCorner.Y + height / 16;
            const int bar_height = std::max(8, height / 70);
            const int bar_width = panel.getWidth() / 3;
            const int gap = panel.getWidth() / 12;
            core::rect<s32> open_bg(panel.UpperLeftCorner.X + gap, bar_y,
                panel.UpperLeftCorner.X + gap + bar_width, bar_y + bar_height);
            core::rect<s32> close_bg(panel.LowerRightCorner.X - gap - bar_width,
                bar_y, panel.LowerRightCorner.X - gap, bar_y + bar_height);
            GL32_draw2DRectangle(video::SColor(255, 30, 38, 62), open_bg);
            GL32_draw2DRectangle(video::SColor(255, 30, 38, 62), close_bg);
            open_bg.LowerRightCorner.X = open_bg.UpperLeftCorner.X +
                (int)(bar_width * signal.open_level / 255.0f);
            close_bg.LowerRightCorner.X = close_bg.UpperLeftCorner.X +
                (int)(bar_width * signal.close_level / 255.0f);
            GL32_draw2DRectangle(video::SColor(255, 190, 66, 255), open_bg);
            GL32_draw2DRectangle(video::SColor(255, 0, 222, 255), close_bg);
        }

        std::string direction_line;
        if (training->usesSimulatedSignals())
        {
            const float calculated = training->getCalculatedAxis();
            const char* direction = calculated < -0.15f ? "◀" :
                                    calculated > 0.15f ? "▶" : "●";
            direction_line = (russian ? "СИГНАЛ: " : "SIGNAL: ") +
                             std::string(direction);
        }
        if (training->getExercise() != StandaloneExerciseID::Precision)
        {
            const float target = training->getTargetAxis(exercise_elapsed);
            const char* target_direction = target < -0.15f ? "◀" :
                                           target > 0.15f ? "▶" : "●";
            if (!direction_line.empty())
                direction_line += "    ";
            direction_line += (russian ? "ЦЕЛЬ: " : "TARGET: ") +
                              std::string(target_direction);
        }
        if (!direction_line.empty())
        {
            core::rect<s32> target_rect(panel.UpperLeftCorner.X,
                panel.UpperLeftCorner.Y + height / 10,
                panel.LowerRightCorner.X, panel.LowerRightCorner.Y);
            font->draw(StringUtils::utf8ToWide(direction_line), target_rect,
                video::SColor(255, 0, 222, 255), true, true);
        }

        if (training->isTrainingPaused(world_time))
        {
            const core::rect<s32> pause_panel(width / 2 - width / 5,
                panel.LowerRightCorner.Y + height / 60,
                width / 2 + width / 5,
                panel.LowerRightCorner.Y + height / 11);
            GL32_draw2DRectangle(video::SColor(228, 92, 12, 28), pause_panel);
            font->draw(StringUtils::utf8ToWide(russian ?
                "ТРЕНИРОВКА НА ПАУЗЕ" : "TRAINING PAUSED"), pause_panel,
                video::SColor(255, 255, 255, 255), true, true);
        }
    }
#endif
#endif
} // draw
