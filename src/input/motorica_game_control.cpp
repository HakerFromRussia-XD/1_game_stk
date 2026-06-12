//  SuperTuxKart - a fun racing game with go-kart

#include "input/motorica_game_control.hpp"

#include <algorithm>
#include <cmath>

#include "config/user_config.hpp"
#include "guiengine/engine.hpp"
#include "input/input.hpp"
#include "karts/controller/controller.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/time.hpp"

namespace
{
    const uint64_t STALE_TIMEOUT_MS = 500;
    const int DEADZONE = 8;
    const int ACTION_MAX_VALUE = 32768;
}

MotoricaGameControl::MotoricaGameControl()
    : m_open_level(0), m_close_level(0), m_connected(false),
      m_receive_time_ms(0), m_seq(0), m_loss_handled(false),
      m_was_active(false)
{
}

MotoricaGameControl* MotoricaGameControl::get()
{
    static MotoricaGameControl instance;
    return &instance;
}

void MotoricaGameControl::updateSnapshot(int open_level, int close_level,
                                         bool connected,
                                         uint64_t timestamp_ms, uint64_t seq)
{
    (void)timestamp_ms;
    m_open_level.store(std::max(0, std::min(open_level, 255)));
    m_close_level.store(std::max(0, std::min(close_level, 255)));
    m_connected.store(connected);
    m_receive_time_ms.store(StkTime::getMonoTimeMs());
    m_seq.store(seq);
    if (connected)
        m_loss_handled.store(false);
}

void MotoricaGameControl::releaseSteering(Controller* controller)
{
    if (!controller)
        return;
    controller->action(PA_STEER_LEFT, 0);
    controller->action(PA_STEER_RIGHT, 0);
}

void MotoricaGameControl::apply(Controller* controller)
{
    if (!controller)
        return;

    if (!UserConfigParams::m_motorica_emg_steering)
        return;

    const uint64_t now = StkTime::getMonoTimeMs();
    const uint64_t received = m_receive_time_ms.load();
    const bool active = m_connected.load() &&
        received > 0 && now - received <= STALE_TIMEOUT_MS;

    if (!active)
    {
        releaseSteering(controller);
        if (m_was_active && !m_loss_handled.load() &&
            StateManager::get()->getGameState() == GUIEngine::GAME)
        {
            StateManager::get()->escapePressed();
            m_loss_handled.store(true);
        }
        m_was_active = false;
        return;
    }

    int diff = m_close_level.load() - m_open_level.load();
    if (UserConfigParams::m_motorica_emg_inverted)
        diff = -diff;

    if (std::abs(diff) <= DEADZONE)
    {
        releaseSteering(controller);
    }
    else if (diff < 0)
    {
        const int value = std::min(ACTION_MAX_VALUE,
            (std::abs(diff) * ACTION_MAX_VALUE) / 255);
        controller->action(PA_STEER_RIGHT, 0);
        controller->action(PA_STEER_LEFT, value);
    }
    else
    {
        const int value = std::min(ACTION_MAX_VALUE,
            (diff * ACTION_MAX_VALUE) / 255);
        controller->action(PA_STEER_LEFT, 0);
        controller->action(PA_STEER_RIGHT, value);
    }

    m_was_active = true;
    m_loss_handled.store(false);
}

int MotoricaGameControl::getOpenLevel() const
{
    return m_open_level.load();
}

int MotoricaGameControl::getCloseLevel() const
{
    return m_close_level.load();
}

bool MotoricaGameControl::isConnected() const
{
    const uint64_t received = m_receive_time_ms.load();
    return m_connected.load() && received > 0 &&
        StkTime::getMonoTimeMs() - received <= STALE_TIMEOUT_MS;
}
