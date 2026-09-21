#ifndef HEADER_FLUXARA_EVENT_HPP
#define HEADER_FLUXARA_EVENT_HPP
#include "race/race_manager.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"
#include <irrString.h>
#include <string>

struct FluxaraEvent
{
    std::string id, mode, track, segment;
};

struct FluxaraSegment
{
    std::string id;
    irr::core::stringw title;
    unsigned int unlock_completed = 0;
};

namespace FluxaraModes
{
// Kept outside UserConfigParams so an automated simulator pass never becomes
// a persisted player preference or changes the shipped interaction flow.
inline bool& autoCampaignValidation()
{
    static bool enabled = false;
    return enabled;
}
inline bool& autoCampaignSmoke()
{
    static bool enabled = false;
    return enabled;
}
// Temporary Simulator-only acceptance switch.  It is intentionally separate
// from the public campaign state and must be removed with the validation run.
inline bool& forceValidationWins()
{
    static bool enabled = false;
    return enabled;
}
// The result screen marks an advance during its update pass. MainLoop
// consumes it after GUIEngine::update returns, when replacing the result
// screen and deleting the race world is safe.
inline bool& autoCampaignAdvancePending()
{
    static bool pending = false;
    return pending;
}
// A failed validation race is replayed through the same visible action. This
// keeps the process and the campaign event alive; it never grants progress.
inline bool& autoCampaignReplayPending()
{
    static bool pending = false;
    return pending;
}
// These are validation outcomes, not player progress.  They make the
// simulator runner fail closed: a loss or a still-locked next event stops it
// on an observable screen rather than quietly skipping ahead.
inline bool& autoCampaignFailed()
{
    static bool failed = false;
    return failed;
}
inline bool& autoCampaignFinished()
{
    static bool finished = false;
    return finished;
}
inline RaceManager::MinorRaceModeType nativeMode(const std::string& mode)
{
    if (mode=="normal") return RaceManager::MINOR_MODE_NORMAL_RACE;
    if (mode=="time_trial" || mode=="ghost_geometry") return RaceManager::MINOR_MODE_TIME_TRIAL;
    if (mode=="follow_leader") return RaceManager::MINOR_MODE_FOLLOW_LEADER;
    if (mode=="lap_trial") return RaceManager::MINOR_MODE_LAP_TRIAL;
    if (mode=="three_strikes") return RaceManager::MINOR_MODE_3_STRIKES;
    if (mode=="free_for_all") return RaceManager::MINOR_MODE_FREE_FOR_ALL;
    if (mode=="soccer") return RaceManager::MINOR_MODE_SOCCER;
    if (mode=="capture_the_flag") return RaceManager::MINOR_MODE_CAPTURE_THE_FLAG;
    if (mode=="egg_hunt") return RaceManager::MINOR_MODE_EASTER_EGG;
    return RaceManager::MINOR_MODE_NONE;
}
inline irr::core::stringw label(const std::string& mode)
{
    if(mode=="normal") return _C("fluxara", "NORMAL RACE");
    if(mode=="time_trial") return _C("fluxara", "TIME TRIAL");
    if(mode=="ghost_geometry") return _C("fluxara", "GHOST RUN");
    if(mode=="follow_leader") return _C("fluxara", "FOLLOW THE LEADER");
    if(mode=="lap_trial") return _C("fluxara", "LAP TRIAL");
    if(mode=="three_strikes") return _C("fluxara", "THREE STRIKES");
    if(mode=="free_for_all") return _C("fluxara", "FREE FOR ALL");
    if(mode=="soccer") return _C("fluxara", "SOCCER");
    if(mode=="capture_the_flag") return _C("fluxara", "CAPTURE THE FLAG");
    if(mode=="egg_hunt") return _C("fluxara", "EGG HUNT");
    return _C("fluxara", "UNAVAILABLE MODE");
}
inline bool laps(const std::string& mode)
{ return mode=="normal" || mode=="time_trial"; }
inline bool timed(const std::string& mode)
{ return mode=="lap_trial" || mode=="free_for_all" || mode=="soccer"; }
inline bool arena(const std::string& mode)
{ return mode=="three_strikes" || mode=="free_for_all" || mode=="capture_the_flag"; }
inline bool hasOfflineOpponents(const std::string& mode)
{
    // Ghost and egg hunt remain solo. CTF uses FluxaraCTFAI, which is an
    // offline controller shared by the local campaign and deep links.
    return mode!="ghost_geometry" && mode!="egg_hunt";
}
// Fluxara races always start against this exact number of offline rivals.
constexpr int opponentsPerRace = 6;
inline bool supportedOffline(const std::string& mode)
{
    return nativeMode(mode)!=RaceManager::MINOR_MODE_NONE;
}
}
#endif
