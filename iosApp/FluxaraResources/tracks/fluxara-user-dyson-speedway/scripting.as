/*
* Author: RX1
* Version: 1.000
* License: CC-BY-SA 4.0 (see ./License.txt)
*/

// constants
int eeNumberOfEasy = 19;
int eeNumberOfMed = 16;
int eeNumberOfHard = 20;
int eeNumberOfHardInSpace = 13;

int eeScoreEasy = 250;
int eeScoreMed = 500;
int eeScoreHard = 1000;

int eeBonusEasy = 300;
int eeBonusMed = 600;
int eeBonusHard = 1200;
int completionMult = 25;

int eeTimeBonusPerSec = 20;
int eeTimeBonusLimitEasy = 10 * 60;
int eeTimeBonusLimitMed = 20 * 60;
int eeTimeBonusLimitHard = 60 * 60;

int maxVortexJumps = 4;
double teleTargetVisDuration = 0.75;
bool displayChecklines = false;


// variables (have to be reset when restarting)
int eeCountEasy = 0;
int eeCountMed = 0;
int eeCountHard = 0;
int eeCountHardInSpace = 0;
bool isFinalEasyUnlocked = false;
bool isFinalMedUnlocked = false;
bool isFinalHardUnlocked = false;
bool isFinalHardSpaceUnlocked = false;
bool areTeleportersUnlocked = false;
int eeFinalHardSpaceTriggerCounter = 0;
bool foundFriedEgg = false;

int score = 0;
int instantEggBonus = 1000;
double instantEggBonusTimeLimit = 6.0;

bool doubleRefrigeration = false;
bool doubleForceFieldSlider = false;
bool doubleDarkSide = false;
bool doubleStargazer = false;
bool isSpaceRescueComplete = false;
int vortexJumpCount = 0;
int orbitalRescues= 0;
int deepSpaceRescues= 0;

int timePassed = 0;
int timingInterval = 5;		// lower values (than default 5) mean more precise timing, but slow down the game
bool isTimedGameOver = false;
bool specialTeleAct = false;

// variables to check for running initial timers
bool isWaitingForDisplayEEStartMessage = false;
bool isWaitingForStartTimedGame = false;
bool isWaitingForInstantEggBonusOff = false;

// others
int botIdToTeleportBack;
Vec3 positionToTeleportBotBackTo;


// ----------------------------- general functions ----------------------------

// ------------------------------ Version related -----------------------------
bool isOlderV1_3(Track::TrackObject@ obj) {
	int version = Utils::versionToInt(Utils::getFLUXARA_DRIFTVersion());
	return version < 10300000;
}

bool isV1_3OrNewer(Track::TrackObject@ obj) {
	int version = Utils::versionToInt(Utils::getFLUXARA_DRIFTVersion());
	return version >= 10300000;
}
// ----------------------------------------------------------------------------


// ------------------- Race Direction and Networking related ------------------
bool isTrackForward(Track::TrackObject@ obj) {
    return !Track::isReverse();
}

bool isTrackReverse(Track::TrackObject@ obj) {
    return Track::isReverse();
}

bool isNetworking(Track::TrackObject@ obj) {
    return Utils::isNetworking();
}

bool isNetworkingAndForward(Track::TrackObject@ obj) {
    return Utils::isNetworking() && !Track::isReverse();
}
// ----------------------------------------------------------------------------


// -------------------- Movable and Networking related ------------------------
bool movableIsTrackForward(Track::TrackObject@ obj) {
    return !Track::isReverse();
}

bool movableIsTrackReverse(Track::TrackObject@ obj) {
    return Track::isReverse();
}

bool movableIsNetworkingAndForward(Track::TrackObject@ obj) {
    return Utils::isNetworking() && !Track::isReverse();
}

bool movableIsNetworkingAndReverse(Track::TrackObject@ obj) {
    return Utils::isNetworking() && Track::isReverse();
}

bool movableIsNotNetworking(Track::TrackObject@ obj) {
    return !Utils::isNetworking();
}

bool movableIsNotNetworkingAndForward(Track::TrackObject@ obj) {
    return !Utils::isNetworking() && !Track::isReverse();
}

bool movableIsNotNetworkingAndReverse(Track::TrackObject@ obj) {
    return !Utils::isNetworking() && Track::isReverse();
}
// ----------------------------------------------------------------------------


// ------------------------ CTF and Networking related ------------------------
bool isNetworkingAndForwardAndNotCTF(Track::TrackObject@ obj) {
    return Utils::isNetworking() && !Track::isReverse() && Track::getMinorRaceMode() != 2002;
}

bool isNetworkingAndReverseAndNotCTF(Track::TrackObject@ obj) {
    return Utils::isNetworking() &&  Track::isReverse() && Track::getMinorRaceMode() != 2002;
}
// ----------------------------------------------------------------------------


// -------------------------- specific functions ------------------------------

// ----------------------- Easter Egg Hunt related ----------------------------
bool isEasterEggHunt(Track::TrackObject@ obj) {
    // enum RaceManager::MINOR_MODE_EASTER_EGG is 3000
    return Track::getMinorRaceMode() == 3000;
}

bool isNotEasterEggHunt(Track::TrackObject@ obj) {
    return Track::getMinorRaceMode() != 3000;
}

bool isEasterEggOrCTF(Track::TrackObject@ obj) {
    return Track::getMinorRaceMode() == 3000 || Track::getMinorRaceMode() == 2002;
}

bool isNotEasterEggOrCTF(Track::TrackObject@ obj) {
    return Track::getMinorRaceMode() != 3000 && Track::getMinorRaceMode() != 2002;
}

bool isNotEasterEggOrCTFAndIsForward(Track::TrackObject@ obj) {
    return Track::getMinorRaceMode() != 3000 && Track::getMinorRaceMode() != 2002 && !Track::isReverse();
}

bool isNotEasterEggOrCTFAndIsReverse(Track::TrackObject@ obj) {
    return Track::getMinorRaceMode() != 3000 && Track::getMinorRaceMode() != 2002 && Track::isReverse();
}

bool isEasterEggHuntMedium(Track::TrackObject@ obj) {
	return Track::getMinorRaceMode() == 3000 && Track::getDifficulty() >= 1;
}

bool isEasterEggHuntHard(Track::TrackObject@ obj) {
	return Track::getMinorRaceMode() == 3000 && Track::getDifficulty() >= 2;
}

bool isEasterEggHuntHardOnly(Track::TrackObject@ obj) {
	return Track::getMinorRaceMode() == 3000 && Track::getDifficulty() == 2;
}

bool isForwardAndNotEasterEggHunt(Track::TrackObject@ obj) {
    return !Track::isReverse() && Track::getMinorRaceMode() != 3000;
}

bool isReverseAndNotEasterEggHunt(Track::TrackObject@ obj) {
	// should always be true
    return Track::isReverse() && Track::getMinorRaceMode() != 3000;
}

bool isReverseOrEasterEggHunt(Track::TrackObject@ obj) {
    return Track::isReverse() || Track::getMinorRaceMode() == 3000;
}

