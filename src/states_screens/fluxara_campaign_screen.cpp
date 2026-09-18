// Fluxara Drift - iOS campaign circuit selection

#include "states_screens/fluxara_campaign_screen.hpp"

#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "graphics/stk_tex_manager.hpp"
#include "io/xml_node.hpp"
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
        "race/campaign-plate", "race/circuit-card", "race/summit-card", "home/icon-previous", "home/icon-next"};
    for (int i=0;i<8;++i) m_art[i]=FluxaraUI::texture(files[i]);
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
    updateTrackCard();
}

void FluxaraCampaignScreen::updateTrackCard()
{
    for (unsigned i=0;i<2;++i)
    {
        m_cards[i]=nullptr;
        m_card_names[i]="";
        Track* track = m_selected_track+i < m_tracks.size() ?
            track_manager->getTrack(m_tracks[m_selected_track+i]) : nullptr;
        getWidget<ButtonWidget>(i==0?"choose":"choose-second")->setActive(track!=nullptr);
        if (!track) continue;
        m_card_names[i]=track->getName();
        if (track->getIdent()=="fluxara-circuit") m_cards[i]=m_art[4];
        else if (track->getIdent()=="fluxara-summit-run") m_cards[i]=m_art[5];
        else m_cards[i]=STKTexManager::getInstance()->getTexture(
            track->getScreenshotFile(),"While loading Fluxara track card:",track->getFilename());
    }
    getWidget<ButtonWidget>("previous")->setActive(m_tracks.size()>2);
    getWidget<ButtonWidget>("next")->setActive(m_tracks.size()>2);
}

void FluxaraCampaignScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"back","choose","choose-second","previous","next"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<ButtonWidget>("back"),21,26,50,50);
    c.move(getWidget<ButtonWidget>("choose"),30,104,300,236);
    c.move(getWidget<ButtonWidget>("choose-second"),30,380,300,236);
    c.move(getWidget<ButtonWidget>("previous"),35,674,67,64);
    c.move(getWidget<ButtonWidget>("next"),258,674,67,64);
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
    for (int i=0;i<2;++i)
    {
        if (!m_cards[i]) continue;
        c.image(m_cards[i],30,104+i*276,300,236,true);
        c.image(m_art[3],45,284+i*276,270,40);
        c.label(m_card_names[i],58,294+i*276,244,20,16);
        if(m_selected_track+i<m_events.size())
            c.label(FluxaraModes::label(m_events[m_selected_track+i].mode),45,324+i*276,270,15,10);
    }
    if (m_tracks.empty()) c.label(L"No circuit available",30,300,300,50,20);
    if (m_tracks.size()>2)
    {
        c.image(m_art[6],45,680,47,51); c.image(m_art[7],268,680,47,51);
        const core::stringw page = core::stringw(m_selected_track+1)+L"–"+
            core::stringw(std::min(unsigned(m_tracks.size()),m_selected_track+2))+L" / "+
            core::stringw(unsigned(m_tracks.size()));
        c.label(page,105,691,150,30,18);
    }
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

    if (name == "previous")
    {
        m_selected_track = m_selected_track < 2 ?
            unsigned((m_tracks.size() - 1) / 2 * 2) : m_selected_track - 2;
        updateTrackCard();
        return;
    }
    if (name == "next")
    {
        m_selected_track = m_selected_track + 2 < m_tracks.size() ? m_selected_track+2 : 0;
        updateTrackCard();
        return;
    }
    if (name != "choose" && name != "choose-second")
        return;
    const unsigned selected = m_selected_track + (name=="choose-second"?1:0);
    if (selected>=m_tracks.size()) return;
    Track* track = track_manager->getTrack(m_tracks[selected]);
    if (!track)
        return;

    FluxaraRaceSetupScreen::getInstance()->setTrack(track,m_events[selected].mode);
    FluxaraRaceSetupScreen::getInstance()->push();
}

bool FluxaraCampaignScreen::onEscapePressed()
{
    return true;
}

void FluxaraCampaignScreen::showNextAfter(const std::string& track_ident)
{
    m_next_after = track_ident;
}
