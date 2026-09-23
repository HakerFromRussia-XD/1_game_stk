// Fluxara Drift - iOS settings

#ifndef HEADER_FLUXARA_SETTINGS_SCREEN_HPP
#define HEADER_FLUXARA_SETTINGS_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }
namespace irr { namespace video { class ITexture; } }

class FluxaraSettingsScreen
    : public GUIEngine::Screen,
      public GUIEngine::ScreenSingleton<FluxaraSettingsScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraSettingsScreen>;
    FluxaraSettingsScreen();

    void refreshLabels();
    void layoutControls();
    irr::video::ITexture* m_art[9] = {};
    bool m_return_to_paused_race = false;

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void tearDown() OVERRIDE;
    void onResize() OVERRIDE;
    void onDraw(float dt) OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    // Opens settings above the race stack; Back restores the pause modal.
    void openFromPausedRace();
    bool onEscapePressed() OVERRIDE;
};

#endif
