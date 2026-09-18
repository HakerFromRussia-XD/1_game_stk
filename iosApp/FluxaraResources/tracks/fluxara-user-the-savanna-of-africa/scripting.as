bool isNotCTF(Track::TrackObject@ obj)
{
    // enum RaceManager::MINOR_MODE_CAPTURE_THE_FLAG is 2002
    return Track::getMinorRaceMode() != 2002;
}

bool isCTF(Track::TrackObject@ obj)
{
    return !isNotCTF(obj);
}

bool isTrackReverse(Track::TrackObject@ obj)
{
    return Track::isReverse();
}

bool isTrackNotReverse(Track::TrackObject@ obj)
{
    return !Track::isReverse();
}

bool isEasterEgg(Track::TrackObject@ obj)
{
    // enum RaceManager::MINOR_MODE_EASTER_EGG is 3000
    return Track::getMinorRaceMode() == 3000;
}