bool isReverseOrEasterEggHuntOrCTF(Track::TrackObject@ obj) {
    return Track::isReverse() || Track::getMinorRaceMode() == 3000 || Track::getMinorRaceMode() == 2002;
}
// ----------------------------------------------------------------------------


// ------------------------------- Others -------------------------------------
bool displayChecklineVis(Track::TrackObject@ obj) {
	return displayChecklines;
}

bool maybeLater(Track::TrackObject@ obj) {
	return false;
}
// ----------------------------------------------------------------------------


// ----------------------- Dyson Speedway specific ----------------------------
void onStart() {

	// is EasterEggHunt
	if (Track::getMinorRaceMode() == 3000) {
		// resets global variables
		eeCountEasy = 0;
		eeCountMed = 0;
		eeCountHard = 0;
		eeCountHardInSpace = 0;
		isFinalEasyUnlocked = false;
		isFinalMedUnlocked = false;
		isFinalHardUnlocked = false;
		isFinalHardSpaceUnlocked = false;
		areTeleportersUnlocked = false;
		eeFinalHardSpaceTriggerCounter = 0;
		foundFriedEgg = false;

		score = 0;
		instantEggBonus = 1000;

		doubleRefrigeration = false;
		doubleForceFieldSlider = false;
		doubleDarkSide = false;
		doubleStargazer = false;
		isSpaceRescueComplete = false;
		vortexJumpCount = 0;
		orbitalRescues= 0;
		deepSpaceRescues= 0;

		isTimedGameOver = true;		// to stop possible running counter

		if (!isWaitingForDisplayEEStartMessage) {
			isWaitingForDisplayEEStartMessage = true;
			Utils::setTimeout("displayEEStartMessage", 5.5);
		}
		updateEEScore();

		// activates final easter egg boxes
		Track::getTrackObject("", "EEEasyFinalBox").setEnabled(true);
		Track::getTrackObject("", "EEMedFinalBox").setEnabled(true);
		Track::getTrackObject("", "EEHardFinalBox").setEnabled(true);
		Track::getTrackObject("", "EESpecialCylinderDoor").setEnabled(true);

		// activates other lock objects
		Track::getTrackObject("", "CannonEETopLockInvis").setEnabled(true);
		Track::getTrackObject("", "CannonEETopLockInvis.001").setEnabled(true);
		Track::getTrackObject("", "NuclearBlastDisabled").setEnabled(true);
		Track::getTrackObject("", "DeepSpaceLaunchLock").setEnabled(true);

		// disables higher skill level egg triggers if easy or medium mode
		if (Track::getDifficulty() < 2)
			eeSetAllHardTriggers(false);
		if (Track::getDifficulty() < 1)
			eeSetAllMedTriggers(false);

		// starts time counter
		// start is delayed for "2 * timingInterval" number of seconds to wait for a possible running time counter to stop
		if (!isWaitingForStartTimedGame) {
			isWaitingForStartTimedGame = true;
			Utils::setTimeout("startTimedGame", 2 * timingInterval);
		}

		// disables final space egg bonus and message trigger
		Track::setTriggerReenableTimeout("EETriggerFinalSpace", "", 1000000);
		// disabled until DeepSpaceLaunchUnlockTrigger1 was activated
		Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger2", "", 1000000);
		// disables race mode long run teleporters
		Track::setTriggerReenableTimeout("SpecialTeleRaceAct", "", 1000000);
	}

	// is not EasterEggHunt
	else {
		// disables all easter egg triggers
		eeSetAllTriggers(false);

		Track::setTriggerReenableTimeout("SpecialTeleRaceAct", "", 300);

		disableNuclearBlastDisabledTele();
	}

	disableTeleporters();
	specialTeleAct = false;

	// initial state for the RemoveTopGateTeleportTempResetTriggers
	Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerF", "", 1000000);
	Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerR", "", 1000000);

	// disables top gate fall rescue teleport trigger in easter egg hunt and CTF mode
	if (Track::getMinorRaceMode() == 3000 || Track::getMinorRaceMode() == 2002)
		Track::setTriggerReenableTimeout("GateSection1FallGuideReset", "", 1000000);

	// disables rescue bubble sound emitter triggers, if not race forward
	if (Track::isReverse()) {
		for (int i = 1; i <= 4; i++) {		// there are 4 rescue bubble sound triggers
			Track::setTriggerReenableTimeout("RescueBubbleTrigger" + i, "", 1000000);
		}
	}
}


// --------------------- section 2 sphere collisions --------------------------
/* requires an objects on colission function call -
so it can't be used in combination with texture based effects, which work with "object" type none only
void onBlueSphereKartCollision(int idKart, const string library_instance_id, const string obj_id) {
	Track::getTrackObject("", "blue_sphere_shock_emitter").getSoundEmitter().playOnce();
}*/

void onGreenSphereKartCollision(int idKart, const string library_instance_id, const string obj_id) {
	Track::getTrackObject("", "green_sphere_bounce_emitter").getSoundEmitter().playOnce();
}

void orangeSphereBeamIn(int idKart) {
	Kart::teleportExact(idKart, Track::getTrackObject("", "OrangeSphere").getCenterPosition());
}
// ----------------------------------------------------------------------------


// --------------------- other sound emitter functions ------------------------

void rescueBubbleNoise(int idKart) {
    Track::getTrackObject("", "RescueBubbleEmitter").getSoundEmitter().playOnce();
}
// ----------------------------------------------------------------------------


// ----------------------- teleport reset functions ---------------------------
void topGateFallTeleport(int idKart) {
	Vec3 position;
	if (!Track::isReverse()) {
		Track::getTrackObject("", "topGateTeleportTargetF_TempReset").setEnabled(true);
		position = Track::getTrackObject("", "topGateTeleportTargetF").getCenterPosition();
		Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerF", "", 0.8);
	}
	else {
		Track::getTrackObject("", "topGateTeleportTargetR_TempReset").setEnabled(true);
		position = Track::getTrackObject("", "topGateTeleportTargetR").getCenterPosition();
		Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerR", "", 0.8);
	}
	Kart::teleportExact(idKart, position);
	Audio::playSound("bzzt");

	// enables special teleporter easter eggs for networking racing modes
	if (!specialTeleAct && Utils::isNetworking()) {
		specialTele1();
		GUI::displayMessage("WARNING: Fusion Core leak detected.", 2);
	}
}

void removeTopGateTeleportTempReset(int idKart) {
	if (!Track::isReverse()) {
		Track::getTrackObject("", "topGateTeleportTargetF_TempReset").setEnabled(false);
		Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerF", "", 1000000);
	}
	else {
		Track::getTrackObject("", "topGateTeleportTargetR_TempReset").setEnabled(false);
		Track::setTriggerReenableTimeout("RemoveTopGateTeleportTempResetTriggerR", "", 1000000);
	}
}
// ----------------------------------------------------------------------------


// ----------------------- Easter Egg Hunt related ----------------------------
void startTimedGame() {
	isTimedGameOver = false;
	timePassed = 2 * timingInterval;
	Utils::setTimeout("timeCounter", timingInterval);
	isWaitingForStartTimedGame = false;
}

