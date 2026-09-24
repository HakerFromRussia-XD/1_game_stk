// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "config/player_manager.hpp"
#include "config/player_profile.hpp"
#include "config/user_config.hpp"
#include "addons/addon.hpp"
#include "addons/zip.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/list_widget.hpp"
#include "io/xml_node.hpp"
#include "io/file_manager.hpp"
#include "online/http_request.hpp"
#include "online/request_manager.hpp"
#include "states_screens/dialogs/message_dialog.hpp"
#include <IGUIScrollBar.h>
#include <memory>
#include "states_screens/fluxara_race_setup_screen.hpp"
#include "states_screens/fluxara_home_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"
#ifdef IOS_FLUXARA_DRIFT
#include "utils/fluxara_device_validation_ios.hpp"
#endif
#include "tracks/track.hpp"
#include "tracks/track_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/extract_mobile_assets.hpp"
#include "utils/translation.hpp"

#include <sstream>
#include <algorithm>
#include <cmath>
#include <map>
#include <array>
#include <chrono>
#include <cstdlib>
#include "utils/log.hpp"

using namespace GUIEngine;

namespace
{
// Tracks are data-only packages.  They are unpacked into the normal add-ons
// search root, so reinitialising the manager makes a newly downloaded circuit
// indistinguishable from a bundled one without ever modifying the IPA.
class FluxaraTrackDownloadRequest final : public Online::HTTPRequest
{
private:
    std::string m_track_id;
    bool m_install_error = true;

    void afterOperation() OVERRIDE
    {
        Online::HTTPRequest::afterOperation();
        if (isCancelled() || Online::HTTPRequest::hadDownloadError())
            return;
        if (!file_manager->fileExists(getFileName()))
            return;

        const std::string destination =
            file_manager->getAddonsFile("tracks/") + m_track_id;
        // A prior interrupted archive must not look installed.  The remote
        // ZIP is checked for traversal, symlinks and executable extensions
        // by extract_zip(data_only=true) before it writes any file.
        file_manager->removeDirectory(destination);
        file_manager->checkAndCreateDirForAddons(destination);
        m_install_error = !extract_zip(getFileName(), destination,
                                       true/*recursive*/, true/*data_only*/);
        file_manager->removeFile(getFileName());
    }

public:
    FluxaraTrackDownloadRequest(const std::string& track_id,
                                const std::string& url,
                                double expected_size)
        : Online::HTTPRequest("fluxara-track-" + track_id + ".zip",
                              /*priority*/5), m_track_id(track_id)
    {
        if (StringUtils::startsWith(url, "https://"))
        {
            setURL(url);
            m_install_error = false;
        }
        else
            m_install_error = true;
        // GitHub's redirect does not always expose Content-Length to
        // NSURLSession. Keep the catalogued archive size as a progress hint.
        if (expected_size > 0.0)
            setTotalSize(expected_size);
        setDownloadAssetsRequest(true);
    }

