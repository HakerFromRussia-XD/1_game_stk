//  Motorica Kart product and open-source information

#ifndef HEADER_MOTORICA_ABOUT_SCREEN_HPP
#define HEADER_MOTORICA_ABOUT_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }

class MotoricaAboutScreen : public GUIEngine::Screen,
                            public GUIEngine::ScreenSingleton<MotoricaAboutScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<MotoricaAboutScreen>;
    MotoricaAboutScreen();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
};

#endif
