//  SuperTuxKart - a fun racing game with go-kart

#ifndef HEADER_MOTORICA_GAME_CONTROL_HPP
#define HEADER_MOTORICA_GAME_CONTROL_HPP

#include <atomic>
#include <stdint.h>

class Controller;

class MotoricaGameControl
{
private:
    std::atomic<int> m_open_level;
    std::atomic<int> m_close_level;
    std::atomic<bool> m_connected;
    std::atomic<uint64_t> m_receive_time_ms;
    std::atomic<uint64_t> m_seq;
    std::atomic<bool> m_loss_handled;
    bool m_was_active;

    MotoricaGameControl();
    void releaseSteering(Controller* controller);

public:
    static MotoricaGameControl* get();

    void updateSnapshot(int open_level, int close_level, bool connected,
                        uint64_t timestamp_ms, uint64_t seq);
    void apply(Controller* controller);

    int getOpenLevel() const;
    int getCloseLevel() const;
    bool isConnected() const;
};

#endif
