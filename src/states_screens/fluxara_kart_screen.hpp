// Fluxara Drift - iOS kart selection

#ifndef HEADER_FLUXARA_KART_SCREEN_HPP
#define HEADER_FLUXARA_KART_SCREEN_HPP

#include "guiengine/screen.hpp"

#include <string>
#include <vector>

namespace GUIEngine { class Widget; }
class Track;

class FluxaraKartScreen : public GUIEngine::Screen,
                         public GUIEngine::ScreenSingleton<FluxaraKartScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraKartScreen>;
    FluxaraKartScreen();

    Track* m_track = NULL;
    int m_laps = 3;
    std::vector<std::string> m_karts;
    unsigned m_selected_kart = 0;

    void updateKartPreview();
    void startRace();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;

    void setRace(Track* track, int laps);
};

#endif
