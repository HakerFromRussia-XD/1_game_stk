// Fluxara Drift - iOS race settings

#include "states_screens/fluxara_race_setup_screen.hpp"

#include "config/player_manager.hpp"
#include "config/user_config.hpp"
#include "graphics/stk_tex_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "race/race_manager.hpp"
#include "states_screens/fluxara_kart_screen.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "states_screens/fluxara_event.hpp"
#include "tracks/track.hpp"

#include <algorithm>
#include <sstream>

using namespace GUIEngine;

FluxaraRaceSetupScreen::FluxaraRaceSetupScreen()
    : Screen("fluxara_race_setup.stkgui")
{
}

void FluxaraRaceSetupScreen::loadedFromFile()
{
}

void FluxaraRaceSetupScreen::setTrack(Track* track, const std::string& mode)
{
    m_track = track;
    m_mode = mode;
}

void FluxaraRaceSetupScreen::init()
{
    Screen::init();

    if (!m_track)
    {
        StateManager::get()->escapePressed();
        return;
    }

    m_preview = STKTexManager::getInstance()->getTexture(
        m_track->getScreenshotFile(), "While loading Fluxara track preview:",
        m_track->getFilename());
    const char* files[] = {"race/background", "race/laps-panel", "race/laps-surface",
        "race/icon-plus", "race/icon-minus", "race/track-plate", "home/back-surface",
        "home/icon-back", "home/button-play", "race/circuit-card"};
    for (int i = 0; i < 10; ++i) m_art[i] = FluxaraUI::texture(files[i]);
    layoutControls();

    RaceManager::get()->setMajorMode(RaceManager::MAJOR_MODE_SINGLE);
    const auto native_mode=FluxaraModes::nativeMode(m_mode);
    if(native_mode!=RaceManager::MINOR_MODE_NONE) RaceManager::get()->setMinorMode(native_mode);
    m_unavailable_reason="";
    if(m_mode=="ghost_geometry") m_unavailable_reason=L"Ghost needs a saved replay";
    else if(m_mode=="capture_the_flag") m_unavailable_reason=L"CTF has no offline AI";
    else if(native_mode==RaceManager::MINOR_MODE_NONE) m_unavailable_reason=L"Unsupported event mode";
    else if(m_mode=="egg_hunt" && !m_track->hasEasterEggs()) m_unavailable_reason=L"This map has no egg hunt placements";
    else if(m_mode=="soccer" && !m_track->isSoccer()) m_unavailable_reason=L"This event needs a soccer arena";
    else if(FluxaraModes::arena(m_mode) && !m_track->isArena()) m_unavailable_reason=L"This event needs a battle arena";
    else if((FluxaraModes::arena(m_mode)||m_mode=="soccer") && !m_track->hasNavMesh())
        m_unavailable_reason=L"This arena has no offline AI navigation";

    m_laps = FluxaraModes::timed(m_mode) ? 3 : std::max(1, std::min(9, m_track->getActualNumberOfLap()));
    const int saved_ai = int(UserConfigParams::m_num_karts_per_gamemode[
        native_mode==RaceManager::MINOR_MODE_NONE?RaceManager::MINOR_MODE_NORMAL_RACE:native_mode]) - 1;
    m_ai_karts = std::max(1, std::min(7, saved_ai));
    if(m_mode=="follow_leader") m_ai_karts=std::max(2,m_ai_karts);
    if(FluxaraModes::arena(m_mode)||m_mode=="soccer")
        m_ai_karts=std::min(m_ai_karts,std::max(0,int(m_track->getMaxArenaPlayers())-1));
    if(m_mode=="egg_hunt") m_ai_karts=0;
    if((FluxaraModes::arena(m_mode)||m_mode=="soccer") && m_ai_karts==0 && m_unavailable_reason.empty())
        m_unavailable_reason=L"This arena has no room for opponents";
    m_difficulty = std::max(0, std::min(2, int(UserConfigParams::m_difficulty)));
    updateRaceDetails();

    getWidget<ButtonWidget>(m_unavailable_reason.empty() ? "start" : "back")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void FluxaraRaceSetupScreen::updateRaceDetails()
{
    const bool target=FluxaraModes::laps(m_mode)||FluxaraModes::timed(m_mode);
    getWidget<ButtonWidget>("laps-minus")->setActive(target && m_laps > 1);
    getWidget<ButtonWidget>("laps-plus")->setActive(target && m_laps < 9);
    getWidget<ButtonWidget>("opponents")->setActive(m_mode!="egg_hunt");
    getWidget<ButtonWidget>("start")->setActive(m_unavailable_reason.empty());
}

void FluxaraRaceSetupScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"back", "laps-minus", "laps-plus", "opponents", "novice", "standard", "expert", "start"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<ButtonWidget>("back"), 21,26,50,50);
    c.move(getWidget<ButtonWidget>("laps-minus"), 180,414,46,46);
    c.move(getWidget<ButtonWidget>("laps-plus"), 280,414,46,46);
    c.move(getWidget<ButtonWidget>("opponents"), 24,484,312,50);
    c.move(getWidget<ButtonWidget>("novice"), 24,558,100,58);
    c.move(getWidget<ButtonWidget>("standard"), 130,558,100,58);
    c.move(getWidget<ButtonWidget>("expert"), 236,558,100,58);
    c.move(getWidget<ButtonWidget>("start"), 28,646,304,109);
}

void FluxaraRaceSetupScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraRaceSetupScreen::onDraw(float)
{
    if (!m_track) return;
    const FluxaraUI::Canvas c;
    GL32_draw2DRectangle(irr::video::SColor(255,16,47,122),c.rect(0,0,360,780));
    c.image(m_art[0],0,0,360,780,true,77);
    c.image(m_art[6],21,26,50,50); c.image(m_art[7],32,36,25,31);
    c.label(L"RACE SETUP",84,33,210,38,30);
    c.label(FluxaraModes::label(m_mode),24,83,312,24,15);
    // The approved Circuit illustration is retained for its matching track;
    // all other tracks use their own real preview, never another track's art.
    c.image(m_track->getIdent() == "fluxara-circuit" ? m_art[9] : m_preview,24,126,312,245,true);
    c.image(m_art[5],54,307,252,42);
    c.label(m_track->getName(),68,315,224,24,18);
    c.image(m_art[1],24,401,312,71);
    c.label(FluxaraModes::timed(m_mode)?L"MINUTES":FluxaraModes::laps(m_mode)?L"LAPS":L"RULES",36,424,120,26,16);
    c.image(m_art[2],182,416,42,42); c.image(m_art[2],282,416,42,42);
    c.image(m_art[4],190,422,26,26); c.image(m_art[3],290,423,26,26);
    c.label(FluxaraModes::laps(m_mode)||FluxaraModes::timed(m_mode)?core::stringw(m_laps):core::stringw(L"—"),227,412,52,42,33);
    c.image(m_art[1],24,484,312,50);
    c.label(core::stringw(L"OPPONENTS: ") + core::stringw(m_ai_karts),36,492,288,32,18);
    c.label(L"DIFFICULTY",24,536,312,20,14);
    const wchar_t* names[] = {L"NOVICE", L"STANDARD", L"EXPERT"};
    for (int i=0;i<3;++i)
    {
        c.image(m_art[8],24+i*106,558,100,58,false,i==m_difficulty?255:140);
        c.label(names[i],27+i*106,574,94,24,13);
    }
    if(!m_unavailable_reason.empty()) c.label(m_unavailable_reason,20,617,320,24,14);
    c.image(m_art[8],28,646,304,109,false,m_unavailable_reason.empty()?255:110);
    c.label(L"START RACE",104,676,152,30,23);
}

void FluxaraRaceSetupScreen::eventCallback(Widget*, const std::string& name,
                                           const int)
{
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }

    if (name == "laps-minus" || name == "laps-plus")
    {
        m_laps = std::max(1,std::min(9,m_laps + (name == "laps-plus" ? 1 : -1)));
        updateRaceDetails();
        return;
    }

    if (name == "opponents")
    {
        if(m_mode=="egg_hunt") return;
        const int minimum=m_mode=="follow_leader"?2:1;
        const int maximum=FluxaraModes::arena(m_mode)||m_mode=="soccer" ?
            std::min(7,std::max(0,int(m_track->getMaxArenaPlayers())-1)):7;
        m_ai_karts=maximum<minimum?0:m_ai_karts>=maximum?minimum:m_ai_karts+1;
        updateRaceDetails();
        return;
    }

    if (name == "novice" || name == "standard" || name == "expert")
    {
        m_difficulty = name == "novice" ? 0 : name == "standard" ? 1 : 2;
        return;
    }
    if (name != "start" || !m_unavailable_reason.empty()) return;
    const auto difficulty = static_cast<RaceManager::Difficulty>(m_difficulty);

    RaceManager::get()->setMajorMode(RaceManager::MAJOR_MODE_SINGLE);
    RaceManager::get()->setMinorMode(FluxaraModes::nativeMode(m_mode));
    RaceManager::get()->setDifficulty(difficulty);
    UserConfigParams::m_difficulty = difficulty;
    RaceManager::get()->setNumLaps(m_laps);
    RaceManager::get()->setNumKarts(m_ai_karts + 1);
    if (FluxaraModes::laps(m_mode))
        UserConfigParams::m_num_laps = m_laps;
    UserConfigParams::m_num_karts_per_gamemode[
        FluxaraModes::nativeMode(m_mode)] = m_ai_karts + 1;

    FluxaraKartScreen::getInstance()->setRace(m_track, m_laps,
                                               m_ai_karts + 1,m_mode);
    FluxaraKartScreen::getInstance()->push();
}

bool FluxaraRaceSetupScreen::onEscapePressed()
{
    return true;
}