    bool hadDownloadError() const OVERRIDE
    {
        return Online::HTTPRequest::hadDownloadError() || m_install_error;
    }
};

// The campaign manifest names bundle tracks by their directory identifier.
// TrackManager deliberately prefixes a track installed under Addons with
// "addon_" to avoid colliding with a bundled map.  Accept both forms here:
// otherwise a perfectly extracted package is reported as absent, which used
// to show a false install-error dialog and trigger another download.
static Track* campaignTrack(const std::string& track_id)
{
    Track* track = track_manager->getTrack(track_id);
    return track ? track :
        track_manager->getTrack(Addon::createAddonId(track_id));
}

static void drawTrackDownloadControl(const FluxaraUI::Canvas& canvas,
                                     irr::video::ITexture* base,
                                     irr::video::ITexture* arrow,
                                     float x, float y, float progress,
                                     const irr::core::recti& clip)
{
    constexpr float control_size = 66.1476f;
    constexpr float arrow_width = 23.0748f;
    constexpr float arrow_height = 26.9205f;
    const float radius = 30.574f * canvas.scale;
    const irr::core::position2di center(
        int(std::lround(canvas.x + x * canvas.scale)),
        int(std::lround(canvas.y + y * canvas.scale)));
    // The base and arrow are exported Figma layers at their design size. Do
    // not draw any blue segment until bytes have actually arrived: an idle
    // circuit must begin as an empty loader rather than a fake partial state.
    canvas.image(base, x - control_size * .5f, y - control_size * .5f,
                 control_size, control_size, false, 255, &clip);

    if (progress > 0.0f)
    {
        // Vertex-coloured triangles use the Vulkan driver's white texture.
        // No allocations or texture uploads are needed as the arc grows.
        const float completed = std::min(1.0f, std::max(0.0f, progress));
        constexpr float pi = 3.14159265358979323846f;
        const int steps = std::max(1, int(std::ceil(96.0f * completed)));
        const float inner = radius - 2.5f * canvas.scale;
        const float outer = radius + 2.5f * canvas.scale;
        const irr::video::SColor cyan(255, 67, 166, 255);
        std::array<irr::video::S3DVertex, 194> vertices;
        std::array<irr::u16, 576> indices;
        for (int step = 0; step <= steps; ++step)
        {
            const float angle = -pi * .5f +
                2.0f * pi * completed * float(step) / float(steps);
            vertices[step * 2] = irr::video::S3DVertex(center.X + std::cos(angle) * outer,
                                  center.Y + std::sin(angle) * outer,
                                  0.0f, 0.0f, 0.0f, 0.0f, cyan, 0.0f, 0.0f);
            vertices[step * 2 + 1] = irr::video::S3DVertex(center.X + std::cos(angle) * inner,
                                  center.Y + std::sin(angle) * inner,
                                  0.0f, 0.0f, 0.0f, 0.0f, cyan, 0.0f, 0.0f);
        }
        for (int step = 0; step < steps; ++step)
        {
            const irr::u16 start = static_cast<irr::u16>(step * 2);
            // Screen-space clockwise winding: Vulkan culls back faces.
            // Outer -> inner -> next outer is counter-clockwise and would
            // discard every triangle even with a valid white texture.
            const irr::u16 triangle[] = {start, irr::u16(start + 2),
                irr::u16(start + 1), irr::u16(start + 2),
                irr::u16(start + 3), irr::u16(start + 1)};
            std::copy(triangle, triangle + 6, indices.begin() + step * 6);
        }
        irr::video::SMaterial material;
        material.setTexture(0, nullptr);
        material.MaterialType = irr::video::EMT_TRANSPARENT_VERTEX_ALPHA;
        material.ZWriteEnable = false;
        irr_driver->getVideoDriver()->setMaterial(material);
        if (CVS->isGLSL())
        {
            glEnable(GL_BLEND);
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        }
        irr_driver->getVideoDriver()->enableScissorTest(clip);
        draw2DVertexPrimitiveList(nullptr, vertices.data(),
            static_cast<irr::u32>((steps + 1) * 2), indices.data(),
            static_cast<irr::u32>(steps * 2),
            irr::video::EVT_STANDARD, irr::scene::EPT_TRIANGLES,
            irr::video::EIT_16BIT);
        if (CVS->isGLSL()) glDisable(GL_BLEND);
        irr_driver->getVideoDriver()->disableScissorTest();
    }
    canvas.image(arrow, x - arrow_width * .5f, y - arrow_height * .5f,
                 arrow_width, arrow_height, false, 255, &clip);
}
} // namespace

FluxaraCampaignScreen::FluxaraCampaignScreen()
    : Screen("fluxara_campaign.fluxara_driftgui")
{
}

void FluxaraCampaignScreen::loadedFromFile()
{
}

