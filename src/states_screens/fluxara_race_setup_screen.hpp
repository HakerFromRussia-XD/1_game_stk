// Fluxara Drift - iOS race settings

#ifndef HEADER_FLUXARA_RACE_SETUP_SCREEN_HPP
#define HEADER_FLUXARA_RACE_SETUP_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }
namespace irr { namespace video { class ITexture; } }
class Track;

class FluxaraRaceSetupScreen
    : public GUIEngine::Screen,
      public GUIEngine::ScreenSingleton<FluxaraRaceSetupScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraRaceSetupScreen>;
    FluxaraRaceSetupScreen();

    Track* m_track = NULL;
    int m_laps = 3;
    int m_ai_karts = 3;
    int m_difficulty = 1;
    float m_auto_start_delay = -1.0f;
    std::string m_event_id;
    std::string m_mode = "normal";
    irr::core::stringw m_unavailable_reason;
    irr::video::ITexture* m_art[10] = {};
    irr::video::ITexture* m_preview = nullptr;
    void layoutControls();

    void updateRaceDetails();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void onUpdate(float dt) OVERRIDE;
    void onDraw(float dt) OVERRIDE;
    void onResize() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;

    void setTrack(Track* track, const std::string& mode = "normal",
                  const std::string& event_id = "");
};

#endif
