// constants
int numLightsBiDir = 32;
int numLightsF = 20;
int numLightsR = 26;
int netwPhaseDetectorInit = 11;			// seconds
int netwPhaseDetectorReset = 16;		// seconds
int maxNetwDoublePhaseCheck = 3;
bool displayEpilepsyWarning = true;

// variables - working LOCALLY ONLY!
int phaseCount = 0;
string prevColor = "Blue";
int netwPhaseDetectorTimeout = 16;		// seconds
int netwDoublePhaseCheckCount = 0;		// 1 unit = 1 second of overTime


bool isTrackForward(Track::TrackObject@ obj) {
    return !Track::isReverse();
}

bool isTrackReverse(Track::TrackObject@ obj) {
    return Track::isReverse();
}

bool isNetworking(Track::TrackObject@ obj) {
    return Utils::isNetworking();
}

bool isNetworkingF(Track::TrackObject@ obj) {
    return Utils::isNetworking() && !Track::isReverse();
}

bool isNetworkingR(Track::TrackObject@ obj) {
    return Utils::isNetworking() && Track::isReverse();
}

bool maybeLater(Track::TrackObject@ obj) {
	return false;
}


void onStart() {
	phaseCount = 0;
	prevColor = "Blue";
	
	if (!Utils::isNetworking())
		Track::setTriggerReenableTimeout("NetwPhaseChangeDetector", "", 1000000);
	else {
		Track::setTriggerReenableTimeout("LapTrigger", "", 1000000);
		
		netwDoublePhaseCheckCount = 0;
		speedUpNetw(prevColor);
	}
	
	if (displayEpilepsyWarning)
		GUI::displayMessage("WARNING: Playing or watching this track is NOT RECOMMENDED\nfor people with PHOTOSENSITIYE EPILEPSPY!", 3);
}

// performs changes of the object + trigger based phases for single player modes ONLY
void speedUp(int idKart) {
	if (Utils::isNetworking()) 
		return;
	
	phaseCount++;
	string direction = getDirectionLetter();
	
	int countValue;
	if ((Track::getMinorRaceMode() != 1001 && phaseCount > 7) || phaseCount > 20)
		countValue = Utils::randomInt(1, 20);
	else 
		countValue = phaseCount;

	string color = nextAlert(countValue, phaseCount);
	//Utils::logInfo("speedUp: " + phaseCount + " " + prevColor + " " + color);
	
 	if (phaseCount > 1 && color == prevColor) 
 		return;
	
	changePhase(prevColor, false, direction);		// disables previous phase
	changePhase(color, true, direction);			// enables next phase

	prevColor = color;
}

// trigger based local checks for changes of the animation based phases in networking modes
void checkSpeedUpNetw(int idKart) {
	string currentColor = netwCurrentAlert();
 	
 	if (currentColor == prevColor) {
 		// reduces check timeout towards the expected end of a phase
 		// if minimum timeout length isn't reached, yet
 		if (netwPhaseDetectorTimeout > 1) {
 			netwPhaseDetectorTimeout /= 2;
			Track::setTriggerReenableTimeout("NetwPhaseChangeDetector", "", netwPhaseDetectorTimeout);
		} 
		// checks for double phase
		else {
		 	if (phaseCount >= 7) {
				netwDoublePhaseCheckCount++;
				if (netwDoublePhaseCheckCount > maxNetwDoublePhaseCheck) {
 					speedUpNetw(currentColor);
 					return;
 				}
 			}
			Track::setTriggerReenableTimeout("NetwPhaseChangeDetector", "", netwPhaseDetectorTimeout);
		}
		//Utils::logInfo("checkSpeedUpNetw: " + phaseCount + " " + prevColor + " " + currentColor + " " + netwPhaseDetectorTimeout + " " + netwDoublePhaseCheckCount);
 	}
 	else {
 		netwDoublePhaseCheckCount = 0;		// kann weg?
 		speedUpNetw(currentColor);
 	}
}

// performs local change of non-animated phase elements in networking modes
void speedUpNetw(string currentColor) {
	phaseCount++;
	string direction = getDirectionLetter();
	int overTime = 0;

	nextAlert(phaseCount, phaseCount);
	//Utils::logInfo("speedUpNetw: " + phaseCount + " " + prevColor + " " + currentColor);

	changePhase(prevColor, false, direction);			// disables previous phase
	changePhase(currentColor, true, direction);			// enables next phase

	if (prevColor == currentColor)
		overTime = netwDoublePhaseCheckCount;
	else 
		prevColor = currentColor;

	Track::setTriggerReenableTimeout("NetwPhaseChangeDetector", "", netwPhaseDetectorInit - overTime);
 	netwDoublePhaseCheckCount = 0;
	netwPhaseDetectorTimeout = netwPhaseDetectorReset;
}

