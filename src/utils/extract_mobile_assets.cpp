//  FluxaraDrift - a fun racing game with go-kart
//  Copyright (C) 2019 FluxaraDrift-Team
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 3
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#ifdef MOBILE_FLUXARA_DRIFT

#include "utils/extract_mobile_assets.hpp"
#include "addons/zip.hpp"
#include "challenges/unlock_manager.hpp"
#include "io/file_manager.hpp"
#include "graphics/irr_driver.hpp"
#include "race/grand_prix_manager.hpp"
#include "replay/replay_play.hpp"
#include "tracks/track_manager.hpp"
#include "utils/constants.hpp"
#include "utils/file_utils.hpp"
#include "utils/log.hpp"
// ----------------------------------------------------------------------------
bool ExtractMobileAssets::hasFullAssets()
{
#ifdef IOS_FLUXARA_DRIFT
    // Fluxara ships its complete curated catalog in the app bundle.
    return false;
#else
    return isFullAssetsInstalled();
#endif
}   // hasFullAssets

// ----------------------------------------------------------------------------
bool ExtractMobileAssets::isFullAssetsInstalled()
{
    const std::string& dir = file_manager->getFLUXARA_DRIFTAssetsDownloadDir();
    if (dir.empty())
        return false;
#ifdef IOS_FLUXARA_DRIFT
    return false;
#else
    return file_manager->fileExists(dir + "fluxara_drift-assets." + FLUXARA_DRIFT_VERSION);
#endif
}   // isFullAssetsInstalled

// ----------------------------------------------------------------------------
bool ExtractMobileAssets::extract(const std::string& zip_file,
                                  const std::string& dst)
{
    if (!file_manager->fileExists(zip_file))
        return false;

#ifdef IOS_FLUXARA_DRIFT
    file_manager->removeFile(zip_file);
    return false;
#else
    bool succeed = false;
    // Remove previous fluxara_drift-assets version and create a new one
    file_manager->removeDirectory(dst);
    file_manager->checkAndCreateDirectory(dst);
    if (extract_zip(zip_file, dst, true/*recursive*/))
    {
        std::string extract_ok = dst + "fluxara_drift-assets." + FLUXARA_DRIFT_VERSION;
        FILE* fp = fopen(extract_ok.c_str(), "wb");
        if (!fp)
        {
            Log::error("ExtractMobileAssets",
                "Failed to create extract ok file.");
        }
        else
        {
            fclose(fp);
            succeed = true;
        }
    }
    file_manager->removeFile(zip_file);
    return succeed;
#endif
}   // extract

// ----------------------------------------------------------------------------
void ExtractMobileAssets::reloadTracksAfterDownload()
{
    // The add-ons tracks directory is registered during normal startup and is
    // an ordinary filesystem directory, so the new pack is visible to the
    // existing TrackManager without rebuilding Irrlicht's device.  Calling
    // reinit() here requests a renderer restart while Campaign still owns
    // menu textures; on iOS that dereferenced those stale textures and
    // terminated immediately after a successful download.
    track_manager->loadTrackList();
}   // reloadTracksAfterDownload

// ----------------------------------------------------------------------------
void ExtractMobileAssets::reinit()
{
    file_manager->reinitAfterDownloadAssets();
    irr_driver->sameRestart();
    track_manager->loadTrackList();
    // Update the replay file list to use latest track pointer
    ReplayPlay::get()->loadAllReplayFile();

    delete grand_prix_manager;
    grand_prix_manager = new GrandPrixManager();
    grand_prix_manager->checkConsistency();
    if (unlock_manager)
        unlock_manager->reloadChallengesAndStatuses();
}   // reinit

// ----------------------------------------------------------------------------
void ExtractMobileAssets::uninstall()
{
    // Remove the version file in fluxara_drift-assets folder first, so if it crashes /
    // restarted by mobile it will auto discard downloaded assets
#ifdef IOS_FLUXARA_DRIFT
    file_manager->removeDirectory(file_manager->getFLUXARA_DRIFTAssetsDownloadDir());
    reinit();
    return;
#else
    file_manager->removeFile(file_manager->getFLUXARA_DRIFTAssetsDownloadDir() +
        "fluxara_drift-assets." + FLUXARA_DRIFT_VERSION);
#endif
    file_manager->removeDirectory(file_manager->getFLUXARA_DRIFTAssetsDownloadDir());
    reinit();
}   // uninstall

#endif