void FluxaraCampaignScreen::init()
{
    Screen::init();
    const char* files[] = {"race/background", "home/back-surface", "home/icon-back",
        "race/campaign-plate", "race/circuit-card", "race/summit-card"};
    for (int i=0;i<6;++i) m_art[i]=FluxaraUI::texture(files[i]);
    m_download_base = FluxaraUI::texture("race/download-progress-base");
    m_download_arrow = FluxaraUI::texture("race/download-arrow");
    layoutControls();

    releaseCardTextures();
    m_tracks.clear();
    m_events.clear();
    m_segments.clear();
    m_titles.clear();
    m_download_urls.clear();
    m_download_sizes.clear();
    m_progress_cached = false;
    struct CatalogEntry
    {
        std::string title;
        std::string url;
        double size = 0.0;
    };
    std::map<std::string, CatalogEntry> catalog;
    const std::string catalog_file =
        file_manager->getAsset("fluxara-track-catalog.xml");
    std::unique_ptr<XMLNode> catalog_root(catalog_file.empty() ? nullptr :
        file_manager->createXMLTree(catalog_file));
    if (catalog_root)
    {
        for (unsigned i = 0; i < catalog_root->getNumNodes(); ++i)
        {
            const XMLNode* node = catalog_root->getNode(i);
            if (node->getName() != "track") continue;
            std::string id, title, url, size;
            node->get("id", &id); node->get("title", &title);
            node->get("url", &url);
            node->get("size-bytes", &size);
            CatalogEntry entry;
            entry.title = title;
            entry.url = url;
            StringUtils::fromString(size, entry.size);
            if (!id.empty()) catalog[id] = entry;
        }
    }

    const std::string manifest = file_manager->getAsset("fluxara-campaign.xml");
    std::unique_ptr<XMLNode> campaign(manifest.empty() ? nullptr : file_manager->createXMLTree(manifest));
    if (campaign)
    {
        for (unsigned i=0;i<campaign->getNumNodes();++i)
        {
            const XMLNode* node=campaign->getNode(i);
            if (node->getName()=="segment")
            {
                FluxaraSegment segment;
                std::string title;
                int unlock_completed = 0;
                node->get("id", &segment.id);
                node->get("title", &title);
                node->get("unlock-completed", &unlock_completed);
                segment.title = _C("fluxara", title.c_str());
                segment.unlock_completed = std::max(0, unlock_completed);
                if (!segment.id.empty())
                    m_segments.push_back(segment);
                continue;
            }
            if (node->getName()!="event") continue;
            FluxaraEvent event;
            node->get("id",&event.id); node->get("mode",&event.mode);
            node->get("track",&event.track); node->get("segment",&event.segment);
            if(event.id.empty() || event.track.empty()) continue;
            m_events.push_back(event);
            m_tracks.push_back(event.track);
            const auto metadata = catalog.find(event.track);
            m_titles.push_back(metadata == catalog.end() ||
                metadata->second.title.empty() ? event.track :
                metadata->second.title);
            m_download_urls.push_back(metadata == catalog.end() ? "" :
                metadata->second.url);
            m_download_sizes.push_back(metadata == catalog.end() ? 0.0 :
                metadata->second.size);
        }
    }

    if (!m_next_after_event.empty())
    {
#ifdef IOS_FLUXARA_DRIFT
        if (FluxaraModes::autoCampaignValidation())
            fluxaraLogDeviceValidationMemory("after-unload", m_next_after_event);
#endif
        const std::vector<FluxaraEvent>::iterator current = std::find_if(
            m_events.begin(), m_events.end(), [this](const FluxaraEvent& event)
            {
                return event.id == m_next_after_event;
            });
        const bool has_current = current != m_events.end();
        const unsigned next = has_current ? unsigned(current - m_events.begin()) + 1u
                                          : 0u;
        m_next_after_event.clear();
        if (!has_current || next >= m_events.size())
        {
            // Reaching the end is valid only if every manifest event has a
            // saved cup.  Otherwise this is a broken sequential run, not a
            // completed campaign.
            FluxaraModes::autoCampaignFinished() = has_current &&
                completedCount() == m_events.size();
            FluxaraModes::autoCampaignFailed() = !FluxaraModes::autoCampaignFinished();
            m_auto_start_delay = -1.0f;
        }
        else if (isEventUnlocked(next))
        {
            m_selected_track = next;
        }
        else
        {
            FluxaraModes::autoCampaignFailed() = true;
            m_auto_start_delay = -1.0f;
        }
    }
    else if (!m_focus_event_id.empty())
    {
        const std::vector<FluxaraEvent>::iterator event = std::find_if(
            m_events.begin(), m_events.end(),
            [this](const FluxaraEvent& candidate)
            {
                return candidate.id == m_focus_event_id;
            });
        if (event != m_events.end())
            m_selected_track = unsigned(event - m_events.begin());
        m_focus_event_id.clear();
    }
    else if (!m_next_after.empty())
    {
        const std::vector<std::string>::iterator current = std::find(
            m_tracks.begin(), m_tracks.end(), m_next_after);
        if (current != m_tracks.end() && !m_tracks.empty())
        {
            const unsigned start = unsigned(current - m_tracks.begin());
            for (unsigned offset = 1; offset <= m_tracks.size(); ++offset)
            {
                const unsigned candidate = (start + offset) % m_tracks.size();
                if (isEventUnlocked(candidate))
                {
                    m_selected_track = candidate;
                    break;
                }
            }
        }
        m_next_after.clear();
    }
    else if (FluxaraModes::autoCampaignValidation())
    {
        // A stopped validation process may be rebuilt and launched again.
        // Resume at the first unresolved card instead of farming an already
        // saved cup or silently bypassing a failed result.
        const PlayerProfile* player = PlayerManager::getCurrentPlayer();
        for (unsigned i = 0; i < m_events.size(); ++i)
        {
            if (isEventUnlocked(i) &&
                (!player || player->getFluxaraCups(m_events[i].id) == 0))
            {
                m_selected_track = i;
                break;
            }
        }
    }
    else if (m_selected_track >= m_tracks.size())
        m_selected_track = 0;
    // The count is stable while this screen is visible. Caching avoids
    // repeatedly rebuilding the 50-event ID list during every scroll frame.
    m_completed_count = completedCount();
    m_progress_cached = true;
    populateTrackList();

    // The emulator-only campaign pass follows the normal screen sequence;
    // it simply supplies the same Start action after each selected card.
    // Do not push another screen from init(): the menu stack must first be
    // complete, otherwise the result screen can pop the application itself.
    m_auto_start_delay = FluxaraModes::autoCampaignValidation() &&
        !FluxaraModes::autoCampaignFailed() &&
        !FluxaraModes::autoCampaignFinished() ? 0.1f : -1.0f;
}