// detecs what the current phase is in networking modes
string netwCurrentAlert() {
	if (!Track::isReverse()) {
		if (Track::getTrackObject("", "ZippersBlueFNetw").getCenterPosition().getY() > -500) 
			return "Blue";
		if (Track::getTrackObject("", "ZippersPurpleFNetw").getCenterPosition().getY() > -500) 
			return "Purple";
		if (Track::getTrackObject("", "ZippersGreenFNetw").getCenterPosition().getY() > -500) 
			return "Green";
		if (Track::getTrackObject("", "ZippersYellowFNetw").getCenterPosition().getY() > -500) 
			return "Yellow";
		if (Track::getTrackObject("", "ZippersRedFNetw").getCenterPosition().getY() > -500) 
			return "Red";
		if (Track::getTrackObject("", "ZippersCyanFNetw").getCenterPosition().getY() > -500) 
			return "Cyan";
		if (Track::getTrackObject("", "ZippersWhiteFNetw").getCenterPosition().getY() > -500) 
			return "White";
	}
	else {
		if (Track::getTrackObject("", "ZippersBlueRNetw").getCenterPosition().getY() > -500) 
			return "Blue";
		if (Track::getTrackObject("", "ZippersPurpleRNetw").getCenterPosition().getY() > -500) 
			return "Purple";
		if (Track::getTrackObject("", "ZippersGreenRNetw").getCenterPosition().getY() > -500) 
			return "Green";
		if (Track::getTrackObject("", "ZippersYellowRNetw").getCenterPosition().getY() > -500) 
			return "Yellow";
		if (Track::getTrackObject("", "ZippersRedRNetw").getCenterPosition().getY() > -500) 
			return "Red";
		if (Track::getTrackObject("", "ZippersCyanRNetw").getCenterPosition().getY() > -500) 
			return "Cyan";
		if (Track::getTrackObject("", "ZippersWhiteRNetw").getCenterPosition().getY() > -500) 
			return "White";
	}	
	return "Blue";
}

string nextAlert(int countValue, int phaseCount) {
	string color = "Blue";
	string alertText = "";
	
	switch (countValue % 20) {
		case 1: case 15:
			color = "Blue";
			alertText = "CODE BLUE";
		    Track::getTrackObject("", "alarm_emitter").getSoundEmitter().playOnce();
			break;
		case 2: case 13:
			color = "Green";
			alertText = "CODE GREEN - WARNING";
			Track::getTrackObject("", "alarm_emitter2").getSoundEmitter().playOnce();
			break;
		case 3: case 9: case 18:
			color = "Yellow";
			alertText = "CODE YELLOW - WARNING !";
		    Track::getTrackObject("", "alarm_emitter2").getSoundEmitter().playOnce();
			break;
		case 4: case 14:
			color = "Cyan";
			alertText = "! CODE CYAN - CRITICAL WARNING !";
		    Track::getTrackObject("", "alarm_emitter2").getSoundEmitter().playOnce();
			break;
		case 5: case 12:
			color = "White";
			alertText = "! CODE WHITE - ALERT !";
		    Track::getTrackObject("", "alarm_emitter3").getSoundEmitter().playOnce();
			break;
		case 6: case 10: case 17:
			color = "Red";
			alertText = "!! CODE RED - CRITICAL ALERT !!";
		    Track::getTrackObject("", "alarm_emitter3").getSoundEmitter().playOnce();
			break;
		case 7: case 8: case 11: case 16: case 19: case 0: default:
			color = "Purple";
			alertText = "!!! ULTRA VIOLET EXCEPTION ALERT !!!";
		    Track::getTrackObject("", "alarm_emitter3").getSoundEmitter().playOnce();
	}
	
	GUI::displayMessage("> > > Phase " + phaseCount + " < < <\n" + alertText);

	return color;
}

void changePhase(string color, bool enable, string dir) {
	if (!Utils::isNetworking()) {
		Track::getTrackObject("", "Zippers" + color + dir).setEnabled(enable);
		Track::getTrackObject("", "Ice" + color).setEnabled(enable);
	}
	Track::getTrackObject("", "Arrows" + color + dir).setEnabled(enable);
	Track::getTrackObject("", "Barrier" + color).setEnabled(enable);
	Track::getTrackObject("", "CrystalsCave2" + color).setEnabled(enable);
	Track::getTrackObject("", "CrystalsEdgesCave2" + color).setEnabled(enable);
	
	int numLightsDir;
	if (!Track::isReverse())
 		numLightsDir = numLightsF;
	else
		numLightsDir = numLightsR;	
	
	changeLighting(color, enable , "", numLightsBiDir);
	changeLighting(color, enable , dir, numLightsDir);
}

void changeLighting(string color, bool enable, string dir, int numLights) {
	for (int i = 0; i < numLights; i++) {
		string fillZero = "";
		if (i < 10) 
			fillZero = "0";
		Track::getTrackObject("", "Light" + color + dir + ".0" + fillZero + i).setEnabled(enable);
	}
}

string getDirectionLetter() {
	if (!Track::isReverse())
		return "F";
	else 
		return "R";
}

/*void playSound(int idKart, const string library_instance_id, const string obj_id) {
    Track::getTrackObject("", "alarm_emitter").getSoundEmitter().playOnce();
}

void onTestObjectKartCollision(int itemType, int idKart, const string objID) {
	GUI::displayMessage("asdasd");
}*/