void timeCounter() {
	timePassed += timingInterval;
	if (!isTimedGameOver)
		Utils::setTimeout("timeCounter", timingInterval);
}

void instantEggBonusOff() {
	instantEggBonus = 0;
	isWaitingForInstantEggBonusOff = false;
}

void displayEEStartMessage() {
	if (Track::getDifficulty() >= 2) {
		GUI::displayOverlayMessage("Collect " + (eeNumberOfEasy + eeNumberOfMed + eeNumberOfHard - eeNumberOfHardInSpace) + " easter eggs inside the dyson sphere\nand find a way outside\nto rescue " + eeNumberOfHardInSpace + " eggs that were lost in space\nand unlock all final eggs.");
	}
	else if (Track::getDifficulty() == 1) {
		GUI::displayOverlayMessage("Collect " + (eeNumberOfEasy + eeNumberOfMed) + " easter eggs inside the dyson sphere\nto unlock the final easy and medium eggs.");
	}
	else if (Track::getDifficulty() <= 0) {
		GUI::displayOverlayMessage("Collect " + eeNumberOfEasy + " easter eggs along the race track\nto unlock the final easy egg.");
	}

	if (!isWaitingForInstantEggBonusOff) {
		isWaitingForInstantEggBonusOff = true;
		Utils::setTimeout("instantEggBonusOff", instantEggBonusTimeLimit);
	}
	isWaitingForDisplayEEStartMessage = false;

	// FLUXARA_DRIFT v.1.2: Not working; specify trigger in Blender instead (Type: action trigger - FluxaraDrift Object Properties)
	//Vec3 triggerLocation = Track::getTrackObject("", "CannonEETopLockInvis").getCenterPosition();
	//Vec3 triggerLocation = Track::getTrackObject("", "CannonEETopLockInvis").getOrigin();
	//float distance = 3.00f;
	//GUI::displayMessage(triggerLocation.getX() + ", " + triggerLocation.getY() + ", " + triggerLocation.getZ(), 1);
	//Track::createTrigger("testTrigger", triggerLocation, distance);		// crashes games
}

void messageResetWarning() {
	GUI::displayMessage("WARNING", 2);
	GUI::displayMessage("Reset function will teleport your kart back to start.", 2);
	GUI::displayMessage("To retain local reset positions follow the race track and don't use the transport lines.", 2);
}

void eeFinalEasyUnlockMsg(int idKart) {
	int numOfEggs = eeNumberOfEasy - eeCountEasy;
	string eggs = eggsOrEgg(numOfEggs);
	GUI::displayOverlayMessage("You need " + numOfEggs + " more easy " + eggs + "\nto unlock the final easy egg.");
}

void eeFinalMedUnlockMsg(int idKart) {
	int numOfEggs = eeNumberOfMed - eeCountMed;
	string eggs = eggsOrEgg(numOfEggs);
	if (numOfEggs > 0)
		GUI::displayOverlayMessage("You need " + numOfEggs + " more medium " + eggs + "\nto unlock the final medium egg.");
	else
		GUI::displayOverlayMessage("To unlock the final medium egg\nyou first have to get the final easy egg.");
}

void eeFinalHardUnlockMsg(int idKart) {
	int numOfEggs = eeNumberOfHard - eeCountHard;
	string eggs = eggsOrEgg(numOfEggs);
	if (numOfEggs > 0)
		GUI::displayOverlayMessage("You need " + numOfEggs + " more hard " + eggs + "\nto unlock the final hard egg.");
	else
		GUI::displayOverlayMessage("To unlock the final hard egg\nyou first have to get the final easy and medium eggs.");
}

