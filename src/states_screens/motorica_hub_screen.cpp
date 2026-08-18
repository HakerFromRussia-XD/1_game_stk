//  Motorica Signal Lab standalone product screens

#include "states_screens/motorica_hub_screen.hpp"

#include "config/player_manager.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "guiengine/widgets/check_box_widget.hpp"
#include "guiengine/widgets/label_widget.hpp"
#include "guiengine/widgets/list_widget.hpp"
#include "guiengine/widgets/spinner_widget.hpp"
#include "states_screens/dialogs/message_dialog.hpp"
#include "states_screens/dialogs/select_challenge.hpp"
#include "states_screens/motorica_about_screen.hpp"
#include "states_screens/options/options_screen_general.hpp"
#include "states_screens/state_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"
#ifdef IOS_STK
#include "input/motorica_game_control_ios.hpp"
#include "input/motorica_standalone_training.hpp"
#endif

#include <algorithm>
#include <ctime>
#include <iomanip>
#include <sstream>

using namespace GUIEngine;

namespace
{
bool useRussian()
{
    if (translations == nullptr)
        return false;
    const std::string code = translations->getCurrentLanguageNameCode();
    return code == "ru" || code.find("ru_") == 0 || code.find("ru-") == 0;
}

core::stringw text(const char* russian, const char* english)
{
    return StringUtils::utf8ToWide(useRussian() ? russian : english);
}

void setText(Screen* screen, const char* id,
             const char* russian, const char* english)
{
    screen->getWidget(id)->setText(text(russian, english));
}

#ifdef IOS_STK
const char* challengeForExercise(StandaloneExerciseID exercise)
{
    switch (exercise)
    {
    case StandaloneExerciseID::Precision:
        return "motorica_precision";
    case StandaloneExerciseID::Reaction:
        return "motorica_reaction";
    case StandaloneExerciseID::SignalHold:
        return "motorica_signal_hold";
    }
    return "motorica_precision";
}

core::stringw exerciseName(StandaloneExerciseID exercise)
{
    switch (exercise)
    {
    case StandaloneExerciseID::Precision:
        return text("Точность", "Precision");
    case StandaloneExerciseID::Reaction:
        return text("Реакция", "Reaction");
    case StandaloneExerciseID::SignalHold:
        return text("Удержание сигнала", "Signal Hold");
    }
    return text("Точность", "Precision");
}

core::stringw exerciseDescription(StandaloneExerciseID exercise)
{
    switch (exercise)
    {
    case StandaloneExerciseID::Precision:
        return text(
            "Пройдите 12 неоновых ворот. Итог учитывает время, "
            "столкновения и плавность управления.",
            "Pass through 12 neon gates. Time, collisions and steering "
            "smoothness contribute to the result.");
    case StandaloneExerciseID::Reaction:
        return text(
            "Реагируйте на 20 команд направления. Тренировка измеряет "
            "скорость и точность реакции.",
            "Respond to 20 direction prompts. The exercise measures "
            "reaction speed and accuracy.");
    case StandaloneExerciseID::SignalHold:
        return text(
            "Удерживайте управление в 10 целевых диапазонах по три секунды.",
            "Keep steering inside 10 target ranges for three seconds each.");
    }
    return core::stringw();
}

StandaloneExerciseID exerciseFromHistoryId(const std::string& id)
{
    if (id == "reaction")
        return StandaloneExerciseID::Reaction;
    if (id == "signal_hold")
        return StandaloneExerciseID::SignalHold;
    return StandaloneExerciseID::Precision;
}
#endif
}

MotoricaHubScreen::MotoricaHubScreen()
    : Screen("motorica_hub.stkgui")
{
}

void MotoricaHubScreen::loadedFromFile()
{
}

