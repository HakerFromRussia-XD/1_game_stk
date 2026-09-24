// Fluxara Drift - iOS campaign circuit selection

#ifndef HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP
#define HEADER_FLUXARA_CAMPAIGN_SCREEN_HPP

#include "guiengine/screen.hpp"
#include "states_screens/fluxara_event.hpp"

#include <string>
#include <memory>
#include <vector>

namespace GUIEngine { class Widget; }
namespace irr { namespace video { class ITexture; } }
namespace Online { class HTTPRequest; }

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
    unsigned int m_completed_count = 0;
    bool m_progress_cached = false;
    float m_auto_start_delay = -1.0f;
    irr::video::ITexture* m_art[6] = {};
    irr::video::ITexture* m_download_base = nullptr;
    irr::video::ITexture* m_download_arrow = nullptr;
    std::vector<irr::video::ITexture*> m_cards;
    // A card remains visible even while its map is not in the IPA.  The
    // catalog provides the human title and the immutable HTTPS pack URL.
    std::vector<std::string> m_titles;
    std::vector<std::string> m_download_urls;
    std::vector<double> m_download_sizes;
    std::shared_ptr<Online::HTTPRequest> m_download_request;
    std::string m_downloading_track;
    void layoutControls();
    void populateTrackList();
    void releaseCardTextures();
    void loadCardTexture(unsigned selected);
    void activateSelectedTrack();
    void openTrack(unsigned selected);
    void startDownload(unsigned selected);
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