void eeFinalHardSpaceUnlockMsg(int idKart) {
	if (!isFinalHardSpaceUnlocked)
		GUI::displayOverlayMessage("You have to get the final hard egg first" + "\nto unlock the final space egg.");
	else {
		Track::setTriggerReenableTimeout("EETriggeFinalHardSpaceUnlockMsg", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggerFinalSpace", "", 1);
	}
}

string eggsOrEgg(int eggsLeft) {
	if (eggsLeft > 1)
		return "eggs";
	else
		return "egg";
}

void updateEEScore() {
	string customEECount = "Easy: " + eeCountEasy + "/" + eeNumberOfEasy + "     ";
	if (Track::getDifficulty() > 0)
		customEECount = customEECount + "Med.: " + eeCountMed + "/" + eeNumberOfMed + "     ";
	else
		customEECount = customEECount + "Med.: -/-     ";
	if (Track::getDifficulty() > 1)
		customEECount = customEECount + "Hard: " + eeCountHard + "/" + eeNumberOfHard;
	else
		customEECount = customEECount + "Hard: -/-";

	GUI::discardStaticMessage();
	GUI::displayStaticMessage("Score: " + score + "                    " + customEECount, 1);
}

void addEEBonus(int bonus, string bonusText) {
	score += bonus;
	GUI::displayOverlayMessage(bonusText + "     " + bonus);
	updateEEScore();
}

void EETriggerEasyDefault() {
	score += eeScoreEasy;
    Audio::playSound("grab_collectable");

	if (eeCountEasy % 6 == 0)
		GUI::displayOverlayMessage("Easy egg collected.");
	else if (eeCountEasy % 6 == 1)
		GUI::displayOverlayMessage("Easy egg collected. Got it!");
	else if (eeCountEasy % 6 == 2)
		GUI::displayOverlayMessage("Easy egg collected.");
	else if (eeCountEasy % 6 == 3)
		GUI::displayOverlayMessage("Easy egg collected. Next!");
	else if (eeCountEasy % 6 == 4)
		GUI::displayOverlayMessage("Easy egg collected. Keep going!");
	else
		GUI::displayOverlayMessage("Easy egg collected.");

	eeCountEasy++;
	updateEEScore();

	if (eeCountEasy == eeNumberOfEasy) {
		float unlockDelay = 5.0;
		Utils::setTimeout("eeFinalEasyUnlock", unlockDelay);

		if (!isFinalMedUnlocked && eeCountMed >= eeNumberOfMed) {
			unlockDelay += 5.0;
			Utils::setTimeout("eeFinalMedUnlock", unlockDelay);
		}
		if (!isFinalHardUnlocked && eeCountHard >= eeNumberOfHard) {
			unlockDelay += 5.0;
			Utils::setTimeout("eeFinalHardUnlock", unlockDelay);
		}
	}
}

void EETriggerMedDefault() {
	score += eeScoreMed;
    Audio::playSound("grab_collectable");

	if (eeCountMed % 6 == 0)
		GUI::displayOverlayMessage("Medium egg collected. Well done!");
	else if (eeCountMed % 6 == 1)
		GUI::displayOverlayMessage("Medium egg collected. Nice!");
	else if (eeCountMed % 6 == 2)
		GUI::displayOverlayMessage("Medium egg collected. Thumbs up!");
	else if (eeCountMed % 6 == 3)
		GUI::displayOverlayMessage("Medium egg collected. Sweet!");
	else if (eeCountMed % 6 == 4)
		GUI::displayOverlayMessage("Medium egg collected. YES!");
	else
		GUI::displayOverlayMessage("Medium egg collected. Good job!");

	eeCountMed++;
	updateEEScore();

	if (eeCountMed == eeNumberOfMed) {
		Utils::setTimeout("eeFinalMedUnlockCongrats", 5.0);

		if (isFinalEasyUnlocked) {
			Utils::setTimeout("eeFinalMedUnlock", 5.05);

			if (!isFinalHardUnlocked && eeCountHard >= eeNumberOfHard)
				Utils::setTimeout("eeFinalHardUnlock", 10.0);
		}
	}
}

void EETriggerHardDefault() {
	score += eeScoreHard;
    Audio::playSound("grab_collectable");

	if (eeCountHard % 7 == 0)
		GUI::displayOverlayMessage("Hard egg collected! AWESOME!!!");
	else if (eeCountHard % 7 == 1)
		GUI::displayOverlayMessage("Hard egg collected! FANTASTIC!");
	else if (eeCountHard % 7 == 2)
		GUI::displayOverlayMessage("Hard egg collected! SUPERB!!");
	else if (eeCountHard % 7 == 3)
		GUI::displayOverlayMessage("Hard egg collected! SPLENDID!!!");
	else if (eeCountHard % 7 == 4)
		GUI::displayOverlayMessage("Hard egg collected! MAGNIFICANT!");
	else if (eeCountHard % 7 == 5)
		GUI::displayOverlayMessage("Hard egg collected! HOLY ****!");
	else
		GUI::displayOverlayMessage("Hard egg collected! TERRIFIC!!");

	eeCountHard++;
	updateEEScore();

	if (eeCountHardInSpace == eeNumberOfHardInSpace && !isSpaceRescueComplete) {
		isSpaceRescueComplete = true;
		Utils::setTimeout("completeSpaceRescue", 3.0);
	}

	if (eeCountHard - eeCountHardInSpace == eeNumberOfHard - eeNumberOfHardInSpace && !areTeleportersUnlocked) {
		areTeleportersUnlocked = true;
		Utils::setTimeout("enableTeleporters", 3.0);
	}

	if (eeCountHard == eeNumberOfHard) {
		Utils::setTimeout("eeFinalHardUnlockCongrats", 8.0);

		if (isFinalEasyUnlocked && isFinalMedUnlocked)
			Utils::setTimeout("eeFinalHardUnlock", 8.05);
	}
}

void eeFinalEasyUnlock() {
	GUI::displayOverlayMessage("GREAT! All easy eggs collected!\nFinal easy egg unlocked.");
	Track::getTrackObject("", "EEEasyFinalBox").setEnabled(false);
	Track::setTriggerReenableTimeout("EETriggeFinalEasyUnlockMsg", "", 1000000);
	isFinalEasyUnlocked = true;
	Audio::playSound("goal_scored");
}

void eeFinalMedUnlock() {
	GUI::displayOverlayMessage("Final medium egg unlocked.");
	Track::getTrackObject("", "EEMedFinalBox").setEnabled(false);
	Track::setTriggerReenableTimeout("EETriggeFinalMedUnlockMsg", "", 1000000);
	isFinalMedUnlocked = true;
}

/* separate in case final easy egg has to not been unlocked */
void eeFinalMedUnlockCongrats() {
	GUI::displayOverlayMessage("AMAZING!!! You collected every medium egg!");
	Audio::playSound("goal_scored");
}

void eeFinalHardUnlock() {
	GUI::displayOverlayMessage("Final hard egg unlocked.");
	Track::getTrackObject("", "EEHardFinalBox").setEnabled(false);
	Track::setTriggerReenableTimeout("EETriggeFinalHardUnlockMsg", "", 1000000);
	isFinalHardUnlocked = true;
}

/* separate in case final easy and / or medium egg has to not been unlocked */
void eeFinalHardUnlockCongrats() {
	GUI::displayOverlayMessage("You collected all of the hard eggs!\nYou are a true Egg Hunt Super Hero!!!");
	Audio::playSound("goal_scored");
}

void completeSpaceRescue() {
	GUI::displayOverlayMessage("Thank you for rescuing all eggs from outer space!");
	addEEBonus(eeBonusHard * 10, "Lost in Space Bonus");
	Audio::playSound("goal_scored");
}

void eeFinalHardSpaceUnlock() {
	Track::getTrackObject("", "EESpecialCylinderDoor").setEnabled(false);
	isFinalHardSpaceUnlocked = true;
	GUI::displayOverlayMessage("Now get the final Space Egg to complete your run!");
}

void eeTriggerHardSec2Oribit(int idKart) {
	Utils::setTimeout("eeTriggerHardSec2OribitP1", 4.0);
	Track::getTrackObject("", "CannonSphereEmitter").getSoundEmitter().playOnce();
}

void eeTriggerHardSec2OribitP1() {
	GUI::displayOverlayMessage("Cargo Export Line - Top Gate Orbit.\n");
	GUI::displayOverlayMessage("Passenger detected - Invisible Air Shield installed.\n");
	Utils::setTimeout("eeTriggerHardSec2OribitP2", 4.0);
}

void eeTriggerHardSec2OribitP2() {
	Track::getTrackObject("", "CannonEETopLockInvis").setEnabled(false);
	Track::getTrackObject("", "CannonEETopLockInvis.001").setEnabled(false);
	Track::getTrackObject("", "CannonEETopRamp").setEnabled(true);
	Track::getTrackObject("", "CannonEETopRamp.001").setEnabled(true);
	GUI::displayOverlayMessage("Top Gate Express Export Lines unlocked.");
}

void cannonEEBottomTriggerGreen(int idKart) {
 	GUI::displayOverlayMessage("Transport Line to\nSection 2 - Cargo Bay.\n");
	messageResetWarning();
}

void cannonEEBottomTriggerBlue(int idKart) {
 	GUI::displayOverlayMessage("Transport Line to\nSection 2 - Warpcore Cooling Lane.\n");
	messageResetWarning();
}

void cannonEEBottomTriggerRed(int idKart) {
 	GUI::displayOverlayMessage("Transport Line to\nSection 1 - Top Gate.\n");
	messageResetWarning();
}

void cannonEEBottomTriggerYellow(int idKart) {
 	GUI::displayOverlayMessage("Transport Line to\nSection 3 - Central Fusion Core.\n");
	messageResetWarning();
}

void vortexJumpCountTrigger(int idKart) {
	if (Track::getMinorRaceMode() == 3000) {
		vortexJumpCount++;
		string vortexLaunchText = "Vortex Flight Launch " + vortexJumpCount + "/" + maxVortexJumps;

		if (vortexJumpCount == maxVortexJumps) {
			Track::getTrackObject("", "EEVortexRampsP1").setEnabled(true);
			Track::getTrackObject("", "EEVortexRampsP2").setEnabled(true);
			Track::getTrackObject("", "EEVortexRampsP3").setEnabled(true);
			Track::setTriggerReenableTimeout("VortexJumpCountTrigger", "", 1000000);
			GUI::displayMessage(vortexLaunchText);
			GUI::displayOverlayMessage("Vortex Ramps activated");
		}
		else if (vortexJumpCount < maxVortexJumps)
			GUI::displayMessage(vortexLaunchText);
	}
}

// enables / disables easter egg hunt triggers
/*
* FLUXARA_DRIFT v1.2: Because Track::enableTrigger(triggerId) Track::disableTrigger(triggerId) doesn't work,
* triggers can ONLY be DISABLED explictly by setTriggerReenableTimeout.
* All triggers are enabled by default and those not needed must be explicitly disabled.
*/
void eeSetAllTriggers(bool enabled) {
	eeSetAllEasyTriggers(enabled);
	eeSetAllMedTriggers(enabled);
	eeSetAllHardTriggers(enabled);

	// other easter egg hunt triggers
	if (!enabled) {
		Track::setTriggerReenableTimeout("EETriggerFinalEasy", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggerFinalMed", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggerFinalHard", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggeFinalEasyUnlockMsg", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggeFinalMedUnlockMsg", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggeFinalHardUnlockMsg", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggeFinalHardSpaceUnlockMsg", "", 1000000);
		Track::setTriggerReenableTimeout("EETriggerFinalSpace", "", 1000000);

		Track::setTriggerReenableTimeout("CannonEEBottomTriggerGreen", "", 1000000);
		Track::setTriggerReenableTimeout("CannonEEBottomTriggerBlue", "", 1000000);
		Track::setTriggerReenableTimeout("CannonEEBottomTriggerRed", "", 1000000);
		Track::setTriggerReenableTimeout("CannonEEBottomTriggerYellow", "", 1000000);

		Track::setTriggerReenableTimeout("eeTriggerHardSec2Oribit", "", 1000000);
		Track::setTriggerReenableTimeout("VortexJumpCountTrigger", "", 1000000);
		Track::setTriggerReenableTimeout("EnableNuclearBlastTrigger", "", 1000000);
		Track::setTriggerReenableTimeout("DeepSpaceLaunchLockedMsgTrigger", "", 1000000);
		Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger1", "", 1000000);
		Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger2", "", 1000000);
		Track::setTriggerReenableTimeout("FriedBananaHelpTrigger", "", 1000000);
	}
}

void eeSetAllEasyTriggers(bool enabled) {
	eeSetAllXTriggers(enabled, "EETriggerEasy.0", eeNumberOfEasy);
}

void eeSetAllMedTriggers(bool enabled) {
	eeSetAllXTriggers(enabled, "EETriggerMed.0", eeNumberOfMed + 1);		// + 1 because EEMedNew11 was removed
}

void eeSetAllHardTriggers(bool enabled) {
	eeSetAllXTriggers(enabled, "EETriggerHard.0", eeNumberOfHard - eeNumberOfHardInSpace);
	eeSetAllXTriggers(enabled, "EETriggerHardSpace.0", eeNumberOfHardInSpace + 1);		// + 1 because EEHardSpaceNew02 was removed
}

void eeSetAllXTriggers(bool enabled, string triggerIdPrefix, int numberOfEEs) {
	string triggerId;
	for (int i = 1; i <= numberOfEEs; i++) {
		if (i < 10)
			triggerId = triggerIdPrefix + "0" + i;
		else
			triggerId = triggerIdPrefix + i;

		/* FLUXARA_DRIFT v1.2: doesn't work:
		if (enabled)
			Track::enableTrigger(triggerId);
		else
			Track::disableTrigger(triggerId);
		*/

		// workaround (FLUXARA_DRIFT v1.2):
		if (!enabled)
			Track::setTriggerReenableTimeout(triggerId, "", 1000000);
	}
}

void deepSpaceLaunchLockedMsg(int idKart) {
	GUI::displayOverlayMessage("Deep Space Launch access denied!\nFind the right entry to this ramp.");
}

void unlockDeepSpaceLaunch1(int idKart) {
	Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger2", "", 2);
	Utils::setTimeout("unlockDeepSpaceLaunch1TimedOut", 11.0);
}

void unlockDeepSpaceLaunch1TimedOut() {
	Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger2", "", 1000000);
}

void unlockDeepSpaceLaunch2(int idKart) {
	Track::getTrackObject("", "DeepSpaceLaunchLock").setEnabled(false);
	Track::setTriggerReenableTimeout("DeepSpaceLaunchUnlockTrigger1", "", 1000000);
	Track::setTriggerReenableTimeout("DeepSpaceLaunchLockedMsgTrigger", "", 1000000);
	GUI::displayOverlayMessage("Deep Space Launch access granted!");
}

// teleporters
void teleport1(int idKart) {
	teleport(idKart, 1);
}

void teleport2(int idKart) {
	teleport(idKart, 2);
}

void teleport3(int idKart) {
	teleport(idKart, 3);
}

void teleport4(int idKart) {
	teleport(idKart, 4);
}

void teleport5(int idKart) {
	teleport(idKart, 5);
}

void teleport6(int idKart) {
	teleport(idKart, 6);
}

void teleport(int idKart, int teleporterNumber) {
	Vec3 position = Track::getTrackObject("", "Teleport" + teleporterNumber + "Target").getCenterPosition();
	Track::getTrackObject("", "Teleport" + teleporterNumber + "TargetVis").setEnabled(true);
	Utils::setTimeout("removeTeleport" + teleporterNumber + "TargetVis", teleTargetVisDuration);
    Track::getTrackObject("", "Teleport" + teleporterNumber + "StartSnd").getSoundEmitter().playOnce();
	Kart::teleportExact(idKart, position);
    Track::getTrackObject("", "Teleport" + teleporterNumber + "TargetSnd").getSoundEmitter().playOnce();
	Track::setTriggerReenableTimeout("Teleport" + teleporterNumber + "Trigger", "", 3);

	// teleport back if bot (0 = player (local), 2 = bot)
	if (Track::getKartType(idKart) == 2) {
		botIdToTeleportBack = idKart;
		positionToTeleportBotBackTo = Track::getTrackObject("", "Teleport" + teleporterNumber + "Start").getCenterPosition();
		Utils::setTimeout("teleportBack", 1.5);
	}
}

void removeTeleport1TargetVis() {
	Track::getTrackObject("", "Teleport1TargetVis").setEnabled(false);
}

void removeTeleport2TargetVis() {
	Track::getTrackObject("", "Teleport2TargetVis").setEnabled(false);
}

void removeTeleport3TargetVis() {
	Track::getTrackObject("", "Teleport3TargetVis").setEnabled(false);
}

void removeTeleport4TargetVis() {
	Track::getTrackObject("", "Teleport4TargetVis").setEnabled(false);
}

void removeTeleport5TargetVis() {
	Track::getTrackObject("", "Teleport5TargetVis").setEnabled(false);
}

void removeTeleport6TargetVis() {
	Track::getTrackObject("", "Teleport6TargetVis").setEnabled(false);
}

void teleportBack() {
	Kart::teleportExact(botIdToTeleportBack, positionToTeleportBotBackTo);
}

void enableTeleporters() {
	setTeleporters(true);
	GUI::displayOverlayMessage("All hard eggs inside the sphere collected!\nTeleporters activated.");
}

void disableTeleporters() {
	setTeleporters(false);
}

/* enables / disables teleport triggers and start / target objects */
void setTeleporters(bool enable) {
	int numberOfTeleporters = 6;
	int timeout = 3;

	if (enable)
		timeout = 3;
	else
		timeout = 1000000;

	for (int i = 1; i <= numberOfTeleporters; i++) {
		setTeleporter(i, timeout, enable);
	}
}

void setTeleporter(int teleporterNumber, int timeout, bool enable) {
	Track::setTriggerReenableTimeout("Teleport" + teleporterNumber + "Trigger", "", timeout);
	Track::getTrackObject("", "Teleport" + teleporterNumber + "Start").setEnabled(enable);
	Track::getTrackObject("", "Teleport" + teleporterNumber + "Target").setEnabled(enable);
}

/* also triggers initial special long run teleporter activation */
void specialTele1() {
	// already activated
	if (specialTeleAct)
		return;

	// initial special tele activation
	else {
		specialTeleAct = true;
		Track::getTrackObject("", "EEEasyNew10").setEnabled(true);
		Track::setTriggerReenableTimeout("SpecialTeleRaceAct", "", 1000000);
	}
}

void specialTele2() {
	Track::getTrackObject("", "EEEasyNew02").setEnabled(true);
}

void specialTele3() {
	Track::getTrackObject("", "EEEasyNew17").setEnabled(true);
}

void specialTele4() {
	Track::getTrackObject("", "EEEasyNew18").setEnabled(true);
}

void specialTele5() {
	Track::getTrackObject("", "EEMedNew06").setEnabled(true);
	Track::setTriggerReenableTimeout("EETriggerMed.006", "", 1);
}

void specialTele6() {
	Track::getTrackObject("", "EEHardNew03").setEnabled(true);
}

void specialTeleRaceActivate(int idKart) {
	specialTele1();
	Track::setTriggerReenableTimeout("SpecialTeleRaceAct", "", 1000000);
}

void nuclearBlastDisabledTeleVis(int idKart) {
	Track::getTrackObject("", "NuclearBlastDisabledTeleVis").setEnabled(true);
	Utils::setTimeout("removeNuclearBlastDisabledTeleVis", 2);
}

void removeNuclearBlastDisabledTeleVis() {
	Track::getTrackObject("", "NuclearBlastDisabledTeleVis").setEnabled(false);
}

void nuclearBlastDisabledTele(int idKart) {
	Vec3 position = Track::getTrackObject("", "TeleportNucTarget").getCenterPosition();
	Track::getTrackObject("", "TeleportNucTargetVis").setEnabled(true);
    Track::getTrackObject("", "TeleportNucStartSnd").getSoundEmitter().playOnce();
	Kart::teleportExact(idKart, position);
    Track::getTrackObject("", "TeleportNucTargetSnd").getSoundEmitter().playOnce();
	Utils::setTimeout("removeTeleportNucTargetVis", teleTargetVisDuration);
	GUI::displayOverlayMessage("Nuclear Blast access denied!\nFind the right entry to enable the ramp.");
}

void removeTeleportNucTargetVis() {
	Track::getTrackObject("", "TeleportNucTargetVis").setEnabled(false);
}

void enableNuclearBlast(int idKart) {
	Track::getTrackObject("", "NuclearBlastRamp").setEnabled(true);
	Track::getTrackObject("", "NuclearBlastDisabled").setEnabled(false);
	disableNuclearBlastDisabledTele();
	GUI::displayOverlayMessage("Nuclear Blast Ramp enabled.");
}

void disableNuclearBlastDisabledTele() {
	int numOfTriggers = 10;
	for (int i = 0; i < numOfTriggers; i++) {
		Track::setTriggerReenableTimeout("NuclearBlastDisabledTrigger.00" + i, "", 1000000);
	}
	numOfTriggers = 3;
	for (int i = 0; i < numOfTriggers; i++) {
		Track::setTriggerReenableTimeout("NuclearBlastDisabledVisTrigger.00" + i, "", 1000000);
	}
}


// specific easter egg trigger
// easy eggs
void eeTriggerEasy01(int idKart) {
	Track::getTrackObject("", "EEEasyNew01").setEnabled(false);
	if (instantEggBonus <= 0) {
		EETriggerEasyDefault();
	}
	else {
		GUI::clearOverlayMessages();
		EETriggerEasyDefault();
		addEEBonus(instantEggBonus, "Instant Egg Bonus");
	}
}

void eeTriggerEasy02(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEEasyNew02").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(1, 3, true);
		GUI::displayOverlayMessage("\nGet launched into orbit!\n");
		specialTele3();
	}
	else {
		EETriggerEasyDefault();
	}
}

