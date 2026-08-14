//  SuperTuxKart - a fun racing game with go-kart
//  Copyright (C) 2019 SuperTuxKart-Team
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

#ifdef MOBILE_STK

#include "utils/extract_mobile_assets.hpp"
#include "addons/zip.hpp"
#include "io/file_manager.hpp"
#include "graphics/irr_driver.hpp"
#include "race/grand_prix_manager.hpp"
#include "replay/replay_play.hpp"
#include "tracks/track_manager.hpp"
#include "utils/constants.hpp"
#include "utils/file_utils.hpp"
#include "utils/log.hpp"
#ifdef IOS_STK
#include "input/motorica_game_control_ios.hpp"
#include "utils/motorica_assets_manifest.hpp"
#include <mbedtls/sha256.h>
#include <array>
#include <iomanip>
#include <sstream>
#include <sys/stat.h>
#endif

// ----------------------------------------------------------------------------
bool ExtractMobileAssets::hasFullAssets()
{
#ifdef IOS_STK
    // The downloaded original STK catalog is deliberately invisible to a
    // direct icon launch. Merely having the package on disk must not change
    // the permanent standalone product experience.
    if (isMotoricaStandaloneModeIOS())
        return false;
#endif
    return isFullAssetsInstalled();
}   // hasFullAssets

// ----------------------------------------------------------------------------
bool ExtractMobileAssets::isFullAssetsInstalled()
{
    const std::string& dir = file_manager->getSTKAssetsDownloadDir();
    if (dir.empty())
        return false;
#ifdef IOS_STK
    return file_manager->fileExists(dir + MotoricaAssetsManifest::MARKER);
#else
    return file_manager->fileExists(dir + "stk-assets." + STK_VERSION);
#endif
}   // isFullAssetsInstalled

#ifdef IOS_STK
// ----------------------------------------------------------------------------
static bool verifyMotoricaArchive(const std::string& zip_file)
{
    struct stat file_stat;
    if (FileUtils::statU8Path(zip_file, &file_stat) != 0 ||
        (uint64_t)file_stat.st_size != MotoricaAssetsManifest::SIZE_BYTES)
    {
        Log::error("ExtractMobileAssets", "Downloaded asset size mismatch.");
        return false;
    }

    FILE* stream = FileUtils::fopenU8Path(zip_file, "rb");
    if (!stream)
        return false;

    mbedtls_sha256_context context;
    mbedtls_sha256_init(&context);
    bool ok = mbedtls_sha256_starts(&context, 0) == 0;
    std::array<unsigned char, 1024 * 1024> buffer;
    while (ok)
    {
        size_t count = fread(buffer.data(), 1, buffer.size(), stream);
        if (count > 0 &&
            mbedtls_sha256_update(&context, buffer.data(), count) != 0)
            ok = false;
        if (count < buffer.size())
        {
            if (ferror(stream))
                ok = false;
            break;
        }
    }
    fclose(stream);

    unsigned char digest[32];
    if (ok)
        ok = mbedtls_sha256_finish(&context, digest) == 0;
    mbedtls_sha256_free(&context);
    if (!ok)
        return false;

    std::ostringstream output;
    output << std::hex << std::setfill('0');
    for (unsigned char value : digest)
        output << std::setw(2) << (unsigned int)value;
    if (output.str() != MotoricaAssetsManifest::SHA256)
    {
        Log::error("ExtractMobileAssets", "Downloaded asset SHA-256 mismatch.");
        return false;
    }
    return true;
}

// ----------------------------------------------------------------------------
static std::string withoutTrailingSlash(std::string path)
{
    while (!path.empty() && (path.back() == '/' || path.back() == '\\'))
        path.pop_back();
    return path;
}
#endif

// ----------------------------------------------------------------------------
bool ExtractMobileAssets::extract(const std::string& zip_file,
                                  const std::string& dst)
{
    if (!file_manager->fileExists(zip_file))
        return false;

#ifdef IOS_STK
    if (!verifyMotoricaArchive(zip_file))
    {
        file_manager->removeFile(zip_file);
        return false;
    }

    const std::string target = withoutTrailingSlash(dst);
    const std::string temporary = target + ".installing";
    const std::string backup = target + ".previous";
    file_manager->removeDirectory(temporary);
    file_manager->checkAndCreateDirectoryP(temporary + "/");

    bool succeed = extract_zip(zip_file, temporary, true/*recursive*/,
                               true/*data_only*/);
    const std::string required[] = {
        "tracks/overworld/track.xml",
        "karts/kiki/kart.xml",
        "textures/licenses.txt",
        "music/licenses.txt"
    };
    for (const std::string& relative : required)
    {
        if (succeed && !file_manager->fileExists(temporary + "/" + relative))
        {
            Log::error("ExtractMobileAssets", "Required asset is missing: %s",
                       relative.c_str());
            succeed = false;
        }
    }

    if (succeed)
    {
        FILE* marker = FileUtils::fopenU8Path(
            temporary + "/" + MotoricaAssetsManifest::MARKER, "wb");
        if (!marker)
            succeed = false;
        else
            fclose(marker);
    }

    bool moved_old = false;
    if (succeed && FileManager::isDirectory(target))
    {
        file_manager->removeDirectory(backup);
        moved_old = FileUtils::renameU8Path(target, backup) == 0;
        succeed = moved_old;
    }
    if (succeed && FileUtils::renameU8Path(temporary, target) != 0)
    {
        Log::error("ExtractMobileAssets", "Failed to activate asset package.");
        succeed = false;
        if (moved_old)
            FileUtils::renameU8Path(backup, target);
    }
    if (succeed && moved_old)
        file_manager->removeDirectory(backup);
    if (!succeed)
        file_manager->removeDirectory(temporary);

    file_manager->removeFile(zip_file);
    return succeed;
#else
    bool succeed = false;
    // Remove previous stk-assets version and create a new one
    file_manager->removeDirectory(dst);
    file_manager->checkAndCreateDirectory(dst);
    if (extract_zip(zip_file, dst, true/*recursive*/))
    {
        std::string extract_ok = dst + "stk-assets." + STK_VERSION;
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
}   // reinit

// ----------------------------------------------------------------------------
void ExtractMobileAssets::uninstall()
{
    // Remove the version file in stk-assets folder first, so if it crashes /
    // restarted by mobile it will auto discard downloaded assets
#ifdef IOS_STK
    file_manager->removeFile(file_manager->getSTKAssetsDownloadDir() +
        MotoricaAssetsManifest::MARKER);
#else
    file_manager->removeFile(file_manager->getSTKAssetsDownloadDir() +
        "stk-assets." + STK_VERSION);
#endif
    file_manager->removeDirectory(file_manager->getSTKAssetsDownloadDir());
    reinit();
}   // uninstall

#endif
