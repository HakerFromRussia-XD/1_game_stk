// Fluxara Drift - iOS campaign circuit selection

#ifndef HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP
#define HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP

#include "guiengine/screen.hpp"
#include "states_screens/fluxara_event.hpp"

#include <string>
#include <vector>

namespace GUIEngine { class Widget; }
namespace irr { namespace video { class ITexture; } }

class FluxaraCampaignScreen : public GUIEngine::Screen,
                             public GUIEngine::ScreenSingleton<FluxaraCampaignScreen>
{
private:
    friend class GUIEngine::ScreenSingleton<FluxaraCampaignScreen>;
    FluxaraCampaignScreen();

    std::vector<std::string> m_tracks;
    std::vector<FluxaraEvent> m_events;
    std::vector<FluxaraSegment> m_segments;
    unsigned m_selected_track = 0;
    std::string m_next_after;
    std::string m_next_after_event;
    // A stable campaign ID can arrive from the iOS launch bridge before the
    // screen has parsed its manifest.  Keep it until init() resolves it.
    std::string m_focus_event_id;
    int m_last_scroll_pos = 0;
    float m_scroll_idle_time = 1.0f;
    float m_auto_start_delay = -1.0f;
    irr::video::ITexture* m_art[6] = {};
    std::vector<irr::video::ITexture*> m_cards;
    void layoutControls();
    void populateTrackList();
    void openTrack(unsigned selected);
    const FluxaraSegment* segmentFor(unsigned selected) const;
    unsigned int completedCount() const;
    bool isEventUnlocked(unsigned selected) const;

public:
    void loadedFromFile() OVERRIDE;
    void init() OVERRIDE;
    void onDraw(float dt) OVERRIDE;
    void onUpdate(float dt) OVERRIDE;
    void onResize() OVERRIDE;
    void eventCallback(GUIEngine::Widget* widget, const std::string& name,
                       const int player_id) OVERRIDE;
    bool onEscapePressed() OVERRIDE;
    void showNextAfter(const std::string& track_ident);
    void showNextAfterEvent(const std::string& event_id);
    void showEvent(const std::string& event_id);
};

#endif