void eeTriggerEasy03(int idKart) {
  	Track::getTrackObject("", "EEEasyNew03").setEnabled(false);
	EETriggerEasyDefault();
	addEEBonus(eeBonusEasy * 2, "Over The Edge Bonus");
}

void eeTriggerEasy04(int idKart) {
  	Track::getTrackObject("", "EEEasyNew04").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy05(int idKart) {
  	Track::getTrackObject("", "EEEasyNew05").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy06(int idKart) {
  	Track::getTrackObject("", "EEEasyNew06").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy07(int idKart) {
  	Track::getTrackObject("", "EEEasyNew07").setEnabled(false);
	EETriggerEasyDefault();
	refrigerationBonus();
}

void eeTriggerEasy08(int idKart) {
  	Track::getTrackObject("", "EEEasyNew08").setEnabled(false);
	EETriggerEasyDefault();
	refrigerationBonus();
}

void eeTriggerEasy09(int idKart) {
  	Track::getTrackObject("", "EEEasyNew09").setEnabled(false);
	EETriggerEasyDefault();
	addEEBonus(eeBonusEasy, "Electro Shock Bonus");
}

void eeTriggerEasy10(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEEasyNew10").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(6, 3, true);
		GUI::displayOverlayMessage("\nBEAM ME UP!!!\n");
		specialTele2();
	}
	else {
		EETriggerEasyDefault();
		forceFieldSliderBonus();
	}
}

void eeTriggerEasy11(int idKart) {
  	Track::getTrackObject("", "EEEasyNew11").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy12(int idKart) {
  	Track::getTrackObject("", "EEEasyNew12").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy13(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEEasyNew13").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy14(int idKart) {
  	Track::getTrackObject("", "EEEasyNew14").setEnabled(false);
	EETriggerEasyDefault();
}

void eeTriggerEasy15(int idKart) {
  	Track::getTrackObject("", "EEEasyNew15").setEnabled(false);
	EETriggerEasyDefault();
	addEEBonus(eeBonusEasy * 3, "Hypertube Bonus");
}

void eeTriggerEasy16(int idKart) {
  	Track::getTrackObject("", "EEEasyNew16").setEnabled(false);
	EETriggerEasyDefault();
	addEEBonus(eeBonusEasy * 3, "Hypertube Bonus");
}

void eeTriggerEasy17(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEEasyNew17").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(4, 3, true);
		GUI::displayOverlayMessage("\nI always wanted you to go into space, man!\n");
		specialTele4();
	}
	else {
		EETriggerEasyDefault();
		forceFieldSliderBonus();
	}
}

void eeTriggerEasy18(int idKart, const string library_instance_id, const string obj_id) {
	Track::getTrackObject("", "EEEasyNew18").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(3, 3, true);
		GUI::displayOverlayMessage("\nWanna explore the outer space?\n");
		specialTele5();
	}
	else {
		EETriggerEasyDefault();
		if (!doubleStargazer) {
			addEEBonus(eeBonusEasy, "Stargazer Bonus");
			doubleStargazer = true;
		} else {
			addEEBonus(eeBonusEasy * 2, "Double Stargazer Bonus");
		}
	}
}

void eeTriggerEasy19(int idKart) {
  	Track::getTrackObject("", "EEEasyNew19").setEnabled(false);
	EETriggerEasyDefault();
	addEEBonus(eeBonusEasy, "Cliffhanger Bonus");
}

void refrigerationBonus() {
	if (!doubleRefrigeration) {
		addEEBonus(eeBonusEasy, "Refrigeration Bonus");
		doubleRefrigeration = true;
	}
	else {
		addEEBonus(eeBonusEasy * 2, "Double Refrigeration Bonus");
	}
}

void forceFieldSliderBonus() {
	if (!doubleForceFieldSlider) {
		addEEBonus(eeBonusEasy, "Force Field Slider Bonus");
		doubleForceFieldSlider = true;
	}
	else {
		addEEBonus(eeBonusEasy * 2, "Double Force Field Slider Bonus");
	}
}

// medium eggs
void eeTriggerMed01(int idKart) {
  	Track::getTrackObject("", "EEMedNew01").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed02(int idKart) {
  	Track::getTrackObject("", "EEMedNew02").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed03(int idKart) {
  	Track::getTrackObject("", "EEMedNew03").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed04(int idKart) {
  	Track::getTrackObject("", "EEMedNew04").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed * 2, "Balance Bonus");
}

void eeTriggerMed05(int idKart) {
  	Track::getTrackObject("", "EEMedNew05").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed06(int idKart) {
  	Track::getTrackObject("", "EEMedNew06").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(5, 3, true);
		Track::setTriggerReenableTimeout("EETriggerMed.006", "", 1000000);
		GUI::displayOverlayMessage("\nLet's go on a deep space excursion!\n");
		specialTele6();
	}
	else {
		EETriggerMedDefault();
	}
}

void eeTriggerMed07(int idKart) {
  	Track::getTrackObject("", "EEMedNew07").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed, "Cargo Bonus");
}

void eeTriggerMed08(int idKart) {
  	Track::getTrackObject("", "EEMedNew08").setEnabled(false);
	EETriggerMedDefault();
	darkSideBonus();
}

void eeTriggerMed09(int idKart) {
  	Track::getTrackObject("", "EEMedNew09").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed10(int idKart) {
  	Track::getTrackObject("", "EEMedNew10").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed * 3, "Core Blast Bonus");
}

/*void eeTriggerMed11(int idKart) {
  	Track::getTrackObject("", "EEMedNew11").setEnabled(false);
	EETriggerMedDefault();
}*/

void eeTriggerMed12(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEMedNew12").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed13(int idKart) {
  	Track::getTrackObject("", "EEMedNew13").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed, "Top Gate Bonus");
}

void eeTriggerMed14(int idKart) {
  	Track::getTrackObject("", "EEMedNew14").setEnabled(false);
	EETriggerMedDefault();
	darkSideBonus();
}

void eeTriggerMed15(int idKart) {
  	Track::getTrackObject("", "EEMedNew15").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed, "Round Trip Bonus");
}

void eeTriggerMed16(int idKart) {
  	Track::getTrackObject("", "EEMedNew16").setEnabled(false);
	EETriggerMedDefault();
}

void eeTriggerMed17(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEMedNew17").setEnabled(false);
	EETriggerMedDefault();
	addEEBonus(eeBonusMed * 2, "Fried Banana Bonus");
	foundFriedEgg = true;
	Track::setTriggerReenableTimeout("FriedBananaHelpTrigger", "", 1000000);
}

void darkSideBonus() {
	if (!doubleDarkSide) {
		addEEBonus(eeBonusMed * 2, "Dark Side Bonus");
		doubleDarkSide = true;
	}
	else {
		addEEBonus(eeBonusMed * 4, "Double Dark Side Bonus");
	}
}

void eeFriedBananaHelp(int idKart) {
	if (!foundFriedEgg && eeNumberOfMed - eeCountMed == 1) {
		Track::setTriggerReenableTimeout("FriedBananaHelpTrigger", "", 1000000);
		GUI::displayMessage("HOT HOT HOT!");
		Utils::setTimeout("sendFriedBananaHelp", 60);
	}
}

void sendFriedBananaHelp() {
	if (foundFriedEgg)
		return;

	switch (Utils::randomInt(0, 2)) {
		case 0:
			GUI::displayMessage("The last medium egg is hot!");
			break;
		case 1: default:
			GUI::displayMessage("Don't you like fried bananas?");
	}
	Utils::setTimeout("sendFriedBananaHelp", 60);
}

// hard eggs
void eeTriggerHard01(int idKart) {
  	Track::getTrackObject("", "EEHardNew01").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 3, "Spaceman Bonus");
}

