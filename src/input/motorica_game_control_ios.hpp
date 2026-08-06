//  SuperTuxKart - a fun racing game with go-kart

#ifndef HEADER_MOTORICA_GAME_CONTROL_IOS_HPP
#define HEADER_MOTORICA_GAME_CONTROL_IOS_HPP

#ifdef IOS_STK
void writeMotoricaGameVersionIOS();
void startMotoricaGameControlIOS();
bool enableMotoricaGameControlForFreshSnapshotIOS();
bool enableMotoricaGameControlForLaunchURLIOS(const char* url);
bool isMotoricaGameControlEnabledIOS();
void showMotoricaConnectionLostDialogIOS();
void dismissMotoricaConnectionLostDialogIOS();
void flushMotoricaConnectionRestoreUiIOS();
#endif

#endif