void FluxaraCampaignScreen::populateTrackList()
{
    ListWidget* list = getWidget<ListWidget>("tracks");
    list->clear();
    for (unsigned i = 0; i < m_tracks.size(); ++i)
        list->addItem(m_events[i].id, L"");

    auto* box = list->getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>();
    box->setDrawBackground(false);
    box->setItemHeight(std::max(1, int(std::lround(276.0f * FluxaraUI::Canvas().scale))));
    releaseCardTextures();
    m_cards.assign(m_tracks.size(), nullptr);
    // These are bounded 512px bundle thumbnails, not native track images.
    // Queue asynchronous decoding once; evicting during scrolling stalls
    // Vulkan's entire GPU queue and forces reloading on every reverse swipe.
    for (unsigned i = 0; i < m_tracks.size(); ++i)
        loadCardTexture(i);

    if (!m_tracks.empty())
    {
        const unsigned target = std::min(m_selected_track,
                                         unsigned(m_tracks.size() - 1));
        box->getScrollBar()->setPos(target * box->getItemHeight());
    }
    box->setTouchInertiaEnabled(true);
}

void FluxaraCampaignScreen::releaseCardTextures()
{
    for (irr::video::ITexture*& card : m_cards)
    {
        if (card)
            irr_driver->removeTexture(card);
        card = nullptr;
    }
    m_cards.clear();
}

void FluxaraCampaignScreen::loadCardTexture(unsigned selected)
{
    if (selected >= m_tracks.size() || selected >= m_cards.size() ||
        m_cards[selected])
        return;

    // Campaign cards never need a track's native screenshot.  Those can be
    // several thousand pixels wide after a pack has been installed, which
    // makes the same row noticeably slower simply because it was downloaded.
    // Every event has this lightweight, bundle-owned thumbnail, so its decode
    // cost and appearance stay identical before and after installation.
    m_cards[selected] = FluxaraUI::campaignPreviewTexture(
        file_manager->getAsset("gui/fluxara/campaign-previews/" +
                               m_tracks[selected] + ".jpg"));
}

void FluxaraCampaignScreen::activateSelectedTrack()
{
    ListWidget* list = getWidget<ListWidget>("tracks");
    const int selected = list->getSelectionID();
    if (selected < 0)
        return;
    list->setSelectionID(-1);
    openTrack(unsigned(selected));
}

void FluxaraCampaignScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>("back"));
    c.move(getWidget<ButtonWidget>("back"),21,58,50,50);
    ListWidget* list = getWidget<ListWidget>("tracks");
    c.move(list,20,124,320,644);
    if (auto* box = list->getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>())
        box->setItemHeight(std::max(1, int(std::lround(276.0f * c.scale))));
}

void FluxaraCampaignScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraCampaignScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    if (!c.isStable())
    {
        const auto size = irr_driver->getActualScreenSize();
        GL32_draw2DRectangle(irr::video::SColor(255,12,31,76),
            irr::core::recti(0, 0, size.Width, size.Height));
        FluxaraUI::transitionBackdrop(m_art[0], 77);
        return;
    }
    const auto title = [&c](const wchar_t* text)
    {
        auto* font = GUIEngine::getFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto sample = font->getDimension(L"M");
        font->setScale(28.0f * c.scale / std::max(1u, sample.Height));
        const auto destination = c.rect(88, 69, 190, 38);
        auto shadow = destination;
        shadow += irr::core::position2di(0, std::max(1, int(2 * c.scale)));
        font->draw(text, shadow, irr::video::SColor(128,5,13,46), true, true);
        font->draw(text, destination, irr::video::SColor(255,255,240,209),
                   true, true);
        font->setScale(saved);
    };
    GL32_draw2DRectangle(irr::video::SColor(255,12,31,76),c.rect(0,0,360,780));
    c.image(m_art[0],0,0,360,780,true,77);
    c.image(m_art[1],21,58,50,50); c.image(m_art[2],32,68,25,31);
    title(_C("fluxara", "CAMPAIGN").c_str());
    ListWidget* list = getWidget<ListWidget>("tracks");
    auto* box = list->getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>();
    const float scroll = box->getTouchScrollPosition() / c.scale;
    const irr::core::recti clip = c.rect(20,124,320,644);
    for (unsigned i=0;i<m_tracks.size();++i)
    {
        const float y = 136.0f + i * 276.0f - scroll;
        if (y > 768.0f || y + 236.0f < 124.0f)
            continue;
        Track* track = campaignTrack(m_tracks[i]);
        if (!m_cards[i])
            loadCardTexture(i);
        if (m_cards[i])
            c.roundedImage(m_cards[i],30,y,300,236,28,&clip);
        else
            GL32_draw2DRectangle(irr::video::SColor(255,28,55,105),
                c.rect(30,y,300,236), &clip);
        const bool installed = track != nullptr;
        const bool unlocked = isEventUnlocked(i);
        if (!installed)
        {
            // The dimmer follows the same rounded mask as the artwork; a
            // rectangular overlay previously produced sharp escaped corners.
            // Two 51% dimming layers combine to 76%, keeping artwork visible.
            c.roundedRectangle(irr::video::SColor(194,5,20,61),
                               30,y,300,236,28,&clip);
            float progress = -1.0f;
            if (m_download_request && m_downloading_track == m_tracks[i])
                progress = m_download_request->getProgress();
            // A circuit can be prepared ahead of its story unlock. The lock
            // controls race entry, never ownership of its data-only package.
            drawTrackDownloadControl(c, m_download_base, m_download_arrow,
                                     180, y + 84.224f, progress, clip);
        }
        c.image(m_art[3],45,y+180,270,40,false,255,&clip);
        const FluxaraSegment* segment = segmentFor(i);
        if (segment && !segment->title.empty())
            c.label(segment->title,48,y+12,264,22,13,&clip);
        c.label(StringUtils::utf8ToWide(m_titles[i]),58,y+190,
                unlocked?166:150,20,15,&clip);
        if (unlocked)
        {
            const PlayerProfile* player = PlayerManager::getCurrentPlayer();
            const unsigned cups = player ? player->getFluxaraCups(m_events[i].id) : 0;
            const core::stringw progress = _C("fluxara", "CUPS %d/3", cups);
            c.label(progress,226,y+190,76,20,13,&clip);
        }
        else
        {
            const core::stringw lock_text = _C("fluxara", "LOCK %d/%d",
                completedCount(), segment ? segment->unlock_completed : 0);
            c.label(lock_text,212,y+190,90,20,12,&clip);
        }
    }
    if (m_tracks.empty()) c.label(_C("fluxara", "No circuit available"),30,300,300,50,20);
}

