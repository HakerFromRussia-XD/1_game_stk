//  Motorica Signal Lab standalone training state.
//  This module is intentionally independent from MotoricaGameControl and
//  never reads the shared App Group used by Motorica Start.

#ifndef HEADER_MOTORICA_STANDALONE_TRAINING_HPP
#define HEADER_MOTORICA_STANDALONE_TRAINING_HPP

#ifdef IOS_STK

#include "input/input.hpp"
#include "input/motorica_game_control_ios.hpp"
#include "io/file_manager.hpp"
#include "karts/controller/controller.hpp"
#include "utils/log.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

enum class StandaloneExerciseID
{
    Precision,
    Reaction,
    SignalHold
};

enum class StandaloneInputSource
{
    TouchGyro,
    SimulatedSignals
};

enum class StandaloneDemoMode
{
    Manual,
    Scripted
};

struct SimulatedSignalFrame
{
    float open_level = 32.0f;
    float close_level = 32.0f;
    bool connected = true;
    uint64_t timestamp_ms = 0;
};

struct StandaloneTrainingResult
{
    int schema_version = 1;
    std::string exercise_id;
    std::string input_source;
    long long started_at = 0;
    int duration_ms = 0;
    int score = 0;
    std::string metrics;
};

class MotoricaStandaloneTraining
{
private:
    StandaloneExerciseID m_exercise = StandaloneExerciseID::Precision;
    StandaloneInputSource m_input = StandaloneInputSource::TouchGyro;
    StandaloneDemoMode m_demo_mode = StandaloneDemoMode::Manual;
    SimulatedSignalFrame m_signal;
    bool m_active = false;
    bool m_finished = false;
    bool m_manual_open_pressed = false;
    bool m_manual_close_pressed = false;
    bool m_script_enabled = false;
    std::string m_last_logged_phase;
    float m_started_world_time = 0.0f;
    long long m_started_at = 0;
    float m_last_steer = 0.0f;
    float m_rest_open = 32.0f;
    float m_rest_close = 32.0f;
    float m_max_open = 230.0f;
    float m_max_close = 230.0f;
    float m_smoothness = 0.0f;
    float m_hold_seconds = 0.0f;
    float m_observed_seconds = 0.0f;
    std::array<int, 20> m_reaction_targets{};
    std::vector<float> m_reaction_times;
    int m_reaction_prompt = -1;
    int m_reaction_correct = 0;
    int m_reaction_errors = 0;
    int m_reaction_answered_count = 0;
    bool m_reaction_answered = false;
    int m_collisions = 0;
    int m_precision_gate = 0;
    float m_precision_deviation = 0.0f;
    float m_overshoot_seconds = 0.0f;
    StandaloneTrainingResult m_last_result;

    MotoricaStandaloneTraining() = default;

    static const char* exerciseId(StandaloneExerciseID id)
    {
        switch (id)
        {
        case StandaloneExerciseID::Precision:  return "precision";
        case StandaloneExerciseID::Reaction:   return "reaction";
        case StandaloneExerciseID::SignalHold: return "signal_hold";
        }
        return "precision";
    }

    static const char* inputId(StandaloneInputSource source)
    {
        return source == StandaloneInputSource::SimulatedSignals ?
            "simulated_signals" : "touch_gyro";
    }

    std::string historyPath() const
    {
        return file_manager == nullptr ? std::string() :
            file_manager->getUserConfigFile("motorica_training_history.tsv");
    }

    static std::vector<std::string> split(const std::string& value, char token)
    {
        std::vector<std::string> output;
        std::stringstream stream(value);
        std::string part;
        while (std::getline(stream, part, token))
            output.push_back(part);
        return output;
    }