void eeTriggerHard02(int idKart) {
  	Track::getTrackObject("", "EEHardNew02").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 2, "Bouncy Bonus");
}

void eeTriggerHard03(int idKart, const string library_instance_id, const string obj_id) {
  	Track::getTrackObject("", "EEHardNew03").setEnabled(false);

	if (specialTeleAct) {
		Audio::playSound("grab_collectable");
		setTeleporter(2, 3, true);
		GUI::displayOverlayMessage("\nThere must be more friendly aliens\nthan friendly humans.\n");
		Utils::setTimeout("finalSpecialMessage", 10.0);
	}
	else {
		EETriggerHardDefault();
		addEEBonus(eeBonusHard * 3, "Falling Up Bonus");
	}
}

void eeTriggerHard04(int idKart) {
  	Track::getTrackObject("", "EEHardNew04").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 2, "Nuclear Blast Bonus");
}

void eeTriggerHard05(int idKart) {
  	Track::getTrackObject("", "EEHardNew05").setEnabled(false);
	EETriggerHardDefault();
}

void eeTriggerHard06(int idKart) {
  	Track::getTrackObject("", "EEHardNew06").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard, "Core Diver Bonus");
}

void eeTriggerHard07(int idKart) {
  	Track::getTrackObject("", "EEHardNew07").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 2, "Window Cleaner Bonus");
}

