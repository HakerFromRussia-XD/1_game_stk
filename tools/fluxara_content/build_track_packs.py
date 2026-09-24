#!/usr/bin/env python3
"""Create data-only Fluxara campaign-track packages and their catalog.

The catalog is bundled with the IPA.  Package output is deliberately separate:
publishing a GitHub Release remains an explicit release action, not a side
effect of building the application.
"""

from __future__ import annotations

import argparse
import hashlib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "iosApp" / "FluxaraResources"
TRACKS = RESOURCES / "tracks"
CAMPAIGN = RESOURCES / "fluxara-campaign.xml"
CATALOG = RESOURCES / "fluxara-track-catalog.xml"
RELEASE_BASE = (
    "https://github.com/HakerFromRussia-XD/1_game_stk/releases/"
    "download/fluxara-track-packs-1"
)
STARTER_TRACKS = {
    "fluxara-canyon",
    "fluxara-user-ski-dash",
    "fluxara-user-dust-cross-split-combat",
    "fluxara-user-spell-lab",
    "fluxara-user-orbital-simulation---soccer",
    "fluxara-user-dp-motorsports-land-ii",
    "fluxara-user-lap-catch",
    "fluxara-user-motorsport-land",
    "fluxara-summit-run",
    "fluxara-user-volcano-remake",
}
ALLOWED_SUFFIXES = {
    ".b3d", ".dds", ".jpg", ".jpeg", ".music", ".ogg", ".png",
    ".spm", ".txt", ".xml",
}


def campaign_tracks() -> list[str]:
    root = ET.parse(CAMPAIGN).getroot()
    tracks = [node.attrib["track"] for node in root.findall("event")]
    if len(tracks) != 50 or len(set(tracks)) != 50:
        raise RuntimeError("campaign must declare exactly 50 unique tracks")
    if set(tracks[:10]) != STARTER_TRACKS:
        raise RuntimeError("first campaign segment no longer matches starter tracks")
    return tracks


def archive_name(track_id: str) -> str:
    return f"fluxara-track-{track_id}.zip"


def source_files(track_id: str) -> list[Path]:
    root = TRACKS / track_id
    if not (root / "track.xml").is_file():
        raise RuntimeError(f"missing track descriptor: {track_id}")
    result = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        if path.name.startswith("."):
            continue
        # Track scripts are kept in the reviewed IPA under packaged-scripts;
        # downloaded archives never carry executable AngelScript.  Two legacy
        # DDS payloads intentionally have the safe `_dds_img` suffix but no
        # filename extension.
        if path.suffix.lower() == ".as":
            continue
        if (path.suffix.lower() not in ALLOWED_SUFFIXES and
                not path.name.endswith("_dds_img")):
            raise RuntimeError(f"unsupported remote track payload: {path}")
        result.append(path)
    return result


def package_track(track_id: str, dist: Path) -> tuple[int, str]:
    files = source_files(track_id)
    archive = dist / archive_name(track_id)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=False) as output:
        for path in files:
            relative = path.relative_to(TRACKS / track_id).as_posix()
            info = zipfile.ZipInfo.from_file(path, arcname=relative)
            info.external_attr &= ~(0o170000 << 16)
            output.writestr(info, path.read_bytes(),
                            compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive.stat().st_size, digest


def metadata(track_id: str) -> tuple[str, int]:
    root = TRACKS / track_id
    descriptor = ET.parse(root / "track.xml").getroot()
    title = descriptor.attrib.get("name", track_id)
    size = sum(path.stat().st_size for path in source_files(track_id))
    return title, size


def write_catalog(packages: dict[str, tuple[int, str]] | None) -> None:
    root = ET.Element("fluxara-track-catalog", {
        "version": "1",
        "release-base": RELEASE_BASE,
    })
    for track_id in campaign_tracks():
        title, source_size = metadata(track_id)
        attributes = {"id": track_id, "title": title}
        if track_id not in STARTER_TRACKS:
            size, digest = packages.get(track_id, (source_size, "")) \
                if packages else (source_size, "")
            attributes.update({
                "url": f"{RELEASE_BASE}/{archive_name(track_id)}",
                "size-bytes": str(size),
            })
            if digest:
                attributes["sha256"] = digest
        ET.SubElement(root, "track", attributes)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(CATALOG, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("catalog", "package"))
    parser.add_argument("--dist", type=Path,
                        help="directory for uploadable per-track ZIP files")
    args = parser.parse_args()

    if args.command == "catalog":
        write_catalog(None)
        print(f"Catalog: {CATALOG}")
        return 0

    if not args.dist:
        parser.error("package requires --dist")
    packages = {
        track_id: package_track(track_id, args.dist.resolve())
        for track_id in campaign_tracks() if track_id not in STARTER_TRACKS
    }
    write_catalog(packages)
    print(f"Packages: {args.dist.resolve()} ({len(packages)} tracks)")
    print(f"Catalog: {CATALOG}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}")
        raise SystemExit(1)