    void saveResult(const StandaloneTrainingResult& result)
    {
        std::vector<StandaloneTrainingResult> history = loadHistory();
        history.push_back(result);
        if (history.size() > 20)
            history.erase(history.begin(), history.end() - 20);

        const std::string path = historyPath();
        if (path.empty())
            return;
        const std::string temporary = path + ".tmp";
        std::ofstream output(temporary.c_str(), std::ios::trunc);
        if (!output)
        {
            Log::error("MotoricaTraining", "Cannot write history: %s",
                       temporary.c_str());
            return;
        }
        for (const StandaloneTrainingResult& item : history)
        {
            output << item.schema_version << '\t' << item.exercise_id << '\t'
                   << item.input_source << '\t' << item.started_at << '\t'
                   << item.duration_ms << '\t' << item.score << '\t'
                   << item.metrics << '\n';
        }
        output.close();
        if (std::rename(temporary.c_str(), path.c_str()) != 0)
            Log::error("MotoricaTraining", "Cannot replace history: %s",
                       path.c_str());
    }

    void updateScript(float elapsed)
    {
        // A repeatable, visible scenario: disconnect, three calibration
        // stages, active control, signal loss and automatic recovery.
        if (elapsed < 2.0f)
        {
            m_signal.connected = false;
            m_signal.open_level = m_signal.close_level = 32.0f;
        }
        else if (elapsed < 5.0f) // rest calibration
        {
            m_signal.connected = true;
            m_signal.open_level = m_signal.close_level = 32.0f;
            m_rest_open = m_signal.open_level;
            m_rest_close = m_signal.close_level;
        }
        else if (elapsed < 8.0f) // opening channel calibration
        {
            m_signal.connected = true;
            m_signal.open_level = 230.0f;
            m_signal.close_level = 32.0f;
            m_max_open = std::max(m_max_open, m_signal.open_level);
        }
        else if (elapsed < 11.0f) // closing channel calibration
        {
            m_signal.connected = true;
            m_signal.open_level = 32.0f;
            m_signal.close_level = 230.0f;
            m_max_close = std::max(m_max_close, m_signal.close_level);
        }
        else if (elapsed < 23.0f)
        {
            m_signal.connected = true;
            const float wave = std::sin((elapsed - 11.0f) * 0.9f);
            m_signal.open_level = wave < 0.0f ? 32.0f - wave * 205.0f : 32.0f;
            m_signal.close_level = wave > 0.0f ? 32.0f + wave * 205.0f : 32.0f;
        }
        else if (elapsed < 27.0f)
        {
            m_signal.connected = false;
            m_signal.open_level = m_signal.close_level = 32.0f;
        }
        else
        {
            m_signal.connected = true;
            const float wave = std::sin((elapsed - 27.0f) * 0.72f);
            m_signal.open_level = wave < 0.0f ? 32.0f - wave * 205.0f : 32.0f;
            m_signal.close_level = wave > 0.0f ? 32.0f + wave * 205.0f : 32.0f;
        }
    }

public:
    static MotoricaStandaloneTraining* get()
    {
        static MotoricaStandaloneTraining instance;
        return &instance;
    }

    void configure(StandaloneExerciseID exercise,
                   StandaloneInputSource input,
                   StandaloneDemoMode demo_mode)
    {
        if (!isMotoricaStandaloneModeIOS())
            return;
        m_exercise = exercise;
        m_input = input;
        m_demo_mode = demo_mode;
        m_script_enabled = demo_mode == StandaloneDemoMode::Scripted;
        if (m_input != StandaloneInputSource::SimulatedSignals ||
            m_demo_mode == StandaloneDemoMode::Scripted)
            m_signal = SimulatedSignalFrame();
    }