// hard eggs in space
void eeTriggerHardSpace01(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew01").setEnabled(false);
	EETriggerHardDefault();
	orbitalRescueBonus();
}

/*void eeTriggerHardSpace02(int idKart) {
  	Track::getTrackObject("", "EEHardSpaceNew02").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 2, "Spacebowl Bonus");
}*/

void eeTriggerHardSpace03(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew03").setEnabled(false);
	EETriggerHardDefault();
	deepSpaceRescueBonus();
}

void eeTriggerHardSpace04(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew04").setEnabled(false);
	EETriggerHardDefault();
	deepSpaceRescueBonus();
}

void eeTriggerHardSpace05(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew05").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard, "So Close Bonus");
}

void eeTriggerHardSpace06(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew06").setEnabled(false);
	EETriggerHardDefault();
}

void eeTriggerHardSpace07(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew07").setEnabled(false);
	EETriggerHardDefault();
}

void eeTriggerHardSpace08(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew08").setEnabled(false);
	EETriggerHardDefault();
}

void eeTriggerHardSpace09(int idKart, const string library_instance_id, const string obj_id) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew09").setEnabled(false);
	EETriggerHardDefault();
	if (!doubleStargazer) {
		addEEBonus(eeBonusHard, "Stargazer Bonus");
		doubleStargazer = true;
	}
	else {
		addEEBonus(eeBonusHard * 2, "Double Stargazer Bonus");
	}
}

