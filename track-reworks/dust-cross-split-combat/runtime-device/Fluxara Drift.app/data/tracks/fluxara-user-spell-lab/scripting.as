bool isReverse(Track::TrackObject@ obj)
{
    return Track::isReverse();
}

bool isForward(Track::TrackObject@ obj)
{
    return !Track::isReverse();
}

void warpKart(int idKart, const string libraryInstance, const string obj_id) {
	Vec3 position;
	position = Track::getTrackObject("", "SpotWarp").getCenterPosition();
	Kart::teleportExact(idKart, position);
}

void badTeleport(int idKart, const string libraryInstance, const string obj_id) {
	Vec3 position;
	position = Track::getTrackObject("", "SpotBad").getCenterPosition();
	Kart::teleportExact(idKart, position);
}

void goodTeleport(int idKart, const string libraryInstance, const string obj_id) {
	Vec3 position;
	position = Track::getTrackObject("", "SpotGood").getCenterPosition();
	Kart::teleportExact(idKart, position);
}