    void beginRace()
    {
        if (!isMotoricaStandaloneModeIOS())
            return;
        m_active = true;
        m_finished = false;
        m_started_world_time = 0.0f;
        m_started_at = (long long)std::time(nullptr);
        m_last_steer = 0.0f;
        m_rest_open = 32.0f;
        m_rest_close = 32.0f;
        m_max_open = 230.0f;
        m_max_close = 230.0f;
        m_smoothness = 0.0f;
        m_hold_seconds = 0.0f;
        m_observed_seconds = 0.0f;
        std::minstd_rand reaction_random(
            static_cast<unsigned int>(m_started_at) ^ 0x4d534c42u);
        std::uniform_int_distribution<int> reaction_side(0, 1);
        for (size_t index = 0; index < m_reaction_targets.size(); index++)
        {
            int side = reaction_side(reaction_random) == 0 ? -1 : 1;
            // Avoid long, visually ambiguous runs while keeping every session
            // unpredictable for the user.
            if (index >= 2 && m_reaction_targets[index - 1] == side &&
                m_reaction_targets[index - 2] == side)
                side = -side;
            m_reaction_targets[index] = side;
        }
        m_reaction_times.clear();
        m_reaction_prompt = -1;
        m_reaction_correct = 0;
        m_reaction_errors = 0;
        m_reaction_answered_count = 0;
        m_reaction_answered = false;
        m_collisions = 0;
        m_precision_gate = 0;
        m_precision_deviation = 0.0f;
        m_overshoot_seconds = 0.0f;
        m_manual_open_pressed = false;
        m_manual_close_pressed = false;
        m_last_logged_phase.clear();
        if (m_input != StandaloneInputSource::SimulatedSignals ||
            m_demo_mode == StandaloneDemoMode::Scripted)
            m_signal = SimulatedSignalFrame();
        Log::info("MotoricaTraining", "Started %s with %s",
                  exerciseId(m_exercise), inputId(m_input));
    }

    void prepareRepeat()
    {
        beginRace();
    }

    void stop()
    {
        m_active = false;
    }

    bool isActive() const
    {
        return m_active && isMotoricaStandaloneModeIOS();
    }

    bool usesSimulatedSignals() const
    {
        return isActive() && m_input == StandaloneInputSource::SimulatedSignals;
    }

    bool isScripted() const
    {
        return m_script_enabled;
    }

    StandaloneExerciseID getExercise() const { return m_exercise; }
    StandaloneInputSource getInputSource() const { return m_input; }
    StandaloneDemoMode getDemoMode() const { return m_demo_mode; }
    const SimulatedSignalFrame& getSignal() const { return m_signal; }
    const StandaloneTrainingResult& getLastResult() const { return m_last_result; }

    float getCalculatedAxis() const
    {
        if (!m_signal.connected)
            return 0.0f;
        const float open_range = std::max(1.0f, m_max_open - m_rest_open);
        const float close_range = std::max(1.0f, m_max_close - m_rest_close);
        const float opening = std::max(0.0f, std::min(1.0f,
            (m_signal.open_level - m_rest_open) / open_range));
        const float closing = std::max(0.0f, std::min(1.0f,
            (m_signal.close_level - m_rest_close) / close_range));
        return std::max(-1.0f, std::min(1.0f, opening - closing));
    }

    int getProgressCount(float elapsed) const
    {
        switch (m_exercise)
        {
        case StandaloneExerciseID::Precision:
            return std::max(0, std::min(12, m_precision_gate));
        case StandaloneExerciseID::Reaction:
            return std::max(1, std::min(20, (int)(elapsed / 2.0f) + 1));
        case StandaloneExerciseID::SignalHold:
            return std::max(1, std::min(10, (int)(elapsed / 3.0f) + 1));
        }
        return 0;
    }

    int getProgressTotal() const
    {
        return m_exercise == StandaloneExerciseID::Precision ? 12 :
               m_exercise == StandaloneExerciseID::Reaction ? 20 : 10;
    }

    float getDemoElapsed(float world_time) const
    {
        return m_started_world_time == 0.0f ? 0.0f :
            std::max(0.0f, world_time - m_started_world_time);
    }

    float getExerciseElapsed(float world_time) const
    {
        const float demo_elapsed = getDemoElapsed(world_time);
        if (!usesSimulatedSignals() || !m_script_enabled)
            return demo_elapsed;

        // The automatic demonstration spends its first eleven seconds on
        // connection and calibration.  A later four-second signal outage is
        // a real training pause: progress, prompts and scoring all stop, while
        // the demonstration clock keeps running so recovery can still occur.
        if (demo_elapsed <= 11.0f)
            return 0.0f;
        if (demo_elapsed <= 23.0f)
            return demo_elapsed - 11.0f;
        if (demo_elapsed <= 27.0f)
            return 12.0f;
        return demo_elapsed - 15.0f;
    }