void eeTriggerHardSpace10(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew10").setEnabled(false);
	EETriggerHardDefault();
}

void eeTriggerHardSpace11(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew11").setEnabled(false);
	EETriggerHardDefault();
	addEEBonus(eeBonusHard * 3, "Vortex Bonus");
}

void eeTriggerHardSpace12(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew12").setEnabled(false);
	EETriggerHardDefault();
	orbitalRescueBonus();
}

void eeTriggerHardSpace13(int idKart) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew13").setEnabled(false);
	EETriggerHardDefault();
	deepSpaceRescueBonus();
}

void eeTriggerHardSpace14(int idKart, const string library_instance_id, const string obj_id) {
	eeCountHardInSpace++;
  	Track::getTrackObject("", "EEHardSpaceNew14").setEnabled(false);
	EETriggerHardDefault();
	orbitalRescueBonus();
}

void orbitalRescueBonus() {
	if (orbitalRescues == 0) {
		addEEBonus(eeBonusHard, "Orbital Rescue Bonus");
		orbitalRescues++;
	}
	else if (orbitalRescues == 1) {
		addEEBonus(eeBonusHard * 2, "Double Orbital Rescue Bonus");
		orbitalRescues++;
	}
	else {
		addEEBonus(eeBonusHard * 3, "Tripple Orbital Rescue Bonus");
		Utils::setTimeout("specialThanksTesting", 5.0);
	}
}

void deepSpaceRescueBonus() {
	if (deepSpaceRescues == 0) {
		addEEBonus(eeBonusHard * 1, "Deep Space Rescue Bonus");
		deepSpaceRescues++;
	}
	else if (deepSpaceRescues == 1) {
		GUI::clearOverlayMessages();
		addEEBonus(eeBonusHard * 2, "Double Deep Space Rescue Bonus");
		deepSpaceRescues++;
	}
	else {
		GUI::clearOverlayMessages();
		addEEBonus(eeBonusHard * 5, "Complete Deep Space Rescue Bonus");
		Utils::setTimeout("specialThanksDedicated", 5.0);
	}
}

/* appears in race, not in easter egg mode */
void finalSpecialMessage() {
	GUI::displayMessage("All teleporters activated!\nWanna find more easter eggs? Play Egg Hunt mode.\nÔ\\,--,/Ô");
}

// final eggs
void eeFinalEasy(int idKart) {
	addEEBonus(eeBonusEasy * completionMult, "Easy Egg Hunt Completion Bonus");
	if (Track::getDifficulty() <= 0) {
		isTimedGameOver = true;
		displayFinalScore(eeBonusEasy * completionMult, eeTimeBonusLimitEasy, "Easy");
	}
}

void eeFinalMed(int idKart) {
	addEEBonus(eeBonusMed * completionMult, "Medium Egg Hunt Completion Bonus");
	if (Track::getDifficulty() == 1) {
		isTimedGameOver = true;
		displayFinalScore(eeBonusMed * completionMult, eeTimeBonusLimitMed, "Med.");
	}
}

void eeFinalHard(int idKart) {
	addEEBonus(eeBonusHard * completionMult, "Hard Egg Hunt Completion Bonus");
	isTimedGameOver = true;
	displayFinalScore(eeBonusHard * completionMult, eeTimeBonusLimitHard, "Hard");

	Utils::setTimeout("eeFinalHardSpaceUnlock", 4.0);
}

void eeFinalHardSpace(int idKart) {
	if (eeFinalHardSpaceTriggerCounter == 0) {
		addEEBonus(eeBonusHard * 9, "Found Final Space Egg\nExtra Bonus");
		Track::setTriggerReenableTimeout("EETriggerFinalSpace", "", 180);
	}
	else if (eeFinalHardSpaceTriggerCounter >= 1 && eeFinalHardSpaceTriggerCounter <= 3) {
		GUI::displayMessage("Special thanks to Ling, Bo.");
	}
	else if (eeFinalHardSpaceTriggerCounter >= 4 && eeFinalHardSpaceTriggerCounter <= 6) {
		GUI::displayMessage("Why don't you shoot yourself?");
	}
	else {
		GUI::displayMessage("Special thanks to Bo Ling.");
	}

	eeFinalHardSpaceTriggerCounter++;
}

int determineTimeBonus(int bonusTimeLimit) {
	int timeResult = bonusTimeLimit - timePassed;
	if (timeResult > 0)
		return eeTimeBonusPerSec * timeResult;
	else
		return 0;
}

void displayFinalScore(int completionBonus, int timeBonusLimit, string difficulty) {
	Audio::playSound("goal_scored");
	int timeBonus = determineTimeBonus(timeBonusLimit);
	int min = timeBonusLimit / 60;
	int oldScore = score - completionBonus;
	score += timeBonus;
	updateEEScore();
	string extraMsg = "";
	string bEqLSign = "<";
	string final = "Final";
	if (timeBonus <= 0)
		bEqLSign = ">=";
	if (difficulty == "Hard") {
		extraMsg = "      >>>      Now get the final Space Egg to complete your run!";
		final = "Current";
	}

	GUI::displayModalMessage(
			"Dyson Speedway Egg Hunt  ( " + difficulty + " )  -  Results\n\n" +
			"Collection Score      " + oldScore + "\n" +
			"Completion Bonus  ( " + difficulty + " )      " + completionBonus + "\n" +
			"Time Bonus  (" + timePassed + " Sec " + bEqLSign + " " + min + " Min )      " + timeBonus + "\n\n" +
			final + " score      " + score +
			extraMsg);
}
// ----------------------------------------------------------------------------


// special thanks
void specialThanksDedicated() {
	GUI::displayMessage("Special thanks to fodoman and Luva9497\nfor hosting dedicated servers for Dyson Speedway testing.");
}

void specialThanksTesting() {
	GUI::displayMessage("Special thanks to Luva9497, Beater, fodoman, RowdyJoe, nimeye, Haenschen, \nHeuchi1, tempAnon093, nascartux-2 and many others for testing Dyson Speedway.");
}
// ----------------------------------------------------------------------------


// ---------------------- test and development functions -----------------------
string kartIDs = "";
void printKartId(int idKart) {
	kartIDs += idKart + ", ";
	Utils::logInfo("kart IDs: " + kartIDs);
}
