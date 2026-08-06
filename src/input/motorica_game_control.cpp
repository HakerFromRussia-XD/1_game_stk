//  SuperTuxKart - a fun racing game with go-kart

#include "input/motorica_game_control.hpp"

#include <algorithm>
#include <cmath>

#include "config/user_config.hpp"
#include "guiengine/engine.hpp"
#include "guiengine/modaldialog.hpp"
#include "input/input.hpp"
#include "karts/controller/controller.hpp"
#ifdef ANDROID
#include "SDL_events.h"
#include "states_screens/dialogs/race_paused_dialog.hpp"
#endif
#include "states_screens/state_manager.hpp"
#include "utils/time.hpp"
#include "utils/log.hpp"
#ifdef IOS_STK
#include "input/motorica_game_control_ios.hpp"
#endif

namespace
{
    const uint64_t STALE_TIMEOUT_MS = 500;
    const int DEADZONE = 8;
    const int ACTION_MAX_VALUE = 32768;

#ifdef ANDROID
    Uint32 getMotoricaConnectionRestoreEventType()
    {
        static const Uint32 event_type = SDL_RegisterEvents(1);
        return event_type;
    }

    void scheduleMotoricaConnectionRestoreUiAndroid()
    {
        const Uint32 event_type = getMotoricaConnectionRestoreEventType();
        if (event_type == (Uint32)-1)
        {
            Log::error("MotoricaGameControl",
                "[BLE stk-game debug] android recovery event registration failed");
            return;
        }

        SDL_Event event = {};
        event.type = event_type;
        if (SDL_PushEvent(&event) <= 0)
        {
            Log::error("MotoricaGameControl",
                "[BLE stk-game debug] android recovery event enqueue failed: %s",
                SDL_GetError());
        }
    }
#endif
}

#ifdef ANDROID
extern "C" bool handle_motorica_game_control_event(SDL_Event& event)
{
    const Uint32 event_type = getMotoricaConnectionRestoreEventType();
    if (event_type == (Uint32)-1 || event.type != event_type)
        return false;

    MotoricaGameControl::get()->flushConnectionRestoreUi();
    return true;
}
#endif

MotoricaGameControl::MotoricaGameControl()
    : m_open_level(0), m_close_level(0), m_connected(false),
      m_receive_time_ms(0), m_seq(0), m_loss_handled(false),
      m_pause_pending(false), m_restore_pending(false), m_was_active(false)
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
    if (connected && m_loss_handled.load() &&
        !m_restore_pending.exchange(true))
    {
        Log::info("MotoricaGameControl",
            "[BLE stk-game debug] native recovery pending seq=%llu",
            (unsigned long long)seq);
#ifdef IOS_STK
        flushMotoricaConnectionRestoreUiIOS();
#elif defined(ANDROID)
        scheduleMotoricaConnectionRestoreUiAndroid();
#endif
    }
    if (!connected || seq <= 3 || seq % 30 == 0)
    {
        Log::info("MotoricaGameControl",
            "[BLE stk-game debug] native update seq=%llu open=%d close=%d connected=%d",
            (unsigned long long)seq, m_open_level.load(),
            m_close_level.load(), connected ? 1 : 0);
    }
}

void MotoricaGameControl::handleConnectionLost(uint64_t seq, uint64_t age_ms,
                                               const char* reason,
                                               bool pause_game)
{
    if (StateManager::get()->getGameState() != GUIEngine::GAME)
        return;
    if (m_loss_handled.exchange(true))
        return;

    Log::info("MotoricaGameControl",
        "[BLE stk-game debug] native connection lost seq=%llu reason=%s ageMs=%llu",
        (unsigned long long)seq, reason, (unsigned long long)age_ms);

    m_pause_pending.store(true);
    if (pause_game)
        flushConnectionLossUi();
}

void MotoricaGameControl::checkConnectionTimeout()
{
    const uint64_t received = m_receive_time_ms.load();
    if (received == 0)
        return;

    const uint64_t now = StkTime::getMonoTimeMs();
    const uint64_t age_ms = now > received ? now - received : 0;
    if (m_connected.load() && age_ms <= STALE_TIMEOUT_MS)
        return;

    handleConnectionLost(m_seq.load(), age_ms,
        m_connected.load() ? "stale" : "disconnected", false);
}

void MotoricaGameControl::flushConnectionLossUi()
{
    if (!m_pause_pending.exchange(false))
        return;

    if (StateManager::get()->getGameState() == GUIEngine::GAME)
        StateManager::get()->escapePressed();
#ifdef IOS_STK
    showMotoricaConnectionLostDialogIOS();
#endif
    Log::info("MotoricaGameControl",
        "[BLE stk-game debug] native connection loss ui shown seq=%llu",
        (unsigned long long)m_seq.load());
}

