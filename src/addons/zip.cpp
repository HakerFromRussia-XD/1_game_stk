//  SuperTuxKart - a fun racing game with go-kart
//  Copyright (C) 2010-2015 Lucas Baudin
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

#include <string.h>
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <fstream>
#include <set>
#include <vector>

#include "graphics/irr_driver.hpp"
#include "io/file_manager.hpp"
#include "utils/log.hpp"
#include "utils/string_utils.hpp"

#include <IrrlichtDevice.h>
#include <IFileSystem.h>
#include <IReadFile.h>
#include <IWriteFile.h>
using namespace irr;
using namespace io;
s32 IFileSystem_copyFileToFile(IWriteFile* dst, IReadFile* src)
{
  char buf[1024];
  const s32 sz = sizeof(buf) / sizeof(*buf);

  s32 rx = src->getSize();
  for (s32 r = 0; r < rx; /**/)
  {
    s32 wx = src->read(buf, sz);
    for (s32 w = 0; w < wx; /**/)
    {
      s32 n = dst->write(buf + w, wx - w);
      if (n < 0)
        return -1;
      else
        w += n;
    }
    r += wx;
  }
  return rx;
}   // IFileSystem_copyFileToFile

// ----------------------------------------------------------------------------
/** Extracts all files from the zip archive 'from' to the directory 'to'.
 *  \param from A zip archive.
 *  \param to The destination directory.
 *  \return True if successful.
 */
static bool isSafeArchivePath(std::string path, bool data_only)
{
    std::replace(path.begin(), path.end(), '\\', '/');
    if (path.empty() || path[0] == '/' || path.find(':') != std::string::npos)
        return false;

    size_t begin = 0;
    while (begin <= path.size())
    {
        size_t end = path.find('/', begin);
        std::string component = path.substr(begin, end - begin);
        if (component == "..")
            return false;
        if (end == std::string::npos)
            break;
        begin = end + 1;
    }

    if (!data_only)
        return true;

    size_t dot = path.find_last_of('.');
    if (dot == std::string::npos)
        return false;
    std::string extension = path.substr(dot);
    std::transform(extension.begin(), extension.end(), extension.begin(),
        [](unsigned char c) { return (char)std::tolower(c); });
    static const std::set<std::string> allowed = {
        ".jpg", ".jpeg", ".music", ".ogg", ".png", ".spm",
        ".txt", ".xml"
    };
    return allowed.find(extension) != allowed.end();
}

// Irrlicht intentionally exposes ZIP contents as ordinary files and does not
// expose the creator-system or Unix mode stored in the central directory. Read
// that small metadata table ourselves so a data package containing a symlink is
// rejected before Irrlicht gets a chance to extract anything.
static uint16_t readLE16(const unsigned char* data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8);
}

static uint32_t readLE32(const unsigned char* data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
           ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 24);
}

static bool hasSafeZipEntryTypes(const std::string& archive_path)
{
    std::ifstream archive(archive_path.c_str(), std::ios::binary);
    if (!archive)
        return false;

    archive.seekg(0, std::ios::end);
    const std::streamoff archive_size = archive.tellg();
    if (archive_size < 22)
        return false;

    const std::streamoff tail_size =
        std::min<std::streamoff>(archive_size, 65557);
    std::vector<unsigned char> tail((size_t)tail_size);
    archive.seekg(archive_size - tail_size, std::ios::beg);
    archive.read(reinterpret_cast<char*>(tail.data()), tail_size);
    if (!archive)
        return false;

    size_t eocd = tail.size();
    for (size_t cursor = tail.size() - 22; ; cursor--)
    {
        if (readLE32(&tail[cursor]) == 0x06054b50)
        {
            const uint16_t comment_length = readLE16(&tail[cursor + 20]);
            if (cursor + 22 + comment_length == tail.size())
            {
                eocd = cursor;
                break;
            }
        }
        if (cursor == 0)
            break;
    }
    if (eocd == tail.size())
        return false;

    const uint16_t disk = readLE16(&tail[eocd + 4]);
    const uint16_t central_disk = readLE16(&tail[eocd + 6]);
    const uint16_t disk_entries = readLE16(&tail[eocd + 8]);
    const uint16_t total_entries = readLE16(&tail[eocd + 10]);
    const uint32_t central_size = readLE32(&tail[eocd + 12]);
    const uint32_t central_offset = readLE32(&tail[eocd + 16]);
    if (disk != 0 || central_disk != 0 || disk_entries != total_entries ||
        total_entries == 0xffff || central_size == 0xffffffff ||
        central_offset == 0xffffffff ||
        (uint64_t)central_offset + central_size > (uint64_t)archive_size)
    {
        // Multi-disk and ZIP64 packages are unnecessary for the pinned
        // Motorica catalog and are rejected to keep this validator strict.
        return false;
    }

    archive.clear();
    archive.seekg(central_offset, std::ios::beg);
    uint32_t consumed = 0;
    for (uint16_t entry = 0; entry < total_entries; entry++)
    {
        unsigned char header[46];
        archive.read(reinterpret_cast<char*>(header), sizeof(header));
        if (!archive || readLE32(header) != 0x02014b50)
            return false;

        const uint16_t version_made_by = readLE16(&header[4]);
        const uint16_t name_length = readLE16(&header[28]);
        const uint16_t extra_length = readLE16(&header[30]);
        const uint16_t comment_length = readLE16(&header[32]);
        const uint32_t external_attributes = readLE32(&header[38]);
        const uint8_t creator_system = (uint8_t)(version_made_by >> 8);
        const uint32_t unix_type = (external_attributes >> 16) & 0170000;
        if ((creator_system == 3 || creator_system == 19) &&
            unix_type == 0120000)
        {
            Log::error("addons", "ZIP contains a symbolic-link entry.");
            return false;
        }

        const uint32_t variable_size =
            (uint32_t)name_length + extra_length + comment_length;
        consumed += (uint32_t)sizeof(header) + variable_size;
        if (consumed > central_size)
            return false;
        archive.seekg(variable_size, std::ios::cur);
        if (!archive)
            return false;
    }
    return consumed == central_size;
}

