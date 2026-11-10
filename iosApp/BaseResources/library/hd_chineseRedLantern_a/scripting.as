/* Script used to disable point light for lamps when the track is set during day
   Jean-Manuel Clemencon (c) 2018 for FluxaraDrift
*/
namespace hd_chineseRedLantern_a
{
    void onStart(const string instID)
    {
        if (Track::isDuringDay())
        {
            Track::TrackObject@ lamp = Track::getTrackObject(instID, "Lamp");
            lamp.setEnabled(false);
        }
    }
}
