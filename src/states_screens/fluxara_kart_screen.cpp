// Fluxara Drift - iOS kart selection

#include "states_screens/fluxara_kart_screen.hpp"

#include "config/player_manager.hpp"
#include "config/user_config.hpp"
#include "ge_render_info.hpp"
#include "graphics/2dutils.hpp"
#include "graphics/irr_driver.hpp"
#include "guiengine/engine.hpp"
#include "guiengine/scalable_font.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/icon_button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/model_view_widget.hpp"
#include "input/device_manager.hpp"
#include "input/input_manager.hpp"
#include "input/multitouch_device.hpp"
#include "io/file_manager.hpp"
#include "karts/abstract_characteristic.hpp"
#include "karts/kart_model.hpp"
#include "karts/kart_properties.hpp"
#include "karts/kart_properties_manager.hpp"
#include "race/race_manager.hpp"
#include "replay/replay_play.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_home_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "states_screens/fluxara_event.hpp"
#include "tracks/track.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

#include <cmath>
#include <algorithm>

using namespace GUIEngine;
using namespace irr;

FluxaraKartScreen::FluxaraKartScreen()
    : Screen("fluxara_kart.stkgui")
{
}

void FluxaraKartScreen::loadedFromFile()
{
}

void FluxaraKartScreen::setRace(Track* track, int laps, int karts,
                                const std::string& mode,
                                const std::string& event_id)
{
    m_track = track;
    m_laps = laps;
    m_num_karts = karts;
    m_mode = mode;
    m_event_id = event_id;
}

void FluxaraKartScreen::init()
{
    Screen::init();

    layoutControls();
    const char* garage_files[] = {"garage-nav", "garage-select", "back-surface",
                                 "icon-back", "icon-next", "icon-previous"};
    for (int i = 0; i < 6; ++i)
        m_garage_art[i] = FluxaraUI::texture(std::string("home/") + garage_files[i]);

    const auto texture = [](const std::string& name)
    {
        return irr_driver->getTexture(file_manager->getAsset(
            "gui/fluxara/stats/fluxara-" + name + ".png"));
    };
    m_stats_panel = texture("panel-transparent");
    m_stat_empty = texture("segment-empty");
    const char* icons[] = {"weight", "speed", "accel", "nitro"};
    const char* fills[] = {"segment-coral", "segment-cyan", "segment-purple", "segment-yellow"};
    for (int i = 0; i < 4; ++i)
    {
        m_stat_icons[i] = texture(icons[i]);
        m_stat_fills[i] = texture(fills[i]);
        m_stat_segments[i] = 0;
    }

    const std::vector<std::string> available_karts =
        kart_properties_manager->getAllAvailableKarts();
    m_karts.clear();
    for (const std::string& ident : available_karts)
    {
        const KartProperties* props = kart_properties_manager->getKart(ident);
        if (props && props->isInGroup("Fluxara"))
            m_karts.push_back(ident);
    }
    if (m_karts.empty())
    {
        m_kart_name = _C("fluxara", "No drive available");
        getWidget<ModelViewWidget>("kart-model")->clearModels();
        getWidget<ButtonWidget>("previous")->setActive(false);
        getWidget<ButtonWidget>("next")->setActive(false);
        getWidget<ButtonWidget>("start")->setActive(false);
        getWidget<ButtonWidget>("back")->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
        return;
    }
    getWidget<ButtonWidget>("previous")->setActive(true);
    getWidget<ButtonWidget>("next")->setActive(true);
    getWidget<ButtonWidget>("start")->setActive(true);

    m_selected_kart = 0;
    for (unsigned i = 0; i < m_karts.size(); ++i)
    {
        if (m_karts[i] == UserConfigParams::m_default_kart.c_str())
        {
            m_selected_kart = i;
            break;
        }
    }

    updateKartPreview();
    getWidget<ButtonWidget>("previous")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);

#if 0 // AUTOPLAY ACCEPTANCE — disabled for human play; retained for a future lab run.
    m_auto_start_delay = FluxaraModes::autoCampaignValidation() ? 0.1f : -1.0f;
#else
    m_auto_start_delay = -1.0f;
#endif
}

