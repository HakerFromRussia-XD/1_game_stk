// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/list_widget.hpp"
#include "io/xml_node.hpp"
#include <IGUIScrollBar.h>
#include <memory>
#include "states_screens/fluxara_race_setup_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "tracks/track.hpp"
#include "tracks/track_manager.hpp"

#include <sstream>
#include <algorithm>

using namespace GUIEngine;

FluxaraCampaignScreen::FluxaraCampaignScreen()
    : Screen("fluxara_campaign.stkgui")
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
    const std::string manifest = file_manager->getAsset("fluxara-campaign.xml");
    std::unique_ptr<XMLNode> campaign(manifest.empty() ? nullptr : file_manager->createXMLTree(manifest));
    if (campaign)
    {
        for (unsigned i=0;i<campaign->getNumNodes();++i)
        {
            const XMLNode* node=campaign->getNode(i);
            if (node->getName()!="event") continue;
            FluxaraEvent event;
            node->get("id",&event.id); node->get("mode",&event.mode); node->get("track",&event.track);
            if(event.id.empty() || event.track.empty()) continue;
            m_events.push_back(event);
            m_tracks.push_back(event.track);
        }
    }

    if (!m_next_after.empty())
    {
        const std::vector<std::string>::iterator current = std::find(
            m_tracks.begin(), m_tracks.end(), m_next_after);
        if (current != m_tracks.end())
            m_selected_track = unsigned((current - m_tracks.begin() + 1) %
                m_tracks.size());
        m_next_after.clear();
    }
    else if (m_selected_track >= m_tracks.size())
        m_selected_track = 0;
    populateTrackList();
}

void FluxaraCampaignScreen::populateTrackList()
{
    ListWidget* list = getWidget<ListWidget>("tracks");
    list->clear();
    for (unsigned i = 0; i < m_tracks.size(); ++i)
        list->addItem(m_events[i].id, L"");

    auto* box = list->getIrrlichtElement<irr::gui::CGUISTKListBox>();
    box->setDrawBackground(false);
    box->setItemHeight(std::max(1, int(std::lround(256.0f * FluxaraUI::Canvas().scale))));
    m_cards.assign(m_tracks.size(), nullptr);

    if (!m_tracks.empty())
    {
        const unsigned target = std::min(m_selected_track,
                                         unsigned(m_tracks.size() - 1));
        box->getScrollBar()->setPos(target * box->getItemHeight());
    }
    m_last_scroll_pos = box->getScrollBar()->getPos();
    m_scroll_idle_time = 1.0f;
}

void FluxaraCampaignScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>("back"));
    c.move(getWidget<ButtonWidget>("back"),21,26,50,50);
    ListWidget* list = getWidget<ListWidget>("tracks");
    c.move(list,20,92,320,676);
    if (auto* box = list->getIrrlichtElement<irr::gui::CGUISTKListBox>())
        box->setItemHeight(std::max(1, int(std::lround(256.0f * c.scale))));
}

void FluxaraCampaignScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraCampaignScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    GL32_draw2DRectangle(irr::video::SColor(255,12,31,76),c.rect(0,0,360,780));
    c.image(m_art[0],0,0,360,780,true,77);
    c.image(m_art[1],21,26,50,50); c.image(m_art[2],32,36,25,31);
    c.label(L"CAMPAIGN",96,37,220,32,28);
    ListWidget* list = getWidget<ListWidget>("tracks");
    auto* box = list->getIrrlichtElement<irr::gui::CGUISTKListBox>();
    const float scroll = box->getScrollBar()->getPos() / c.scale;
    const irr::core::recti clip = c.rect(20,92,320,676);
    for (unsigned i=0;i<m_tracks.size();++i)
    {
        const float y = 104.0f + i * 256.0f - scroll;
        if (y > 768.0f || y + 236.0f < 92.0f) continue;
        Track* track = track_manager->getTrack(m_tracks[i]);
        if (!track) continue;
        if (!m_cards[i])
        {
            if (track->getIdent()=="fluxara-circuit") m_cards[i]=m_art[4];
            else if (track->getIdent()=="fluxara-summit-run") m_cards[i]=m_art[5];
            else m_cards[i]=FluxaraUI::nativeTexture(track->getScreenshotFile());
        }
        c.roundedImage(m_cards[i],30,y,300,236,18,&clip);
        c.image(m_art[3],45,y+180,270,40,false,255,&clip);
        c.label(track->getName(),58,y+190,244,20,16,&clip);
    }
    if (m_tracks.empty()) c.label(L"No circuit available",30,300,300,50,20);
}

void FluxaraCampaignScreen::onUpdate(float dt)
{
    auto* box = getWidget<ListWidget>("tracks")->
        getIrrlichtElement<irr::gui::CGUISTKListBox>();
    const int scroll_pos = box->getScrollBar()->getPos();
    if (scroll_pos != m_last_scroll_pos)
    {
        m_last_scroll_pos = scroll_pos;
        m_scroll_idle_time = 0.0f;
    }
    else
        m_scroll_idle_time += dt;
}

void FluxaraCampaignScreen::openTrack(unsigned selected)
{
    if (selected>=m_tracks.size()) return;
    Track* track = track_manager->getTrack(m_tracks[selected]);
    if (!track) return;
    m_selected_track = selected;
    FluxaraRaceSetupScreen::getInstance()->setTrack(track,m_events[selected].mode);
    FluxaraRaceSetupScreen::getInstance()->push();
}

void FluxaraCampaignScreen::eventCallback(Widget* widget,
                                          const std::string& name,
                                          const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }

    if (m_tracks.empty())
        return;

    if (name == "tracks")
    {
        ListWidget* list = getWidget<ListWidget>("tracks");
        auto* box = list->getIrrlichtElement<irr::gui::CGUISTKListBox>();
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
