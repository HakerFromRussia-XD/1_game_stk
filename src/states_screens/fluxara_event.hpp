#ifndef HEADER_FLUXARA_EVENT_HPP
#define HEADER_FLUXARA_EVENT_HPP
#include "race/race_manager.hpp"
#include <string>

struct FluxaraEvent
{
    std::string id, mode, track;
};

namespace FluxaraModes
{
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
inline const wchar_t* label(const std::string& mode)
{
    if(mode=="normal") return L"NORMAL RACE";
    if(mode=="time_trial") return L"TIME TRIAL";
    if(mode=="ghost_geometry") return L"GHOST · REPLAY REQUIRED";
    if(mode=="follow_leader") return L"FOLLOW THE LEADER";
    if(mode=="lap_trial") return L"LAP TRIAL";
    if(mode=="three_strikes") return L"THREE STRIKES";
    if(mode=="free_for_all") return L"FREE FOR ALL";
    if(mode=="soccer") return L"SOCCER";
    if(mode=="capture_the_flag") return L"CAPTURE THE FLAG";
    if(mode=="egg_hunt") return L"EGG HUNT";
    return L"UNAVAILABLE MODE";
}
inline bool laps(const std::string& mode)
{ return mode=="normal" || mode=="time_trial"; }
inline bool timed(const std::string& mode)
{ return mode=="lap_trial" || mode=="free_for_all" || mode=="soccer"; }
inline bool arena(const std::string& mode)
{ return mode=="three_strikes" || mode=="free_for_all" || mode=="capture_the_flag"; }
inline bool supportedOffline(const std::string& mode)
{ return nativeMode(mode)!=RaceManager::MINOR_MODE_NONE && mode!="ghost_geometry" && mode!="capture_the_flag"; }
}
#endif
