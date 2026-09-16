// Fluxara Drift - iOS settings

#ifndef HEADER_FLUXARA_SETTINGS_SCREEN_HPP
#define HEADER_FLUXARA_SETTINGS_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }

class FluxaraSettingsScreen
    : public GUIEngine::Screen,
      public GUIEngine::ScreenSingleton<FluxaraSettingsScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraSettingsScreen>;
    FluxaraSettingsScreen();

    void refreshLabels();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void tearDown() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;
};

#endif