void MotoricaHubScreen::init()
{
    Screen::init();

    setText(this, "hub_title", "Motorica Signal Lab", "Motorica Signal Lab");
    setText(this, "hub_subtitle", "Тренировка сигналов", "Signal training");
    setText(this, "full_game_notice",
        "Для запуска полной версии игры откройте Motorica Kart через "
        "приложение Motorica Start.",
        "To launch the full version of the game, open Motorica Kart through "
        "the Motorica Start app.");
    setText(this, "device_notice", "Устройство не подключено",
        "No device connected");
    getWidget<LabelWidget>("hub_subtitle")->setColor(
        irr::video::SColor(255, 255, 255, 255));
    getWidget<LabelWidget>("full_game_notice")->setColor(
        irr::video::SColor(255, 255, 255, 255));
    getWidget<LabelWidget>("device_notice")->setColor(
        irr::video::SColor(255, 255, 255, 255));
    setText(this, "precision", "Точность", "Precision");
    setText(this, "reaction", "Реакция", "Reaction");
    setText(this, "signal_hold", "Удержание сигнала", "Signal Hold");
    setText(this, "history", "История тренировок", "Training History");
    setText(this, "controls", "Управление", "Controls");
    setText(this, "settings", "Настройки", "Settings");
    setText(this, "about", "Об игре и Open Source", "About and Open Source");

    getWidget<ButtonWidget>("precision")->setFocusForPlayer(
        PLAYER_ID_GAME_MASTER);
}

void MotoricaHubScreen::eventCallback(Widget*, const std::string& name,
                                      const int)
{
#ifdef IOS_STK
    if (name == "precision" || name == "reaction" || name == "signal_hold")
    {
        StandaloneExerciseID exercise = StandaloneExerciseID::Precision;
        if (name == "reaction")
            exercise = StandaloneExerciseID::Reaction;
        else if (name == "signal_hold")
            exercise = StandaloneExerciseID::SignalHold;
        MotoricaStandaloneTraining::get()->configure(
            exercise, StandaloneInputSource::TouchGyro,
            StandaloneDemoMode::Manual);
        MotoricaExerciseScreen::getInstance()->push();
    }
    else if (name == "history")
    {
        MotoricaHistoryScreen::getInstance()->push();
    }
    else
#endif
    if (name == "controls")
    {
        new MessageDialog(text(
            "Перед началом упражнения выберите экран/гироскоп или "
            "демонстрацию сигналов. В ручной демонстрации две экранные "
            "кнопки формируют сигналы открытия и закрытия. Автосценарий "
            "показывает калибровку, потерю и восстановление связи.",
            "Before an exercise, choose touch/gyroscope or Signal "
            "Demonstration. Manual demonstration uses two on-screen signal "
            "controls. The scripted flow demonstrates calibration, signal "
            "loss and recovery."));
    }
    else if (name == "settings")
    {
        OptionsScreenGeneral::getInstance()->push();
    }
    else if (name == "about")
    {
        MotoricaAboutScreen::getInstance()->push();
    }
}

bool MotoricaHubScreen::onEscapePressed()
{
    return false;
}

MotoricaExerciseScreen::MotoricaExerciseScreen()
    : Screen("motorica_exercise.stkgui")
{
}

void MotoricaExerciseScreen::loadedFromFile()
{
}

void MotoricaExerciseScreen::init()
{
    Screen::init();
#ifdef IOS_STK
    MotoricaStandaloneTraining* training = MotoricaStandaloneTraining::get();
    getWidget("exercise_title")->setText(exerciseName(training->getExercise()));
    getWidget("exercise_description")->setText(
        exerciseDescription(training->getExercise()));

    setText(this, "input_label", "Источник управления", "Control source");
    SpinnerWidget* source = getWidget<SpinnerWidget>("input_source");
    source->clearLabels();
    source->addLabel(text("Экран и гироскоп", "Touch and gyroscope"));
    source->addLabel(text("Демонстрация сигналов Motorica",
                          "Motorica Signal Demonstration"));
    source->setValue(training->getInputSource() ==
        StandaloneInputSource::SimulatedSignals ? 1 : 0);

    setText(this, "demo_label", "Режим демонстрации", "Demonstration mode");
    SpinnerWidget* demo = getWidget<SpinnerWidget>("demo_mode");
    demo->clearLabels();
    demo->addLabel(text("Ручное управление", "Manual controls"));
    demo->addLabel(text("Автоматический сценарий", "Scripted demonstration"));
    demo->setValue(training->getDemoMode() == StandaloneDemoMode::Scripted ? 1 : 0);

    setText(this, "open_label", "Сигнал открытия", "Open signal");
    setText(this, "close_label", "Сигнал закрытия", "Close signal");
    setText(this, "connected_label", "Виртуальное соединение",
            "Virtual connection");
    getWidget<SpinnerWidget>("open_level")->setValue(32);
    getWidget<SpinnerWidget>("close_level")->setValue(32);
    getWidget<CheckBoxWidget>("connected")->setState(true);
    setText(this, "start", "Начать тренировку", "Start Training");
    updateVisibleControls();
    source->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
#endif
}