void FluxaraKartScreen::updateKartPreview()
{
    if (m_karts.empty())
        return;

    const KartProperties* props = kart_properties_manager->getKart(
        m_karts[m_selected_kart]);
    if (!props)
        return;

    ModelViewWidget* view = getWidget<ModelViewWidget>("kart-model");
    view->clearModels();

    const KartModel& model = props->getMasterKartModel();
    core::matrix4 model_location;
    float scale = model.getLength() > 1.45f ? 30.0f : 35.0f;
    model_location.setScale(core::vector3df(scale, scale, scale));
    // Kart meshes do not share a common local X origin.  Keep the preview
    // centred by its rendered body rather than by whichever mesh origin an
    // imported kart happened to use (most visibly Fluxara Ace).
    const float body_center_x = model.getModel()->getBoundingBox().getCenter().X;
    model_location.setTranslation(core::vector3df(-body_center_x * scale,
                                                   0.0f, 0.0f));
    view->addModel(model.getModel(), model_location, model.getBaseFrame(),
                   model.getBaseFrame());

    model_location.setScale(core::vector3df(1.0f, 1.0f, 1.0f));
    for (unsigned i = 0; i < 4; ++i)
    {
        model_location.setTranslation(
            model.getWheelGraphicsPosition(i).toIrrVector());
        view->addModel(model.getWheelModel(i), model_location);
    }

    for (unsigned i = 0; i < model.getSpeedWeightedObjectsCount(); ++i)
    {
        const SpeedWeightedObject& object = model.getSpeedWeightedObject(i);
        core::matrix4 location = object.m_location;
        if (!object.m_bone_name.empty())
        {
            core::matrix4 inverse = model.getInverseBoneMatrix(
                object.m_bone_name);
            location = inverse * object.m_location;
        }
        view->addModel(object.m_model, location, -1, -1, 0.0f,
                       object.m_bone_name);
    }

    view->setRotateContinuously(30.0f);
    view->update(0);

    m_kart_name = props->getName();
    // Same normalization as the original KartStatsWidget; nitro is efficiency.
    const RaceManager::Difficulty difficulty = RaceManager::get()->getDifficulty();
    RaceManager::get()->setDifficulty(RaceManager::DIFFICULTY_BEST);
    KartProperties computed;
    computed.copyForPlayer(props, HANDICAP_NONE);
    const auto* characteristics = computed.getCombinedCharacteristic();
    const float consumption = characteristics->getNitroConsumption();
    const float values[] = {
        characteristics->getMass() / 3.89f,
        (characteristics->getEngineMaxSpeed() - 20.0f) * 15.0f,
        computed.getAccelerationEfficiency() * 10.0f,
        consumption > 0.0f ? 90.0f / consumption : 0.0f
    };
    RaceManager::get()->setDifficulty(difficulty);
    for (int i = 0; i < 4; ++i)
        m_stat_segments[i] = std::isfinite(values[i]) ?
            int(std::lround(std::max(0.0f, std::min(100.0f, values[i])) * 13.0f / 100.0f)) : 0;
}

// -----------------------------------------------------------------------------
void FluxaraKartScreen::updateKartRotation()
{
    constexpr float idle_rotation_speed = 30.0f;
    ModelViewWidget* view = getWidget<ModelViewWidget>("kart-model");
    MultitouchDevice* touch = input_manager->getDeviceManager()
        ->getMultitouchDevice();
    if (!view || !touch)
    {
        if (view) view->setRotateContinuously(idle_rotation_speed);
        return;
    }

    if (m_kart_dragging)
    {
        const MultitouchEvent& event = touch->m_events[m_kart_drag_touch];
        if (!event.touched)
        {
            m_kart_dragging = false;
            m_kart_drag_touch = -1;
            view->setRotateContinuously(idle_rotation_speed);
            return;
        }

        const int delta_x = event.x - m_kart_drag_x;
        if (delta_x != 0)
        {
            // The preview follows a horizontal finger drag without inertia;
            // automatic rotation resumes only after the touch is released.
            view->rotateBy(float(delta_x) * 0.5f);
            m_kart_drag_x = event.x;
        }
        return;
    }

    for (unsigned int i = 0; i < touch->m_events.size(); ++i)
    {
        const MultitouchEvent& event = touch->m_events[i];
        if (!event.touched || event.x < view->m_x ||
            event.x >= view->m_x + view->m_w || event.y < view->m_y ||
            event.y >= view->m_y + view->m_h)
            continue;

        m_kart_dragging = true;
        m_kart_drag_touch = int(i);
        m_kart_drag_x = event.x;
        view->setRotateOff();
        return;
    }

    view->setRotateContinuously(idle_rotation_speed);
}