    bool isTrainingPaused(float world_time) const
    {
        if (!usesSimulatedSignals())
            return false;
        if (!m_signal.connected)
            return true;
        if (!m_script_enabled)
            return false;
        return getDemoElapsed(world_time) < 11.0f;
    }

    void configureManualFrame(float open_level, float close_level,
                              bool connected)
    {
        if (!isMotoricaStandaloneModeIOS())
            return;
        m_signal.open_level = std::max(0.0f, std::min(255.0f, open_level));
        m_signal.close_level = std::max(0.0f, std::min(255.0f, close_level));
        m_signal.connected = connected;
    }

    float getTargetAxis(float elapsed) const
    {
        if (m_exercise == StandaloneExerciseID::Reaction)
        {
            const int index = std::max(0, std::min(19, (int)(elapsed / 2.0f)));
            return m_reaction_targets[index] * 0.72f;
        }
        if (m_exercise == StandaloneExerciseID::SignalHold)
        {
            static const float targets[10] = {
                -0.65f, 0.65f, -0.35f, 0.35f, 0.0f,
                 0.65f, -0.65f, 0.35f, -0.35f, 0.0f
            };
            const int index = std::max(0, std::min(9, (int)(elapsed / 3.0f)));
            return targets[index];
        }
        return 0.0f;
    }

    std::string getPhaseName(float elapsed) const
    {
        if (!usesSimulatedSignals())
            return "touch";
        if (!m_script_enabled)
            return m_signal.connected ? "manual" : "disconnected";
        if (elapsed < 2.0f) return "disconnected";
        if (elapsed < 5.0f) return "calibration_rest";
        if (elapsed < 8.0f) return "calibration_open";
        if (elapsed < 11.0f) return "calibration_close";
        if (elapsed < 23.0f) return "control";
        if (elapsed < 27.0f) return "signal_lost";
        return "restored";
    }

    void setManualSignal(bool opening, bool pressed)
    {
        if (!usesSimulatedSignals())
            return;
        m_script_enabled = false;
        if (opening)
            m_manual_open_pressed = pressed;
        else
            m_manual_close_pressed = pressed;
        m_signal.open_level = m_manual_open_pressed ? 235.0f : 32.0f;
        m_signal.close_level = m_manual_close_pressed ? 235.0f : 32.0f;
    }

    void toggleConnection()
    {
        if (!usesSimulatedSignals())
            return;
        m_script_enabled = false;
        m_signal.connected = !m_signal.connected;
    }

    void toggleScript()
    {
        if (!usesSimulatedSignals())
            return;
        m_script_enabled = !m_script_enabled;
        if (m_script_enabled)
            m_started_world_time = 0.0f;
    }

    void apply(Controller* controller, float world_time)
    {
        constexpr int INPUT_MAX_VALUE = 32768;
        if (!controller || !usesSimulatedSignals())
            return;
        if (m_started_world_time == 0.0f)
            m_started_world_time = world_time;
        const float elapsed = getDemoElapsed(world_time);
        if (m_script_enabled)
            updateScript(elapsed);

        const std::string phase = getPhaseName(elapsed);
        if (phase != m_last_logged_phase)
        {
            m_last_logged_phase = phase;
            Log::info("MotoricaTraining",
                      "Demo phase=%s connected=%d open=%d close=%d axis=%.3f",
                      phase.c_str(), m_signal.connected ? 1 : 0,
                      (int)m_signal.open_level, (int)m_signal.close_level,
                      getCalculatedAxis());
        }

        controller->action(PA_ACCEL, m_signal.connected ? INPUT_MAX_VALUE : 0);
        controller->action(PA_BRAKE, m_signal.connected ? 0 : INPUT_MAX_VALUE);
        controller->action(PA_STEER_LEFT, 0);
        controller->action(PA_STEER_RIGHT, 0);
        if (!m_signal.connected)
            return;

        const float axis = getCalculatedAxis();
        if (std::fabs(axis) < 0.04f)
            return;
        const int value = std::min(INPUT_MAX_VALUE,
            (int)(std::fabs(axis) * INPUT_MAX_VALUE));
        if (axis > 0.0f)
            controller->action(PA_STEER_RIGHT, value);
        else
            controller->action(PA_STEER_LEFT, value);
    }