void MotoricaExerciseScreen::updateVisibleControls()
{
#ifdef IOS_STK
    const bool simulated = getWidget<SpinnerWidget>("input_source")->getValue() == 1;
    const bool manual = getWidget<SpinnerWidget>("demo_mode")->getValue() == 0;
    getWidget("demo_label")->setVisible(simulated);
    getWidget("demo_mode")->setVisible(simulated);
    getWidget("open_label")->setVisible(simulated && manual);
    getWidget("open_level")->setVisible(simulated && manual);
    getWidget("close_label")->setVisible(simulated && manual);
    getWidget("close_level")->setVisible(simulated && manual);
    getWidget("connected_label")->setVisible(simulated && manual);
    getWidget("connected")->setVisible(simulated && manual);
#endif
}

void MotoricaExerciseScreen::eventCallback(Widget*, const std::string& name,
                                           const int)
{
#ifdef IOS_STK
    MotoricaStandaloneTraining* training = MotoricaStandaloneTraining::get();
    if (name == "back")
    {
        StateManager::get()->escapePressed();
        return;
    }
    if (name == "input_source" || name == "demo_mode")
    {
        updateVisibleControls();
        training->configure(
            training->getExercise(),
            getWidget<SpinnerWidget>("input_source")->getValue() == 1 ?
                StandaloneInputSource::SimulatedSignals :
                StandaloneInputSource::TouchGyro,
            getWidget<SpinnerWidget>("demo_mode")->getValue() == 1 ?
                StandaloneDemoMode::Scripted : StandaloneDemoMode::Manual);
        return;
    }
    if (name == "start")
    {
        const StandaloneInputSource source =
            getWidget<SpinnerWidget>("input_source")->getValue() == 1 ?
                StandaloneInputSource::SimulatedSignals :
                StandaloneInputSource::TouchGyro;
        const StandaloneDemoMode mode =
            getWidget<SpinnerWidget>("demo_mode")->getValue() == 1 ?
                StandaloneDemoMode::Scripted : StandaloneDemoMode::Manual;
        training->configure(training->getExercise(), source, mode);
        training->configureManualFrame(
            getWidget<SpinnerWidget>("open_level")->getValue(),
            getWidget<SpinnerWidget>("close_level")->getValue(),
            getWidget<CheckBoxWidget>("connected")->getState());
        PlayerManager::get()->enforceCurrentPlayer();
        if (!SelectChallengeDialog::startRace(
                challengeForExercise(training->getExercise()), false))
        {
            new MessageDialog(text(
                "Не удалось открыть тренировку. Проверьте пакет Signal Lab.",
                "The training could not be opened. Check the Signal Lab assets."));
        }
    }
#else
    (void)name;
#endif
}

MotoricaHistoryScreen::MotoricaHistoryScreen()
    : Screen("motorica_history.stkgui")
{
}

void MotoricaHistoryScreen::loadedFromFile()
{
}

void MotoricaHistoryScreen::init()
{
    Screen::init();
    setText(this, "history_title", "История тренировок", "Training History");
    ListWidget* list = getWidget<ListWidget>("history_list");
    list->clear();
#ifdef IOS_STK
    std::vector<StandaloneTrainingResult> history =
        MotoricaStandaloneTraining::get()->loadHistory();
    std::reverse(history.begin(), history.end());
    int index = 0;
    for (const StandaloneTrainingResult& item : history)
    {
        std::time_t timestamp = (std::time_t)item.started_at;
        std::tm local = *std::localtime(&timestamp);
        std::ostringstream date;
        date << std::put_time(&local, "%d.%m.%Y %H:%M");
        std::ostringstream line;
        line << StringUtils::wideToUtf8(
            exerciseName(exerciseFromHistoryId(item.exercise_id)))
             << "  •  " << item.score << "/1000  •  "
             << (item.input_source == "simulated_signals" ?
                 (useRussian() ? "сигналы" : "signals") :
                 (useRussian() ? "экран" : "touch"))
             << "  •  " << date.str();
        list->addItem("training_" + StringUtils::toString(index++),
                      StringUtils::utf8ToWide(line.str()));
    }
    if (history.empty())
    {
        list->addItem("empty", text(
            "Здесь появятся результаты последних 20 тренировок.",
            "Results from the latest 20 training sessions will appear here."));
    }
#endif
    list->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}

void MotoricaHistoryScreen::eventCallback(Widget*, const std::string& name,
                                          const int)
{
    if (name == "back")
        StateManager::get()->escapePressed();
}
