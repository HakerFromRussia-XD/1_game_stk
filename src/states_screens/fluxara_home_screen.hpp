//  Fluxara Drift - public iOS racing campaign home

#ifndef HEADER_FLUXARA_HOME_SCREEN_HPP
#define HEADER_FLUXARA_HOME_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }

class FluxaraHomeScreen : public GUIEngine::Screen,
                         public GUIEngine::ScreenSingleton<FluxaraHomeScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraHomeScreen>;
    FluxaraHomeScreen();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;
};

#endif