    void observe(float steer, float dt, float world_time,
                 float kart_x, float kart_z)
    {
        if (!isActive() || dt <= 0.0f)
            return;
        if (m_started_world_time == 0.0f)
            m_started_world_time = world_time;
        const float demo_elapsed = getDemoElapsed(world_time);
        if ((m_input == StandaloneInputSource::SimulatedSignals &&
             !m_signal.connected) ||
            (m_script_enabled && demo_elapsed < 11.0f))
            return;
        const float elapsed = getExerciseElapsed(world_time);
        m_observed_seconds += dt;
        m_smoothness += std::fabs(steer - m_last_steer);
        m_last_steer = steer;

        if (m_exercise == StandaloneExerciseID::Precision)
        {
            // Positions match the twelve physical neon gates generated by
            // build_assets.py. Gates must be crossed in sequence, so cutting
            // through the infield cannot produce a perfect result.
            static const float gates[12][2] = {
                {  0.0f,  62.0f}, {-42.0f,  43.0f}, {-50.0f,  10.0f},
                {-61.0f, -22.0f}, {-34.0f, -49.0f}, {  0.0f, -48.0f},
                { 25.0f, -38.0f}, { 56.0f, -28.0f}, { 54.0f,   8.0f},
                { 62.0f,  33.0f}, { 31.0f,  55.0f}, { 12.0f,  65.0f}
            };
            if (m_precision_gate < 12)
            {
                const float dx = kart_x - gates[m_precision_gate][0];
                const float dz = kart_z - gates[m_precision_gate][1];
                const float distance = std::sqrt(dx * dx + dz * dz);
                if (distance < 8.0f)
                {
                    m_precision_deviation += distance;
                    m_precision_gate++;
                }
            }
        }
        else if (m_exercise == StandaloneExerciseID::Reaction)
        {
            const int prompt = std::max(0, std::min(19, (int)(elapsed / 2.0f)));
            if (prompt != m_reaction_prompt)
            {
                m_reaction_prompt = prompt;
                m_reaction_answered = false;
            }
            const float target = getTargetAxis(elapsed);
            if (!m_reaction_answered && std::fabs(steer) > 0.45f)
            {
                m_reaction_answered = true;
                m_reaction_answered_count++;
                const float reaction = std::fmod(elapsed, 2.0f);
                if (steer * target > 0.0f)
                {
                    m_reaction_correct++;
                    m_reaction_times.push_back(reaction);
                }
                else
                {
                    m_reaction_errors++;
                }
            }
        }
        else if (m_exercise == StandaloneExerciseID::SignalHold)
        {
            if (elapsed <= 30.0f)
            {
                if (std::fabs(steer - getTargetAxis(elapsed)) <= 0.20f)
                    m_hold_seconds += dt;
                else
                    m_overshoot_seconds += dt;
            }
        }
    }

    bool shouldFinish(float world_time) const
    {
        if (!isActive() || m_started_world_time == 0.0f)
            return false;
        const float elapsed = getExerciseElapsed(world_time);
        switch (m_exercise)
        {
        case StandaloneExerciseID::Precision:
            return m_precision_gate >= 12 || elapsed >= 120.0f;
        case StandaloneExerciseID::Reaction:
            return elapsed >= 40.0f; // exactly 20 two-second prompts
        case StandaloneExerciseID::SignalHold:
            return elapsed >= 30.0f; // exactly 10 three-second ranges
        }
        return false;
    }

    void recordCollision()
    {
        if (isActive())
            m_collisions++;
    }

