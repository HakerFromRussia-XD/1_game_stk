// Fluxara Drift - iOS kart selection

#include "states_screens/fluxara_kart_screen.hpp"

#include "config/player_manager.hpp"
#include "config/user_config.hpp"
#include "ge_render_info.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/model_view_widget.hpp"
#include "input/device_manager.hpp"
#include "input/input_manager.hpp"
#include "karts/kart_model.hpp"
#include "karts/kart_properties.hpp"
#include "karts/kart_properties_manager.hpp"
#include "race/race_manager.hpp"
#include "states_screens/state_manager.hpp"
#include "tracks/track.hpp"

#include <cmath>
#include <sstream>

using namespace GUIEngine;
using namespace irr;

FluxaraKartScreen::FluxaraKartScreen()
    : Screen("fluxara_kart.stkgui")
{
}

void FluxaraKartScreen::loadedFromFile()
{
}

void FluxaraKartScreen::setRace(Track* track, int laps)
{
    m_track = track;
    m_laps = laps;
}

void FluxaraKartScreen::init()
{
    Screen::init();

    m_karts = kart_properties_manager->getAllAvailableKarts();
    if (m_karts.empty())
    {
        getWidget<LabelWidget>("kart-name")->setText("No drive available", false);
        return;
    }

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

    getWidget<LabelWidget>("kart-name")->setText(props->getName(), false);
    std::ostringstream stats;
    stats << "Speed " << std::lround(props->getEngineMaxSpeed() * 3.6f)
          << " km/h   Acceleration "
          << std::lround(props->getAccelerationEfficiency() * 100.0f)
          << "%   Weight " << std::lround(props->getMass()) << " kg";
    getWidget<LabelWidget>("kart-stats")->setText(
        core::stringw(stats.str().c_str()), false);
}

void FluxaraKartScreen::startRace()
{
    if (!m_track || m_karts.empty())
        return;

    const std::string& kart = m_karts[m_selected_kart];
    UserConfigParams::m_default_kart = kart;

    RaceManager::get()->setNumPlayers(1);
    RaceManager::get()->setNumKarts(std::max(1, int(
        UserConfigParams::m_num_karts_per_gamemode[
            RaceManager::MINOR_MODE_NORMAL_RACE])));
    RaceManager::get()->setPlayerKart(0, kart);
    RaceManager::get()->setReverseTrack(false);

    if (StateManager::get()->activePlayerCount() == 0)
    {
        InputDevice* device = input_manager->getDeviceManager()
            ->getLatestUsedDevice();
        StateManager::get()->createActivePlayer(PlayerManager::getCurrentPlayer(),
                                                device);
    }

    input_manager->getDeviceManager()->setAssignMode(ASSIGN);
    input_manager->getDeviceManager()->setSinglePlayer(
        StateManager::get()->getActivePlayer(0));
    RaceManager::get()->startSingleRace(m_track->getIdent(), m_laps, false);
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
    StateManager::get()->escapePressed();
    return true;
}
