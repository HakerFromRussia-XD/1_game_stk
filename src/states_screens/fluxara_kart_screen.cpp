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
#include "io/file_manager.hpp"
#include "karts/abstract_characteristic.hpp"
#include "karts/kart_model.hpp"
#include "karts/kart_properties.hpp"
#include "karts/kart_properties_manager.hpp"
#include "race/race_manager.hpp"
#include "states_screens/state_manager.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "states_screens/fluxara_event.hpp"
#include "tracks/track.hpp"

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

void FluxaraKartScreen::setRace(Track* track, int laps, int karts, const std::string& mode)
{
    m_track = track;
    m_laps = laps;
    m_num_karts = karts;
    m_mode = mode;
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
        m_kart_name = "No drive available";
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

void FluxaraKartScreen::layoutControls()
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"back", "previous", "next", "start"})
        FluxaraUI::rasterHitTarget(getWidget<ButtonWidget>(id));
    c.move(getWidget<IconButtonWidget>("garage-background"), -2, -63, 360, 780);
    c.move(getWidget<ModelViewWidget>("kart-model"), 32, 162, 296, 260);
    c.move(getWidget<Widget>("stats-panel"), 54, 431, 254, 254);
    c.move(getWidget<ButtonWidget>("back"), 21, 26, 50, 50);
    c.move(getWidget<ButtonWidget>("previous"), 35, 684, 67, 64);
    c.move(getWidget<ButtonWidget>("next"), 258, 684, 67, 64);
    c.move(getWidget<ButtonWidget>("start"), 117, 695, 126, 47);
}

void FluxaraKartScreen::onResize()
{
    Screen::onResize();
    layoutControls();
}

void FluxaraKartScreen::onDraw(float)
{
    const FluxaraUI::Canvas c;
    // The approved contained scenery ends at y647. Fill its uncovered footer
    // before compositing the separate stats/nav layers, away from the 3D kart.
    GL32_draw2DRectangle(video::SColor(255,11,45,120),c.rect(0,647,360,133));
    c.image(m_garage_art[0], 22, 684, 316, 64);
    c.image(m_garage_art[1], 117, 695, 126, 47);
    c.image(m_garage_art[2], 21, 26, 50, 50);
    c.image(m_garage_art[3], 32, 36, 25, 31);
    c.image(m_garage_art[4], 268, 690, 47, 51);
    c.image(m_garage_art[5], 45, 690, 47, 51);
    c.label(L"GARAGE", 88, 32, 190, 38, 31);
    c.label(L"SELECT", 125, 703, 110, 28, 18);
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
        gui::ScalableFont* font = GUIEngine::getTitleFont();
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
    label(L"STATS", 80, 352, 168, 58);
    const wchar_t* labels[] = {L"WEIGHT", L"SPEED", L"ACCEL", L"NITRO"};
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
    // Clear targets left by a previously played mode before applying this
    // event's native target semantics. Arena/timed events never become races.
    RaceManager::get()->setHitCaptureTime(0,0.0f);
    RaceManager::get()->setTimeTarget(0.0f);
    if(FluxaraModes::timed(m_mode))
        RaceManager::get()->setTimeTarget(float(m_laps*60));
    if(m_mode=="free_for_all")
        RaceManager::get()->setHitCaptureTime(0,float(m_laps*60));
    if(m_mode=="egg_hunt") m_num_karts=1;
    RaceManager::get()->setNumKarts(std::max(1, m_num_karts));
    RaceManager::get()->setPlayerKart(0, kart);
    if(m_mode=="soccer")
    {
        RaceManager::get()->setKartTeam(0,KART_TEAM_RED);
        const int ai=std::max(0,m_num_karts-1);
        RaceManager::get()->setNumRedAI(ai/2);
        RaceManager::get()->setNumBlueAI(ai-ai/2);
    }
    // Keep rivals inside the curated Fluxara roster while allowing the player
    // to drive either bundled kart.
    RaceManager::get()->setAIKartOverride(
        m_karts[(m_selected_kart + 1) % m_karts.size()]);
    RaceManager::get()->setReverseTrack(false);

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