    void finish(float time_seconds)
    {
        if (!isActive() || m_finished)
            return;
        m_finished = true;
        m_active = false;
        const float exercise_seconds = m_started_world_time == 0.0f ?
            std::max(0.0f, time_seconds) : getExerciseElapsed(time_seconds);

        int score = 0;
        std::ostringstream metrics;
        if (m_exercise == StandaloneExerciseID::Precision)
        {
            const int smoothness_penalty = std::min(420, (int)(m_smoothness * 9.0f));
            const int time_penalty = std::max(
                0, (int)((exercise_seconds - 70.0f) * 4.0f));
            const int missed = 12 - m_precision_gate;
            const int deviation_penalty = std::min(180,
                (int)(m_precision_deviation * 3.0f));
            score = 1000 - missed * 90 - m_collisions * 100 -
                    smoothness_penalty - deviation_penalty - time_penalty;
            metrics << "gates=" << m_precision_gate << ";missed=" << missed
                    << ";collisions=" << m_collisions
                    << ";deviation=" << (int)(m_precision_deviation * 100.0f);
        }
        else if (m_exercise == StandaloneExerciseID::Reaction)
        {
            const int prompts = std::max(1, m_reaction_prompt + 1);
            const int misses = std::max(0, prompts - m_reaction_answered_count);
            float median = 2.0f;
            if (!m_reaction_times.empty())
            {
                std::sort(m_reaction_times.begin(), m_reaction_times.end());
                const size_t middle = m_reaction_times.size() / 2;
                median = m_reaction_times.size() % 2 == 0 ?
                    (m_reaction_times[middle - 1] + m_reaction_times[middle]) /
                        2.0f : m_reaction_times[middle];
            }
            score = m_reaction_correct * 50 - m_reaction_errors * 35 -
                    misses * 25 - (int)(median * 80.0f);
            metrics << "correct=" << m_reaction_correct
                    << ";errors=" << m_reaction_errors
                    << ";missed=" << misses
                    << ";median_ms=" << (int)(median * 1000.0f);
        }
        else
        {
            const float denominator = std::max(1.0f, std::min(30.0f, m_observed_seconds));
            score = (int)(1000.0f * m_hold_seconds / denominator) -
                    (int)(m_overshoot_seconds * 8.0f) - m_collisions * 60;
            metrics << "hold_ms=" << (int)(m_hold_seconds * 1000.0f)
                    << ";target_ms=" << (int)(denominator * 1000.0f)
                    << ";overshoot_ms=" << (int)(m_overshoot_seconds * 1000.0f)
                    << ";collisions=" << m_collisions;
        }
        score = std::max(0, std::min(1000, score));

        m_last_result.schema_version = 1;
        m_last_result.exercise_id = exerciseId(m_exercise);
        m_last_result.input_source = inputId(m_input);
        m_last_result.started_at = m_started_at;
        m_last_result.duration_ms = std::max(
            0, (int)(exercise_seconds * 1000.0f));
        m_last_result.score = score;
        m_last_result.metrics = metrics.str();
        saveResult(m_last_result);
        Log::info("MotoricaTraining", "Finished %s score=%d metrics=%s",
                  m_last_result.exercise_id.c_str(), score,
                  m_last_result.metrics.c_str());
    }

    std::vector<StandaloneTrainingResult> loadHistory() const
    {
        std::vector<StandaloneTrainingResult> history;
        const std::string path = historyPath();
        std::ifstream input(path.c_str());
        std::string line;
        while (std::getline(input, line))
        {
            const std::vector<std::string> parts = split(line, '\t');
            if (parts.size() != 7)
                continue;
            StandaloneTrainingResult result;
            try
            {
                result.schema_version = std::stoi(parts[0]);
                result.exercise_id = parts[1];
                result.input_source = parts[2];
                result.started_at = std::stoll(parts[3]);
                result.duration_ms = std::stoi(parts[4]);
                result.score = std::stoi(parts[5]);
                result.metrics = parts[6];
            }
            catch (...)
            {
                continue;
            }
            if (result.schema_version == 1)
                history.push_back(result);
        }
        if (history.size() > 20)
            history.erase(history.begin(), history.end() - 20);
        return history;
    }
};

#endif // IOS_STK

#endif
