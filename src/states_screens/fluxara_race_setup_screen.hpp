// Fluxara Drift - iOS race settings

#ifndef HEADER_FLUXARA_RACE_SETUP_SCREEN_HPP
#define HEADER_FLUXARA_RACE_SETUP_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }
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

    void updateRaceDetails();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;

    void setTrack(Track* track);
};

#endif
