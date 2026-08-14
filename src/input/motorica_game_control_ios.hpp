//  SuperTuxKart - a fun racing game with go-kart

#ifndef HEADER_MOTORICA_GAME_CONTROL_IOS_HPP
#define HEADER_MOTORICA_GAME_CONTROL_IOS_HPP

#ifdef IOS_STK
enum class MotoricaLaunchModeIOS
{
    Standalone,
    MotoricaStart
};

void writeMotoricaGameVersionIOS();
void startMotoricaGameControlIOS();
bool enableMotoricaGameControlForLaunchURLIOS(const char* url);
bool isMotoricaGameControlEnabledIOS();
bool isMotoricaStandaloneModeIOS();
MotoricaLaunchModeIOS getMotoricaLaunchModeIOS();
void showMotoricaConnectionLostDialogIOS();
void dismissMotoricaConnectionLostDialogIOS();
void flushMotoricaConnectionRestoreUiIOS();
#endif

#endif