bool extract_zip(const std::string &from, const std::string &to,
                 bool recursive, bool data_only)
{
    if (data_only && !hasSafeZipEntryTypes(from))
    {
        Log::error("addons", "ZIP entry type validation failed.");
        return false;
    }

    //Add the zip to the file system
    IFileSystem *file_system = irr_driver->getDevice()->getFileSystem();
    if(!file_system->addFileArchive(from.c_str(),
                                    /*ignoreCase*/false,
                                   /*ignorePath*/!recursive, io::EFAT_ZIP))
    {
        return false;
    }

    // Get the recently added archive, which is necessary to get a
    // list of file in the zip archive.
    io::IFileArchive *zip_archive =
        file_system->getFileArchive(file_system->getFileArchiveCount()-1);
    const io::IFileList *zip_file_list = zip_archive->getFileList();

    // Validate the complete archive before writing the first byte. This
    // blocks traversal/absolute paths and, for Motorica's remote package,
    // rejects anything other than the reviewed data formats.
    uint64_t uncompressed_size = 0;
    for (unsigned int i = 0; i < zip_file_list->getFileCount(); i++)
    {
        if (zip_file_list->isDirectory(i))
            continue;
        const std::string path =
            zip_file_list->getFullFileName(i).c_str();
        if (!isSafeArchivePath(path, data_only))
        {
            Log::error("addons", "Unsafe or unsupported ZIP entry '%s'.",
                       path.c_str());
            file_system->removeFileArchive(
                file_system->getAbsolutePath(from.c_str()));
            return false;
        }
        uncompressed_size += (uint64_t)zip_file_list->getFileSize(i);
        if (uncompressed_size > 1024ull * 1024ull * 1024ull)
        {
            Log::error("addons", "ZIP expands beyond the 1 GiB safety limit.");
            file_system->removeFileArchive(
                file_system->getAbsolutePath(from.c_str()));
            return false;
        }
    }

    // Copy all files from the zip archive to the destination
    bool error = false;
    for(unsigned int i=0; i<zip_file_list->getFileCount(); i++)
    {
        if(zip_file_list->isDirectory(i)) continue;
        if(zip_file_list->getFileName(i)[0]=='.') continue;
        std::string base = zip_file_list->getFullFileName(i).c_str();
        if (!recursive)
            base = StringUtils::getBasename(base);

        Log::debug("addons", "Unzipping file '%s'.", base.c_str());

        IReadFile* src_file =
            zip_archive->createAndOpenFile(base.c_str());
        if(!src_file)
        {
            Log::warn("addons", "Can't read file '%s'. This is ignored, but the addon might not work", base.c_str());
            error = true;
            continue;
        }

        std::string file_location = to + "/" + base;
        if (recursive)
        {
            const std::string& dir = StringUtils::getPath(file_location);
            file_manager->checkAndCreateDirectoryP(dir);
        }
        IWriteFile* dst_file =
            file_system->createAndWriteFile(file_location.c_str());
        if(dst_file == NULL)
        {
            Log::warn("addons", "Couldn't create the file '%s'. The directory might not exist. This is ignored, but the addon might not work.", file_location.c_str());
            error = true;
            continue;
        }

        if (IFileSystem_copyFileToFile(dst_file, src_file) < 0)
        {
            Log::warn("addons", "Could not copy '%s' from archive '%s'. This is ignored, but the addon might not work.",
                      base.c_str(), from.c_str());
            error = true;
        }
        dst_file->drop();
        src_file->drop();
    }
    // Remove the zip from the filesystem to save memory and avoid
    // problem with a name conflict. Note that we have to convert
    // the path using getAbsolutePath, otherwise windows name
    // will not be detected correctly (e.g. if from=c:\...  the
    // stored filename will be c:/..., which then does not match
    // on removing it. getAbsolutePath will convert all \ to /.
    file_system->removeFileArchive(file_system->getAbsolutePath(from.c_str()));

    return !error;
}   // extract_zip
