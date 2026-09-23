// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "config/player_manager.hpp"
#include "config/player_profile.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/list_widget.hpp"
#include "io/xml_node.hpp"
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
#include "utils/translation.hpp"

#include <sstream>
#include <algorithm>

using namespace GUIEngine;

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
    layoutControls();

    m_tracks.clear();
    m_events.clear();
    m_segments.clear();
    m_progress_cached = false;
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
    m_cards.assign(m_tracks.size(), nullptr);

    if (!m_tracks.empty())
    {
        const unsigned target = std::min(m_selected_track,
                                         unsigned(m_tracks.size() - 1));
        box->getScrollBar()->setPos(target * box->getItemHeight());
    }
    box->setTouchInertiaEnabled(true);
    m_last_scroll_pos = box->getScrollBar()->getPos();
    m_scroll_idle_time = 1.0f;
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
        if (y > 768.0f || y + 236.0f < 124.0f) continue;
        Track* track = track_manager->getTrack(m_tracks[i]);
        if (!track) continue;
        if (!m_cards[i])
        {
            if (track->getIdent()=="fluxara-circuit") m_cards[i]=m_art[4];
            else if (track->getIdent()=="fluxara-summit-run") m_cards[i]=m_art[5];
            else m_cards[i]=FluxaraUI::nativeTexture(track->getScreenshotFile());
        }
        c.roundedImage(m_cards[i],30,y,300,236,28,&clip);
        c.image(m_art[3],45,y+180,270,40,false,255,&clip);
        const FluxaraSegment* segment = segmentFor(i);
        if (segment && !segment->title.empty())
            c.label(segment->title,48,y+12,264,22,13,&clip);
        const bool unlocked = isEventUnlocked(i);
        c.label(track->getName(),58,y+190,unlocked?166:150,20,15,&clip);
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
    auto* box = getWidget<ListWidget>("tracks")->
        getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>();
    const int scroll_pos = box->getScrollBar()->getPos();
    if (scroll_pos != m_last_scroll_pos)
    {
        m_last_scroll_pos = scroll_pos;
        m_scroll_idle_time = 0.0f;
    }
    else
        m_scroll_idle_time += dt;

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
    if (selected>=m_tracks.size() || !isEventUnlocked(selected)) return;
    Track* track = track_manager->getTrack(m_tracks[selected]);
    if (!track) return;
    m_selected_track = selected;
    FluxaraRaceSetupScreen::getInstance()->setTrack(track,
        m_events[selected].mode, m_events[selected].id);
    FluxaraRaceSetupScreen::getInstance()->push();
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
        ListWidget* list = getWidget<ListWidget>("tracks");
        auto* box = list->getIrrlichtElement<irr::gui::CGUIFLUXARA_DRIFTListBox>();
        const int selected = list->getSelectionID();
        list->setSelectionID(-1);
        const int scroll_pos = box->getScrollBar()->getPos();
        const bool was_scrolling = scroll_pos != m_last_scroll_pos ||
                                   m_scroll_idle_time < 0.18f;
        m_last_scroll_pos = scroll_pos;
        if (selected >= 0 && !was_scrolling) openTrack(unsigned(selected));
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