// -----------------------------------------------------------------------------
void FluxaraKartScreen::onUpdate(float dt)
{
    if (m_auto_start_delay >= 0.0f)
    {
        m_auto_start_delay -= dt;
        if (m_auto_start_delay <= 0.0f)
        {
            m_auto_start_delay = -1.0f;
            startRace();
            return;
        }
    }
    updateKartRotation();
}

void FluxaraKartScreen::layoutControls()
{
    for (const char* id : {"back", "previous", "next", "start"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));

    // This screen is a 360x780 full-bleed Figma composition. Unlike menus,
    // the garage scenery and podium must not be moved by the iPhone safe
    // area: that breaks the intended alignment between the 3D preview and
    // the painted turntable.
    const auto screen = irr_driver->getActualScreenSize();
    const float scale = std::min(float(screen.Width) / 360.0f,
                                 float(screen.Height) / 780.0f);
    const auto coordinate = [scale](float value)
    {
        return int(std::lround(value * scale));
    };
    const auto move = [&coordinate](Widget* widget, float x, float y,
                                    float width, float height)
    {
        widget->move(coordinate(x), coordinate(y), coordinate(width),
                     coordinate(height));
    };

    // Figma node 54:3 was exported at 3x with its own blur and alpha fade.
    // The outpainted asset already matches the full 360x780 canvas. Draw it
    // at its native logical frame: shifting or stretching it changes the
    // approved perspective of the garage and podium.
    getWidget<IconButtonWidget>("garage-background")->move(
        0, 0, screen.Width, screen.Height);
    // Shift the rendered kart 20 pt right and 20 pt up with its turntable.
    // Keep its size and the stats panel untouched.
    move(getWidget<ModelViewWidget>("kart-model"), 52, 202, 296, 260);
    move(getWidget<Widget>("stats-panel"), 53, 418, 254, 254);
    // The scenery stays full-bleed; only the interactive header is lowered
    // clear of the Dynamic Island on the actual portrait device.
    move(getWidget<ButtonWidget>("back"), 21, 58, 50, 50);
    move(getWidget<ButtonWidget>("previous"), 35, 684, 67, 64);
    move(getWidget<ButtonWidget>("next"), 258, 684, 67, 64);
    move(getWidget<ButtonWidget>("start"), 117, 695, 126, 47);
}

void FluxaraKartScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraKartScreen::onDraw(float)
{
    // Garage is the one portrait screen whose 3D model is aligned to painted
    // scenery, so draw its Figma layers in the physical full-bleed canvas.
    const FluxaraUI::Canvas c;
    c.image(m_garage_art[0], 22, 684, 316, 64);
    c.image(m_garage_art[1], 117, 695, 126, 47);
    c.image(m_garage_art[2], 21, 58, 50, 50);
    c.image(m_garage_art[3], 32, 68, 25, 31);
    c.image(m_garage_art[4], 268, 690, 47, 51);
    c.image(m_garage_art[5], 45, 690, 47, 51);
    // Keep the header clear of the portrait sensor housing without moving
    // the 3D kart/podium composition below it.
    c.label(_C("fluxara", "GARAGE"), 88, 69, 190, 38, 31);
    c.label(_C("fluxara", "SELECT"), 125, 703, 110, 28, 18);
    Widget* slot = getWidget<Widget>("stats-panel");
    if (!slot || !m_stats_panel || slot->m_w <= 0 || slot->m_h <= 0) return;
    // Reference coordinates: a single scale preserves every raster's shape.
    const float scale = std::min(slot->m_w, slot->m_h) / 1254.0f;
    const float x = slot->m_x + (slot->m_w - 1254.0f * scale) * 0.5f;
    const float y = slot->m_y + (slot->m_h - 1254.0f * scale) * 0.5f;
    const auto rect = [&](float left, float top, float width, float height)
    {
        return core::recti(int(std::lround(x + left * scale)),
                           int(std::lround(y + top * scale)),
                           int(std::lround(x + (left + width) * scale)),
                           int(std::lround(y + (top + height) * scale)));
    };
    const auto draw = [&](video::ITexture* texture, float left, float top,
                          float width, float height)
    {
        if (!texture) return;
        const auto size = texture->getSize();
        draw2DImage(texture, rect(left, top, width, height),
                    core::recti(0, 0, size.Width, size.Height), nullptr,
                    video::SColor(255, 255, 255, 255), true);
    };
    const auto label = [&](const core::stringw& text, float left, float top,
                           float width, float height)
    {
        gui::ScalableFont* font = GUIEngine::getFont();
        const float saved_scale = font->getScale();
        font->setScale(1.0f);
        const auto size = font->getDimension(text.c_str());
        font->setScale(std::min(width * scale / std::max(1u, size.Width),
                                height * scale / std::max(1u, size.Height)));
        const core::recti area = rect(left, top, width, height);
        font->draw(text, area, video::SColor(255, 255, 255, 255), true, true, &area);
        font->setScale(saved_scale);
    };
    draw(m_stats_panel, 0, 0, 1254, 1254);
    label(m_kart_name, 165, 158, 920, 116);
    label(_C("fluxara", "STATS"), 80, 352, 168, 58);
    const core::stringw labels[] = {_C("fluxara", "WEIGHT"), _C("fluxara", "SPEED"), _C("fluxara", "ACCEL"), _C("fluxara", "NITRO")};
    for (int row = 0; row < 4; ++row)
    {
        const float top = 444.0f + row * 175.0f;
        draw(m_stat_icons[row], 88, top, 140, 140);
        label(labels[row], 234, top + 36, 196, 61);
        for (int segment = 0; segment < 13; ++segment)
            draw(segment < m_stat_segments[row] ? m_stat_fills[row] : m_stat_empty,
                 469.0f + segment * 51.0f, top + 28, 54, 90);
    }
}