void FluxaraCampaignScreen::onUpdate(float dt)
{
#ifdef IOS_FLUXARA_DRIFT
    // Opt-in hardware regression run, dormant in ordinary app launches.
    // Measure real wall-clock intervals: the game dt is capped and cannot
    // expose long frames. This never changes campaign progress or deletes maps.
    if (std::getenv("FLUXARA_VALIDATE_DOWNLOAD_UI"))
    {
        using Clock = std::chrono::steady_clock;
        static const auto began = Clock::now();
        static auto previous = began;
        static double next_report = 0.0;
        static int target = -1;
        static bool started = false, finished = false;
        static double scroll_start = -1.0;
        static std::vector<double> intervals;
        const auto now = Clock::now();
        const double elapsed = std::chrono::duration<double>(now - began).count();
        const double frame_ms = std::chrono::duration<double, std::milli>(now - previous).count();
        previous = now;
        auto* box = getWidget<ListWidget>("tracks")
            ->getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>();
        if (!started && elapsed > 3.0)
        {
            for (unsigned i = 10; i < m_tracks.size(); ++i)
                if (!campaignTrack(m_tracks[i]) &&
                    (target < 0 || m_download_sizes[i] > m_download_sizes[target]))
                    target = int(i);
            started = true;
            if (target >= 0)
            {
                box->getScrollBar()->setPos(target * box->getItemHeight());
                box->setTouchInertiaEnabled(true);
                Log::info("DownloadUI", "START index=%d locked=%d", target,
                          !isEventUnlocked(unsigned(target)));
                openTrack(unsigned(target));
            }
            else scroll_start = elapsed;
        }
        if (started && !finished && elapsed >= next_report)
        {
            next_report = elapsed + .5;
            Log::info("DownloadUI", "t=%.2f progress=%.4f active=%d installed=%d frame_ms=%.2f",
                elapsed, m_download_request ? m_download_request->getProgress() : -1.0f,
                bool(m_download_request), target >= 0 && campaignTrack(m_tracks[target]), frame_ms);
        }
        if (started && target >= 0 && !m_download_request && scroll_start < 0.0)
            scroll_start = elapsed;
        if (scroll_start >= 0.0 && !finished)
        {
            const double scroll_time = elapsed - scroll_start;
            // Traverse all cards in both directions with loaders visible.
            const double phase = std::fmod(scroll_time, 8.0) / 4.0;
            const double fraction = phase <= 1.0 ? phase : 2.0 - phase;
            box->getScrollBar()->setPos(int(box->getScrollBar()->getMax() * fraction));
            box->setTouchInertiaEnabled(true);
            if (scroll_time > 1.0) intervals.push_back(frame_ms);
            if (scroll_time >= 24.0)
            {
                std::sort(intervals.begin(), intervals.end());
                double sum = 0; for (double ms : intervals) sum += ms;
                Log::info("DownloadUI", "SCROLL frames=%u mean=%.2f p95=%.2f p99=%.2f max=%.2f",
                    unsigned(intervals.size()), sum / intervals.size(),
                    intervals[size_t(intervals.size() * .95)],
                    intervals[size_t(intervals.size() * .99)], intervals.back());
                fluxaraLogDeviceValidationMemory("download-ui-scroll", "");
                finished = true;
                box->getScrollBar()->setPos(10 * box->getItemHeight());
                box->setTouchInertiaEnabled(true);
            }
        }
    }
#endif
    // A ListBox selection is normally delivered through its GUI callback, but
    // iOS can coalesce that callback around a touch-pan transition.  Polling
    // the selected row gives a tap one deterministic route without treating a
    // story lock as a download lock.
    activateSelectedTrack();

    if (m_download_request && m_download_request->isDone())
    {
        const bool failed = m_download_request->hadDownloadError();
        m_download_request.reset();
        const std::string downloaded = m_downloading_track;
        m_downloading_track.clear();
        if (failed)
        {
            new MessageDialog(_("Unable to download this circuit. Please check your connection and try again."));
        }
        else
        {
            ExtractMobileAssets::reloadTracksAfterDownload();
            const bool installed = campaignTrack(downloaded) != nullptr;
            if (!installed)
                new MessageDialog(_("The circuit package could not be installed."));
        }
    }

    if (m_auto_start_delay >= 0.0f)
    {
        m_auto_start_delay -= dt;
        if (m_auto_start_delay <= 0.0f)
        {
            m_auto_start_delay = -1.0f;
            if (!m_tracks.empty() && isEventUnlocked(m_selected_track))
                openTrack(m_selected_track);
        }
    }
}