void MotoricaGameControl::flushConnectionRestoreUi()
{
    if (!m_restore_pending.exchange(false))
        return;

#ifdef IOS_STK
    dismissMotoricaConnectionLostDialogIOS();
    if (GUIEngine::ModalDialog::isADialogActive())
        GUIEngine::ModalDialog::dismiss();
#elif defined(ANDROID)
    if (dynamic_cast<RacePausedDialog*>(GUIEngine::ModalDialog::getCurrent()))
        GUIEngine::ModalDialog::dismiss();
#endif
    m_pause_pending.store(false);
    m_loss_handled.store(false);
    Log::info("MotoricaGameControl",
        "[BLE stk-game debug] native recovery applied seq=%llu",
        (unsigned long long)m_seq.load());
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
    {
        static bool logged_disabled = false;
        if (!logged_disabled)
        {
            Log::info("MotoricaGameControl",
                "[BLE stk-game debug] apply disabled motorica_emg_steering=0");
            logged_disabled = true;
        }
        return;
    }

    const uint64_t now = StkTime::getMonoTimeMs();
    const uint64_t received = m_receive_time_ms.load();
    const bool active = m_connected.load() &&
        received > 0 && now - received <= STALE_TIMEOUT_MS;
    const uint64_t seq = m_seq.load();
    static uint64_t last_logged_apply_seq = (uint64_t)-1;

    if (!active)
    {
        releaseSteering(controller);
        if (seq != last_logged_apply_seq &&
            (seq <= 3 || seq % 30 == 0 || m_was_active))
        {
            last_logged_apply_seq = seq;
            Log::info("MotoricaGameControl",
                "[BLE stk-game debug] apply inactive seq=%llu connected=%d ageMs=%llu",
                (unsigned long long)seq, m_connected.load() ? 1 : 0,
                (unsigned long long)(received > 0 ? now - received : 0));
        }
        if (received > 0)
            handleConnectionLost(seq, received > 0 ? now - received : 0,
                m_connected.load() ? "stale" : "disconnected", true);
        m_was_active = false;
        return;
    }

    flushConnectionRestoreUi();

    int diff = m_close_level.load() - m_open_level.load();
    if (UserConfigParams::m_motorica_emg_inverted)
        diff = -diff;

    if (std::abs(diff) <= DEADZONE)
    {
        releaseSteering(controller);
        if (seq != last_logged_apply_seq &&
            (seq <= 3 || seq % 30 == 0))
        {
            last_logged_apply_seq = seq;
            Log::info("MotoricaGameControl",
                "[BLE stk-game debug] apply deadzone seq=%llu diff=%d open=%d close=%d",
                (unsigned long long)seq, diff, m_open_level.load(),
                m_close_level.load());
        }
    }
    else if (diff < 0)
    {
        const int value = std::min(ACTION_MAX_VALUE,
            (std::abs(diff) * ACTION_MAX_VALUE) / 255);
        controller->action(PA_STEER_LEFT, 0);
        controller->action(PA_STEER_RIGHT, value);
        if (seq != last_logged_apply_seq &&
            (seq <= 3 || seq % 30 == 0))
        {
            last_logged_apply_seq = seq;
            Log::info("MotoricaGameControl",
                "[BLE stk-game debug] apply left seq=%llu diff=%d value=%d open=%d close=%d",
                (unsigned long long)seq, diff, value, m_open_level.load(),
                m_close_level.load());
        }
    }
    else
    {
        const int value = std::min(ACTION_MAX_VALUE,
            (diff * ACTION_MAX_VALUE) / 255);
        controller->action(PA_STEER_RIGHT, 0);
        controller->action(PA_STEER_LEFT, value);
        if (seq != last_logged_apply_seq &&
            (seq <= 3 || seq % 30 == 0))
        {
            last_logged_apply_seq = seq;
            Log::info("MotoricaGameControl",
                "[BLE stk-game debug] apply right seq=%llu diff=%d value=%d open=%d close=%d",
                (unsigned long long)seq, diff, value, m_open_level.load(),
                m_close_level.load());
        }
    }

    m_was_active = true;
}

int MotoricaGameControl::getOpenLevel() const
{
    return m_open_level.load();
}

int MotoricaGameControl::getCloseLevel() const
{
    return m_close_level.load();
}

uint64_t MotoricaGameControl::getSeq() const
{
    return m_seq.load();
}

float MotoricaGameControl::getSteeringAxis() const
{
    int diff = m_close_level.load() - m_open_level.load();
    if (UserConfigParams::m_motorica_emg_inverted)
        diff = -diff;
    if (std::abs(diff) <= DEADZONE)
        return 0.0f;
    return std::max(-1.0f, std::min(1.0f, (float)diff / 255.0f));
}

bool MotoricaGameControl::isConnected() const
{
    const uint64_t received = m_receive_time_ms.load();
    return m_connected.load() && received > 0 &&
        StkTime::getMonoTimeMs() - received <= STALE_TIMEOUT_MS;
}