void FluxaraKartScreen::startRace()
{
    if (m_karts.empty())
        return;

    const std::string& kart = m_karts[m_selected_kart];
    UserConfigParams::m_default_kart = kart;
    if (!m_track)
    {
        StateManager::get()->escapePressed();
        return;
    }
    if(!FluxaraModes::supportedOffline(m_mode)) return;

    if (StateManager::get()->activePlayerCount() == 0)
    {
        InputDevice* device = input_manager->getDeviceManager()
            ->getLatestUsedDevice();
        StateManager::get()->createActivePlayer(PlayerManager::getCurrentPlayer(),
                                                device);
    }

    RaceManager::get()->setNumPlayers(1);
    RaceManager::get()->setMajorMode(RaceManager::MAJOR_MODE_SINGLE);
    RaceManager::get()->setMinorMode(FluxaraModes::nativeMode(m_mode));
    RaceManager::get()->setWatchingReplay(false);
    RaceManager::get()->setRaceGhostKarts(false);
    RaceManager::get()->setRecordRace(false);
    if (m_mode == "ghost_geometry")
    {
        // Prefer a replay of this exact circuit.  A first visit remains
        // playable: it records a seed run instead of substituting a replay
        // from another map, then the next visit races against that ghost.
        ReplayPlay* replay = ReplayPlay::get();
        replay->loadAllReplayFile();
        bool found_matching_ghost = false;
        for (unsigned int i = 0; i < replay->getNumReplayFile(); ++i)
        {
            const ReplayPlay::ReplayData& candidate = replay->getReplayData(i);
            if (candidate.m_track_name == m_track->getIdent() &&
                candidate.m_minor_mode == "time-trial" &&
                !candidate.m_kart_list.empty())
            {
                replay->setReplayFile(i);
                replay->setSecondReplayFile(0, false);
                RaceManager::get()->setRaceGhostKarts(true);
                found_matching_ghost = true;
                break;
            }
        }
        if (!found_matching_ghost)
            RaceManager::get()->setRecordRace(true);
    }
    // Clear targets left by a previously played mode before applying this
    // event's native target semantics. Arena/timed events never become races.
    RaceManager::get()->setHitCaptureTime(0,0.0f);
    RaceManager::get()->setTimeTarget(0.0f);
    if(FluxaraModes::timed(m_mode))
        RaceManager::get()->setTimeTarget(float(m_laps*60));
    if(m_mode=="free_for_all")
        RaceManager::get()->setHitCaptureTime(0,float(m_laps*60));
    if(m_mode=="soccer")
    {
        // SoccerWorld regards a zero goal target as a completed 0:0 match.
        // Keep the Garage launch equivalent to the direct campaign route:
        // a playable first-to-three local game.
        RaceManager::get()->setMaxGoal(3);
    }
    if(m_mode=="capture_the_flag")
    {
        // CTF treats a zero capture limit with no timer as an already-over
        // match.  A local event is a three-capture practice with a bounded
        // time limit, so it enters actual gameplay instead of jumping straight
        // to the result screen. The automatic campaign pass is the only
        // consumer that may shorten this real CTF round for coverage. A
        // score-validation launch still uses the normal match duration.
        RaceManager::get()->setHitCaptureTime(
            3, (FluxaraModes::autoCampaignValidation() &&
                FluxaraModes::forceValidationWins()) ? 5.0f : 180.0f);
    }
    const bool has_opponents = FluxaraModes::hasOfflineOpponents(m_mode);
    int wanted_opponents = has_opponents
        ? FluxaraModes::opponentsPerRace : 0;
    int maximum_opponents = std::max(0, int(m_karts.size()) - 1);
    if (FluxaraModes::arena(m_mode) || m_mode == "soccer")
        maximum_opponents = std::min(maximum_opponents,
            std::max(0, int(m_track->getMaxArenaPlayers()) - 1));
    wanted_opponents = std::min(wanted_opponents, maximum_opponents);

    std::vector<std::string> ai_karts;
    for (unsigned int offset = 1; offset < m_karts.size() &&
                                  int(ai_karts.size()) < wanted_opponents;
         ++offset)
    {
        const std::string& candidate =
            m_karts[(m_selected_kart + offset) % m_karts.size()];
        if (candidate != kart && std::find(ai_karts.begin(), ai_karts.end(),
                                            candidate) == ai_karts.end())
            ai_karts.push_back(candidate);
    }

    // Set the total from the actual unique roster, so the engine never fills
    // a missing slot with an arbitrary duplicate kart.
    const int total_karts = int(ai_karts.size()) + 1;
    RaceManager::get()->setNumKarts(total_karts);
    RaceManager::get()->setPlayerKart(0, kart);
    RaceManager::get()->setDefaultAIKartList(ai_karts);
    if(m_mode=="soccer")
    {
        RaceManager::get()->setKartTeam(0,KART_TEAM_RED);
        const int ai=total_karts-1;
        RaceManager::get()->setNumRedAI(ai/2);
        RaceManager::get()->setNumBlueAI(ai-ai/2);
    }
    else if(m_mode=="capture_the_flag")
    {
        RaceManager::get()->setKartTeam(0,KART_TEAM_RED);
        const int ai = total_karts - 1;
        // Six opponents form 4-vs-3 teams including the player. This keeps
        // the automatic player on a real team without turning CTF into the
        // old one-kart practice route.
        RaceManager::get()->setNumRedAI(ai / 2);
        RaceManager::get()->setNumBlueAI(ai - ai / 2);
    }
    RaceManager::get()->setReverseTrack(false);

    if (!m_event_id.empty() && PlayerManager::getCurrentPlayer())
        PlayerManager::getCurrentPlayer()->beginFluxaraEvent(
            m_event_id, m_track->getIdent());

    input_manager->getDeviceManager()->setAssignMode(ASSIGN);
    input_manager->getDeviceManager()->setSinglePlayer(
        StateManager::get()->getActivePlayer(0));
    RaceManager::get()->startSingleRace(m_track->getIdent(),
        FluxaraModes::laps(m_mode)?m_laps:-1, false);
}

void FluxaraKartScreen::eventCallback(Widget*, const std::string& name,
                                      const int)
{
    if (name == "back")
    {
        // A Garage deep launch has no Home page beneath it.  Popping that
        // one-item menu stack quits the app, while the same visual action
        // must return to the Fluxara home screen.  Kart choice for a campaign
        // event does have a setup page underneath and keeps ordinary Back.
        if (m_track == nullptr)
            StateManager::get()->resetAndGoToScreen(
                FluxaraHomeScreen::getInstance());
        else
            StateManager::get()->escapePressed();
        return;
    }

    if (name == "previous" && !m_karts.empty())
    {
        m_selected_kart = m_selected_kart == 0 ?
            unsigned(m_karts.size() - 1) : m_selected_kart - 1;
        updateKartPreview();
    }
    else if (name == "next" && !m_karts.empty())
    {
        m_selected_kart = (m_selected_kart + 1) % unsigned(m_karts.size());
        updateKartPreview();
    }
    else if (name == "start")
    {
        startRace();
    }
}

bool FluxaraKartScreen::onEscapePressed()
{
    return true;
}