void FluxaraCampaignScreen::openTrack(unsigned selected)
{
    if (selected >= m_tracks.size()) return;
    Track* track = campaignTrack(m_tracks[selected]);
    if (!track)
    {
        startDownload(selected);
        return;
    }
    // The package may have been downloaded before the cup gate opens, but
    // campaign progression still controls entering the race itself.
    if (!isEventUnlocked(selected)) return;
    m_selected_track = selected;
    FluxaraRaceSetupScreen::getInstance()->setTrack(track,
        m_events[selected].mode, m_events[selected].id);
    FluxaraRaceSetupScreen::getInstance()->push();
}

void FluxaraCampaignScreen::startDownload(unsigned selected)
{
    if (selected >= m_tracks.size() || m_download_request ||
        m_download_urls[selected].empty())
    {
        return;
    }

    // Track packs are an explicitly requested part of the iPhone product.
    // Earlier Fluxara builds disabled every network request at startup, which
    // made HTTPRequest reject this queue before it could transfer any bytes.
    if (UserConfigParams::m_internet_status !=
        Online::RequestManager::IPERM_ALLOWED)
    {
        UserConfigParams::m_internet_status =
            Online::RequestManager::IPERM_ALLOWED;
        user_config->saveConfig();
    }
    // Permission is persisted, while the request worker only lives for the
    // current process.  A second launch must therefore start the worker too.
    if (!Online::RequestManager::isRunning())
        Online::RequestManager::get()->startNetworkThread();

    m_downloading_track = m_tracks[selected];
    m_download_request = std::make_shared<FluxaraTrackDownloadRequest>(
        m_tracks[selected], m_download_urls[selected], m_download_sizes[selected]);
    m_download_request->queue();
}

void FluxaraCampaignScreen::eventCallback(Widget* widget,
                                          const std::string& name,
                                          const int)
{
    if (name == "back")
    {
        // The campaign can be opened as a deep-linked top-level screen.
        // Resetting to Home prevents a one-page stack from terminating the
        // app while preserving the same destination for normal navigation.
        StateManager::get()->resetAndGoToScreen(
            FluxaraHomeScreen::getInstance());
        return;
    }

    if (m_tracks.empty())
        return;

    if (name == "tracks")
    {
        activateSelectedTrack();
        return;
    }
}

bool FluxaraCampaignScreen::onEscapePressed()
{
    return true;
}

void FluxaraCampaignScreen::showNextAfter(const std::string& track_ident)
{
    m_next_after = track_ident;
}

void FluxaraCampaignScreen::showNextAfterEvent(const std::string& event_id)
{
    m_next_after_event = event_id;
}

void FluxaraCampaignScreen::showEvent(const std::string& event_id)
{
    m_focus_event_id = event_id;
}

const FluxaraSegment* FluxaraCampaignScreen::segmentFor(unsigned selected) const
{
    if (selected >= m_events.size())
        return nullptr;
    for (const FluxaraSegment& segment : m_segments)
    {
        if (segment.id == m_events[selected].segment)
            return &segment;
    }
    return nullptr;
}

unsigned int FluxaraCampaignScreen::completedCount() const
{
    if (m_progress_cached)
        return m_completed_count;
    const PlayerProfile* player = PlayerManager::getCurrentPlayer();
    if (!player)
        return 0;
    std::vector<std::string> ids;
    ids.reserve(m_events.size());
    for (const FluxaraEvent& event : m_events)
        ids.push_back(event.id);
    return player->getFluxaraCompletedCount(ids);
}

bool FluxaraCampaignScreen::isEventUnlocked(unsigned selected) const
{
    if (selected >= m_events.size())
        return false;
    const FluxaraSegment* segment = segmentFor(selected);
    return !segment || completedCount() >= segment->unlock_completed;
}
