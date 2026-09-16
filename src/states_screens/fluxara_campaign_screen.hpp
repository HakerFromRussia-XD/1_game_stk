// Fluxara Drift - iOS campaign circuit selection

#ifndef HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP
#define HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP

#include "guiengine/screen.hpp"

namespace GUIEngine { class Widget; }

class FluxaraCampaignScreen : public GUIEngine::Screen,
                             public GUIEngine::ScreenSingleton<FluxaraCampaignScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraCampaignScreen>;
    FluxaraCampaignScreen();

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;
};

#endif
