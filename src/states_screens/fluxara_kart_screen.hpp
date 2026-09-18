// Fluxara Drift - iOS kart selection

#ifndef HEADER_FLUXARA_KART_SCREEN_HPP
#define HEADER_FLUXARA_KART_SCREEN_HPP

#include "guiengine/screen.hpp"

#include <string>
#include <vector>
namespace irr { namespace video { class ITexture; } }

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
    int m_num_karts = 4;
    std::string m_mode = "normal";
    std::vector<std::string> m_karts;
    unsigned m_selected_kart = 0;
    irr::core::stringw m_kart_name;
    int m_stat_segments[4] = {};
    irr::video::ITexture* m_stats_panel = nullptr;
    irr::video::ITexture* m_stat_icons[4] = {};
    irr::video::ITexture* m_stat_fills[4] = {};
    irr::video::ITexture* m_stat_empty = nullptr;
    irr::video::ITexture* m_garage_art[6] = {};
    void layoutControls();

    void updateKartPreview();
    void startRace();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void onDraw(float dt) OVERRIDE;
    void onResize() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;

    void setRace(Track* track, int laps, int karts, const std::string& mode = "normal");
};

#endif
