//  Motorica Kart standalone product hub

#ifndef HEADER_MOTORICA_HUB_SCREEN_HPP
#define HEADER_MOTORICA_HUB_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }

class MotoricaHubScreen : public GUIEngine::Screen,
                          public GUIEngine::ScreenSingleton<MotoricaHubScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<MotoricaHubScreen>;
    MotoricaHubScreen();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;
};

class MotoricaExerciseScreen : public GUIEngine::Screen,
        public GUIEngine::ScreenSingleton<MotoricaExerciseScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<MotoricaExerciseScreen>;
    MotoricaExerciseScreen();

    void updateVisibleControls();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
};

class MotoricaHistoryScreen : public GUIEngine::Screen,
        public GUIEngine::ScreenSingleton<MotoricaHistoryScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<MotoricaHistoryScreen>;
    MotoricaHistoryScreen();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
};

#endif
