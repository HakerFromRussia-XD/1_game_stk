#!/usr/bin/env python3
"""Build the permanent Motorica standalone overlay and iOS asset packages.

The tracked overlay is intentionally separate from build-ios-assets.  The
latter is only a generated CMake input and must never be edited by hand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw, ImageEnhance


REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY_ROOT = REPO_ROOT / "motorica-assets-overlay" / "data"
DEFAULT_SOURCE = Path("/Users/motoricallc/Downloads/stk-assets")
DEFAULT_MOBILE_BASE = REPO_ROOT / "build-ios-assets" / "assets" / "data"
DEFAULT_BASE_OUTPUT = REPO_ROOT / "build-motorica-ios-assets" / "assets" / "data"
DEFAULT_DIST = REPO_ROOT / "dist" / "motorica-assets"

ASSET_VERSION = "1"
MINIMUM_APP_BUILD = 28
RELEASE_TAG = "ios-assets-1.0-build28"
ARCHIVE_NAME = "motorica-stk-full-assets-1.zip"
MANIFEST_NAME = "motorica-stk-full-assets-1.json"
CHECKSUM_NAME = "motorica-stk-full-assets-1.sha256"
ARCHIVE_URL = (
    "https://github.com/HakerFromRussia-XD/1_game_stk/releases/download/"
    f"{RELEASE_TAG}/{ARCHIVE_NAME}"
)
MARKER = "motorica-stk-assets.1"

REMOTE_ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".music", ".ogg", ".png", ".spm", ".txt", ".xml"
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def verify_source(source: Path) -> None:
    required = [
        source / "tracks" / "overworld" / "scene.xml",
        source / "tracks" / "lighthouse" / "scene.xml",
        source / "tracks" / "soccer_field" / "scene.xml",
        source / "karts" / "kiki" / "kart.xml",
        source / "textures" / "Cloth_Kiki01.png",
        source / "textures" / "Cloth_Kiki01_colormask.png",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        fail("Incompatible stk-assets checkout; missing: " + ", ".join(missing))

    # Large shared collections use aggregate license inventories, while each
    # kart keeps an adjacent one. Refuse to package an incomplete checkout.
    aggregate_licenses = [
        source / "models" / "licenses.txt",
        source / "music" / "licenses.txt",
        source / "sfx" / "licenses.txt",
        source / "textures" / "licenses.txt",
    ]
    missing_licenses = [str(path) for path in aggregate_licenses
                        if not path.is_file()]
    for kart in sorted((source / "karts").iterdir()):
        if kart.is_dir() and not (kart / "licenses.txt").is_file():
            missing_licenses.append(str(kart / "licenses.txt"))
    if missing_licenses:
        fail("Asset license inventory is incomplete; missing: " +
             ", ".join(missing_licenses))


def safe_replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def golden_grass(image_path: Path) -> None:
    image = Image.open(image_path).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        luminance = (red * 0.26 + green * 0.62 + blue * 0.12)
        pixels.append((
            min(255, int(luminance * 1.34 + 36)),
            min(255, int(luminance * 0.88 + 24)),
            min(255, int(luminance * 0.22 + 12)),
            alpha,
        ))
    image.putdata(pixels)
    image.convert("RGB" if image_path.suffix.lower() in {".jpg", ".jpeg"}
                  else "RGBA").save(image_path, quality=92)


def night_tint(image_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    image = ImageEnhance.Brightness(image).enhance(0.25)
    red, green, blue = image.split()
    red = red.point(lambda value: min(255, int(value * 0.52 + 3)))
    green = green.point(lambda value: min(255, int(value * 0.72 + 8)))
    blue = blue.point(lambda value: min(255, int(value * 1.36 + 24)))
    Image.merge("RGB", (red, green, blue)).save(image_path, quality=92)


def recolor_kiki(image_path: Path, palette: str) -> None:
    image = Image.open(image_path).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        luminance = red * 0.27 + green * 0.62 + blue * 0.11
        saturation = max(red, green, blue) - min(red, green, blue)
        if alpha == 0 or saturation < 12:
            pixels.append((red, green, blue, alpha))
            continue
        if palette == "violet":
            pixels.append((
                min(255, int(luminance * 1.08 + 55)),
                min(255, int(luminance * 0.34 + 16)),
                min(255, int(luminance * 1.20 + 70)),
                alpha,
            ))
        else:
            pixels.append((
                min(255, int(luminance * 1.18 + 40)),
                min(255, int(luminance * 0.74 + 30)),
                min(255, int(luminance * 0.22 + 8)),
                alpha,
            ))
    image.putdata(pixels)
    image.save(image_path)


def remove_matching_children(parent: ET.Element, predicate) -> None:
    for child in list(parent):
        if predicate(child):
            parent.remove(child)
        else:
            remove_matching_children(child, predicate)


def add_curve(parent: ET.Element, channel: str, values: list[tuple[int, float]]) -> None:
    curve = ET.SubElement(parent, "curve", {
        "channel": channel,
        "interpolation": "linear",
        "extend": "cyclic",
    })
    for frame, value in values:
        point = f"{frame:.3f} {value:.3f}"
        ET.SubElement(curve, "p", {"c": point, "h1": point, "h2": point})


def add_ufo(parent: ET.Element, identifier: str, xyz: str, scale: str = "2.4 2.4 2.4") -> None:
    ET.SubElement(parent, "static-object", {
        "id": identifier,
        "model": "bubble_solid_saucer.spm",
        "xyz": xyz,
        "hpr": "0.0 0.0 0.0",
        "scale": scale,
        "interaction": "ghost",
        "skeletal-animation": "false",
    })


def add_animated_ufo(scene: ET.Element) -> None:
    ufo = ET.SubElement(scene, "object", {
        "id": "motorica_ufo_patrol",
        "type": "animation",
        "xyz": "24.0 58.0 110.0",
        "hpr": "0.0 0.0 0.0",
        "scale": "3.2 3.2 3.2",
        "interaction": "ghost",
        "model": "bubble_solid_saucer.spm",
        "skeletal-animation": "false",
    })
    add_curve(ufo, "LocX", [(1, -110), (160, 110), (320, -110)])
    add_curve(ufo, "LocZ", [(1, 120), (160, 250), (320, 120)])
    add_curve(ufo, "LocY", [(1, 58), (160, 72), (320, 58)])
    add_curve(ufo, "RotY", [(1, 0), (160, math.pi), (320, math.pi * 2)])


def build_motorica_kiki(source: Path, overlay: Path) -> None:
    destination = overlay / "karts" / "motorica_kiki"
    safe_replace_tree(source / "karts" / "kiki", destination)

    for texture in [
        "Cloth_Kiki01.png",
        "Cloth_Kiki01_colormask.png",
        "Kiki_body.png",
        "kiki_hair_dif.png",
    ]:
        shutil.copy2(source / "textures" / texture, destination / texture)

    tree = ET.parse(destination / "kart.xml")
    root = tree.getroot()
    root.set("name", "Motorica Kiki")
    root.set("groups", "motorica")
    root.set("rgb", "0.66 0.12 0.84")
    write_xml(tree, destination / "kart.xml")

    recolor_kiki(destination / "Cloth_Kiki01.png", "violet")
    recolor_kiki(destination / "Kiki_body.png", "violet")
    recolor_kiki(destination / "kiki_hair_dif.png", "gold")
    for texture in ["kiki_kart.png", "kiki_icon.png", "kiki_license_plate.png"]:
        recolor_kiki(destination / texture, "gold")

    license_path = destination / "licenses.txt"
    with license_path.open("a", encoding="utf-8") as output:
        output.write(
            "\nMotorica Kiki color variant: MOTORICA RESEARCH LLC, 2026. "
            "Derived from the original Kiki model and textures under the "
            "licenses listed above.\n"
        )


def configure_track_xml(path: Path, name: str, designer: str, *, internal: bool) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    root.set("name", name)
    root.set("designer", designer)
    root.set("groups", "motorica")
    root.set("default-number-of-laps", "3")
    root.set("reverse", "N")
    root.set("clouds", "N")
    root.set("is-during-day", "N")
    root.set("shadows", "Y")
    for mode_attribute in ["soccer", "arena", "ctf", "max-arena-players"]:
        root.attrib.pop(mode_attribute, None)
    if internal:
        root.set("internal", "Y")
        root.set("push-back", "N")
        root.set("auto-rescue", "N")
    else:
        root.attrib.pop("internal", None)
    write_xml(tree, path)


def build_signal_route() -> list[tuple[tuple[float, float, float],
                                       tuple[float, float, float]]]:
    """Create the original Signal Lab waveform route from control points."""
    controls = [
        (0.0, 62.0), (-42.0, 43.0), (-50.0, 10.0), (-61.0, -22.0),
        (-34.0, -49.0), (0.0, -48.0), (25.0, -38.0), (56.0, -28.0),
        (54.0, 8.0), (62.0, 33.0), (31.0, 55.0), (12.0, 65.0),
    ]
    samples_per_segment = 8
    centers: list[tuple[float, float]] = []
    count = len(controls)
    for index in range(count):
        p0 = controls[(index - 1) % count]
        p1 = controls[index]
        p2 = controls[(index + 1) % count]
        p3 = controls[(index + 2) % count]
        for sample in range(samples_per_segment):
            t = sample / samples_per_segment
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                2 * p1[0] + (-p0[0] + p2[0]) * t +
                (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            z = 0.5 * (
                2 * p1[1] + (-p0[1] + p2[1]) * t +
                (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            centers.append((x, z))

    sections = []
    for index, (x, z) in enumerate(centers):
        previous = centers[(index - 1) % len(centers)]
        following = centers[(index + 1) % len(centers)]
        tangent_x = following[0] - previous[0]
        tangent_z = following[1] - previous[1]
        length = math.hypot(tangent_x, tangent_z)
        normal_x = -tangent_z / length
        normal_z = tangent_x / length
        width = 6.2 + 0.9 * math.sin(index * math.pi / 9.0)
        chicane = 0.75 * math.sin(index * math.pi / 6.0)
        center_x = x + normal_x * chicane
        center_z = z + normal_z * chicane
        left = (center_x + normal_x * width, 0.08,
                center_z + normal_z * width)
        right = (center_x - normal_x * width, 0.08,
                 center_z - normal_z * width)
        sections.append((left, right))
    return sections


def format_point(point: tuple[float, float, float]) -> str:
    return " ".join(f"{value:.3f}" for value in point)


def write_signal_quads(destination: Path,
                       sections: list[tuple[tuple[float, float, float],
                                            tuple[float, float, float]]]) -> None:
    root = ET.Element("quads")
    ET.SubElement(root, "height-testing", {"min": "-1.000000", "max": "5.000000"})
    for index, (left, right) in enumerate(sections):
        next_left, next_right = sections[(index + 1) % len(sections)]
        attributes = {
            "p0": format_point(left) if index == 0 else f"{index - 1}:3",
            "p1": format_point(right) if index == 0 else f"{index - 1}:2",
            "p2": "0:1" if index == len(sections) - 1 else format_point(next_right),
            "p3": "0:0" if index == len(sections) - 1 else format_point(next_left),
        }
        ET.SubElement(root, "quad", attributes)
    write_xml(ET.ElementTree(root), destination / "quads.xml")

    graph = ET.Element("graph")
    ET.SubElement(graph, "node-list", {
        "from-quad": "0", "to-quad": str(len(sections) - 1)
    })
    ET.SubElement(graph, "edge-loop", {
        "from": "0", "to": str(len(sections) - 1)
    })
    write_xml(ET.ElementTree(graph), destination / "graph.xml")


def append_signal_race_nodes(scene: ET.Element,
                             sections: list[tuple[tuple[float, float, float],
                                                  tuple[float, float, float]]]) -> None:
    checks = ET.SubElement(scene, "checks")
    ET.SubElement(checks, "check-lap", {
        "kind": "lap", "same-group": "0", "other-ids": "1"
    })
    for check_id, section_index in enumerate(
            [len(sections) // 4, len(sections) // 2, len(sections) * 3 // 4],
            start=1):
        left, right = sections[section_index]
        ET.SubElement(checks, "check-line", {
            "kind": "activate",
            "other-ids": str((check_id + 1) % 4),
            "p1": f"{left[0]:.3f} {left[2]:.3f}",
            "p2": f"{right[0]:.3f} {right[2]:.3f}",
            "min-height": "-1.000",
            "same-group": str(check_id),
        })

    ET.SubElement(scene, "default-start", {
        "karts-per-row": "2",
        "forwards-distance": "1.50",
        "sidewards-distance": "3.00",
        "upwards-distance": "0.10",
    })
    for row in range(4):
        section_index = (len(sections) - 2 - row * 2) % len(sections)
        left, right = sections[section_index]
        next_left, next_right = sections[(section_index + 1) % len(sections)]
        center = tuple((left[axis] + right[axis]) / 2 for axis in range(3))
        next_center = tuple((next_left[axis] + next_right[axis]) / 2
                            for axis in range(3))
        direction_x = next_center[0] - center[0]
        direction_z = next_center[2] - center[2]
        heading = math.degrees(math.atan2(direction_x, direction_z))
        side_x = right[0] - left[0]
        side_z = right[2] - left[2]
        side_length = math.hypot(side_x, side_z)
        for side in (-1.0, 1.0):
            x = center[0] + side_x / side_length * side * 1.8
            z = center[2] + side_z / side_length * side * 1.8
            ET.SubElement(scene, "start", {
                "x": f"{x:.3f}", "y": "0.180", "z": f"{z:.3f}",
                "h": f"{heading:.2f}",
            })

    for index in range(0, len(sections), 6):
        for side_name, point in zip(("left", "right"), sections[index]):
            ET.SubElement(scene, "object", {
                "id": f"motorica_route_{side_name}_{index}",
                "type": "animation",
                "xyz": f"{point[0]:.3f} 0.180 {point[2]:.3f}",
                "hpr": "0.0 0.0 0.0",
                "scale": "0.42 0.42 0.42",
                "interaction": "ghost",
                "model": "signal_marker.spm",
                "skeletal-animation": "false",
            })


def create_signal_preview(path: Path,
                          sections: list[tuple[tuple[float, float, float],
                                               tuple[float, float, float]]]) -> None:
    image = Image.new("RGB", (1024, 576), (7, 9, 28))
    draw = ImageDraw.Draw(image)
    for y in range(image.height):
        ratio = y / image.height
        draw.line((0, y, image.width, y), fill=(
            int(7 + ratio * 18), int(9 + ratio * 15), int(28 + ratio * 25)))
    centers = [
        ((left[0] + right[0]) / 2, (left[2] + right[2]) / 2)
        for left, right in sections
    ]
    points = [
        (512 + x * 8.6, 288 - z * 4.5) for x, z in centers
    ]
    points.append(points[0])
    draw.line(points, fill=(193, 255, 56), width=28, joint="curve")
    draw.line(points, fill=(112, 35, 180), width=8, joint="curve")
    for x, y in [(150, 105), (850, 130), (760, 470)]:
        draw.ellipse((x - 34, y - 12, x + 34, y + 12),
                     fill=(174, 195, 255), outline=(193, 255, 56), width=4)
        draw.ellipse((x - 11, y - 8, x + 11, y + 8), fill=(69, 25, 111))
    image.save(path, quality=94)


def make_scene_night(scene: ET.Element) -> None:
    for sun in scene.iter("sun"):
        sun.set("fog", "true")
        sun.set("fog-color", "8 12 35")
        sun.set("fog-max", "0.72")
        sun.set("fog-start", "18.00")
        sun.set("fog-end", "420.00")
        sun.set("sun-specular", "146 170 255")
        sun.set("sun-diffuse", "36 44 92")
        sun.set("ambient", "28 32 76")
    for sky in scene.iter("sky-box"):
        names = " ".join(f"motorica_night_{side}.jpg" for side in
            ["top", "bottom", "north", "south", "east", "west"])
        sky.set("texture", names)
        sky.set("sh-texture", names)


def create_night_sky(source_track: Path, destination: Path) -> None:
    sides = ["top", "bottom", "north", "south", "east", "west"]
    fallback = source_track / "skybox_top.jpg"
    for side in sides:
        original = source_track / f"skybox_{side}.jpg"
        if not original.is_file():
            original = fallback
        target = destination / f"motorica_night_{side}.jpg"
        shutil.copy2(original, target)
        night_tint(target)


def build_night_island(source: Path, overlay: Path) -> None:
    destination = overlay / "tracks" / "motorica_night_island"
    safe_replace_tree(source / "tracks" / "overworld", destination)
    configure_track_xml(
        destination / "track.xml", "Motorica Night Island",
        "MOTORICA RESEARCH LLC", internal=True,
    )

    tree = ET.parse(destination / "scene.xml")
    scene = tree.getroot()

    def obsolete(element: ET.Element) -> bool:
        model = element.attrib.get("model", "").lower()
        condition = element.attrib.get("if", "")
        return (
            "challenge" in element.attrib or
            "isLocked(" in condition or
            "lighthouse" in model or
            element.attrib.get("id") in {"RDoor", "RDoor.001"}
        )

    remove_matching_children(scene, obsolete)
    track = scene.find("track")
    if track is None:
        fail("overworld scene has no <track> node")

    challenge_positions = [
        ("-19.64 -2.87 30.22", "-6.1 -178.5 -1.2"),
        ("45.55 -3.71 121.05", "-4.8 -152.5 3.0"),
        ("-90.80 -0.05 186.99", "0.0 169.5 0.0"),
        ("88.73 -10.82 257.88", "0.0 36.6 0.0"),
        ("-19.66 -17.28 408.17", "0.0 36.6 0.0"),
        ("144.71 0.17 4.00", "0.0 36.6 0.0"),
    ]
    for index, (xyz, hpr) in enumerate(challenge_positions, start=1):
        ET.SubElement(track, "static-object", {
            "id": f"motorica_signal_point_{index}",
            "model": "crystal_ball.spm",
            "xyz": xyz,
            "hpr": hpr,
            "scale": "0.94 0.94 0.94",
            "challenge": "motorica_signal_circuit",
        })

    add_ufo(track, "motorica_ufo_west", "-115.0 52.0 206.0")
    add_ufo(track, "motorica_ufo_east", "126.0 64.0 264.0", "2.8 2.8 2.8")
    add_ufo(track, "motorica_ufo_core", "16.0 44.0 40.0", "1.9 1.9 1.9")
    add_animated_ufo(scene)
    make_scene_night(scene)

    starts = list(scene.iter("start"))
    if len(starts) >= 3:
        starts[0].set("x", "22.50")
        starts[0].set("y", "-4.10")
        starts[0].set("z", "18.20")
        starts[0].set("h", "128.00")

    # Rearrange non-physical library decorations without touching collision
    # meshes or the driveable surface.
    for index, library in enumerate(scene.iter("library")):
        if index % 4 != 0 or "xyz" not in library.attrib:
            continue
        x, y, z = (float(value) for value in library.attrib["xyz"].split())
        x += ((index % 7) - 3) * 2.4
        z += ((index % 5) - 2) * 3.1
        library.set("xyz", f"{x:.2f} {y:.2f} {z:.2f}")

    write_xml(tree, destination / "scene.xml")
    (destination / "scripting.as").write_text(
        "// Motorica Night Island intentionally uses engine-native challenge "
        "interaction only.\n", encoding="utf-8")

    for texture in ["grass.jpg", "grass2.jpg", "city_grass.png", "GrassTall.png"]:
        path = destination / texture
        if path.is_file():
            golden_grass(path)
    create_night_sky(source / "tracks" / "overworld", destination)
    screenshot = destination / "screenshot.jpg"
    if screenshot.is_file():
        night_tint(screenshot)

    legacy_notice = destination / "licence2.txt"
    if legacy_notice.is_file():
        legacy_notice.write_text(
            "\n".join(line.rstrip() for line in
                      legacy_notice.read_text(encoding="utf-8").splitlines()) +
            "\n",
            encoding="utf-8",
        )

    with (destination / "licenses.txt").open("a", encoding="utf-8") as output:
        output.write(
            "\nMotorica Night Island composition and derived color variants: "
            "MOTORICA RESEARCH LLC, 2026. Original asset licenses remain "
            "unchanged and are listed in this file.\n"
        )


def build_signal_circuit(source: Path, overlay: Path) -> None:
    destination = overlay / "tracks" / "motorica_signal_circuit"
    safe_replace_tree(source / "tracks" / "soccer_field", destination)
    configure_track_xml(
        destination / "track.xml", "Motorica Signal Circuit",
        "MOTORICA RESEARCH LLC", internal=False,
    )
    track_tree = ET.parse(destination / "track.xml")
    track_root = track_tree.getroot()
    track_root.set("music", "klabauter_dance.music")
    track_root.set("screenshot", "screenshot.jpg")
    write_xml(track_tree, destination / "track.xml")

    overworld = source / "tracks" / "overworld"
    for asset in [
        "bubble_solid_saucer.spm", "ufo_window.png",
        "crystal_ball.spm", "crystal_ball_halo.png",
    ]:
        shutil.copy2(overworld / asset, destination / asset)

    tree = ET.parse(destination / "scene.xml")
    scene = tree.getroot()

    def soccer_gameplay(element: ET.Element) -> bool:
        return (
            element.tag in {
                "checks", "item", "big-nitro", "small-nitro",
                "default-start", "start", "goal",
            } or
            element.attrib.get("id") in {"field_lining", "soccer_ball"}
        )

    remove_matching_children(scene, soccer_gameplay)
    track = scene.find("track")
    if track is None:
        fail("soccer-field scene has no <track> node")

    sections = build_signal_route()
    write_signal_quads(destination, sections)
    append_signal_race_nodes(scene, sections)

    add_ufo(track, "signal_ufo_start", "-28.0 30.0 22.0", "2.4 2.4 2.4")
    add_ufo(track, "signal_ufo_curve", "31.0 36.0 -32.0", "3.2 3.2 3.2")
    add_ufo(track, "signal_ufo_center", "2.0 27.0 -3.0", "1.8 1.8 1.8")
    make_scene_night(scene)
    write_xml(tree, destination / "scene.xml")

    for texture in ["racetrack_grass.jpg", "racetrack_red.jpg"]:
        path = destination / texture
        if path.is_file():
            golden_grass(path)
    for texture in ["racetrack_sky.jpg", "racetrack_stadium.jpg"]:
        path = destination / texture
        if path.is_file():
            night_tint(path)
    create_night_sky(source / "tracks" / "overworld", destination)
    screenshot = destination / "screenshot.jpg"
    create_signal_preview(screenshot, sections)

    with (destination / "licenses.txt").open("a", encoding="utf-8") as output:
        output.write(
            "\nMotorica Signal Circuit route, driveline, quads, preview and "
            "composition: MOTORICA RESEARCH LLC, 2026. The collision floor "
            "and perimeter derive from Soccer Field under the licenses above. "
            "Additional UFO and crystal-ball objects derive from Overworld; "
            "its license inventory follows.\n\n"
        )
        output.write((overworld / "licenses.txt").read_text(encoding="utf-8"))


def write_spm(path: Path, materials: list[str],
              buffers: list[tuple[int, list[tuple[float, float, float, float, float]],
                                  list[int]]]) -> None:
    """Write a small static SPM v1 mesh accepted by STK's native loader."""
    all_vertices = [vertex for _, vertices, _ in buffers for vertex in vertices]
    if not all_vertices:
        fail(f"Cannot write empty SPM: {path}")
    xs = [vertex[0] for vertex in all_vertices]
    ys = [vertex[1] for vertex in all_vertices]
    zs = [vertex[2] for vertex in all_vertices]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        output.write(b"SP")
        output.write(struct.pack("<B", (1 << 3) | 2))  # version 1, SPMN
        output.write(struct.pack("<B", 0))  # implicit up normal, white color
        output.write(struct.pack("<6f", min(xs), min(ys), min(zs),
                                 max(xs), max(ys), max(zs)))
        output.write(struct.pack("<H", len(materials)))
        for material in materials:
            encoded = material.encode("utf-8")
            if len(encoded) > 255:
                fail(f"SPM material name too long: {material}")
            output.write(struct.pack("<B", len(encoded)))
            output.write(encoded)
            output.write(b"\x00")  # no second UV texture
        output.write(struct.pack("<H", 1))  # one mesh sector
        output.write(struct.pack("<H", len(buffers)))
        for material_id, vertices, indices in buffers:
            output.write(struct.pack("<IIH", len(vertices), len(indices),
                                     material_id))
            for x, y, z, u, v in vertices:
                output.write(struct.pack("<3f", x, y, z))
                output.write(struct.pack("<ee", u, v))
            index_format = "B" if len(vertices) <= 255 else "H"
            output.write(struct.pack("<" + index_format * len(indices),
                                     *indices))


def add_box(vertices: list[tuple[float, float, float, float, float]],
            indices: list[int], center: tuple[float, float, float],
            size: tuple[float, float, float]) -> None:
    cx, cy, cz = center
    sx, sy, sz = (value / 2.0 for value in size)
    start = len(vertices)
    vertices.extend([
        (cx - sx, cy - sy, cz - sz, 0.0, 0.0),
        (cx + sx, cy - sy, cz - sz, 1.0, 0.0),
        (cx + sx, cy + sy, cz - sz, 1.0, 1.0),
        (cx - sx, cy + sy, cz - sz, 0.0, 1.0),
        (cx - sx, cy - sy, cz + sz, 0.0, 0.0),
        (cx + sx, cy - sy, cz + sz, 1.0, 0.0),
        (cx + sx, cy + sy, cz + sz, 1.0, 1.0),
        (cx - sx, cy + sy, cz + sz, 0.0, 1.0),
    ])
    faces = [
        (0, 2, 1, 0, 3, 2), (4, 5, 6, 4, 6, 7),
        (0, 1, 5, 0, 5, 4), (3, 7, 6, 3, 6, 2),
        (1, 2, 6, 1, 6, 5), (0, 4, 7, 0, 7, 3),
    ]
    for face in faces:
        indices.extend(start + index for index in face)


def build_signal_lab_track(overlay: Path) -> None:
    destination = overlay / "tracks" / "motorica_signal_lab"
    destination.mkdir(parents=True, exist_ok=True)
    sections = build_signal_route()

    road_vertices: list[tuple[float, float, float, float, float]] = []
    road_indices: list[int] = []
    for index, (left, right) in enumerate(sections):
        road_vertices.extend([
            (left[0], 0.06, left[2], 0.0, index / 8.0),
            (right[0], 0.06, right[2], 1.0, index / 8.0),
        ])
    for index in range(len(sections)):
        following = (index + 1) % len(sections)
        road_indices.extend([
            index * 2, following * 2, index * 2 + 1,
            index * 2 + 1, following * 2, following * 2 + 1,
        ])

    floor_vertices = [
        (-90.0, -0.12, -78.0, 0.0, 0.0),
        (90.0, -0.12, -78.0, 8.0, 0.0),
        (90.0, -0.12, 78.0, 8.0, 8.0),
        (-90.0, -0.12, 78.0, 0.0, 8.0),
    ]
    floor_indices = [0, 2, 1, 0, 3, 2]
    zone_vertices: list[tuple[float, float, float, float, float]] = []
    zone_indices: list[int] = []
    for center, size in [((-22.0, 0.08, 2.0), (20.0, 0.35, 15.0)),
                         ((8.0, 0.08, 3.0), (20.0, 0.35, 15.0)),
                         ((38.0, 0.08, 5.0), (20.0, 0.35, 15.0))]:
        add_box(zone_vertices, zone_indices, center, size)
    write_spm(destination / "signal_lab_track.spm",
              ["signal_road.png", "signal_floor.png", "signal_zone.png"],
              [(0, road_vertices, road_indices),
               (1, floor_vertices, floor_indices),
               (2, zone_vertices, zone_indices)])

    gate_vertices: list[tuple[float, float, float, float, float]] = []
    gate_indices: list[int] = []
    add_box(gate_vertices, gate_indices, (-6.6, 2.5, 0.0), (0.6, 5.0, 0.7))
    add_box(gate_vertices, gate_indices, (6.6, 2.5, 0.0), (0.6, 5.0, 0.7))
    add_box(gate_vertices, gate_indices, (0.0, 5.0, 0.0), (13.8, 0.6, 0.7))
    write_spm(destination / "signal_gate.spm", ["signal_neon.png"],
              [(0, gate_vertices, gate_indices)])

    panel_vertices: list[tuple[float, float, float, float, float]] = []
    panel_indices: list[int] = []
    add_box(panel_vertices, panel_indices, (0.0, 1.6, 0.0), (5.5, 3.2, 0.45))
    add_box(panel_vertices, panel_indices, (-3.0, 0.5, 0.0), (0.35, 1.0, 0.7))
    add_box(panel_vertices, panel_indices, (3.0, 0.5, 0.0), (0.35, 1.0, 0.7))
    write_spm(destination / "signal_panel.spm", ["signal_panel.png"],
              [(0, panel_vertices, panel_indices)])

    marker_vertices: list[tuple[float, float, float, float, float]] = []
    marker_indices: list[int] = []
    add_box(marker_vertices, marker_indices, (0.0, 0.55, 0.0),
            (0.34, 1.10, 0.34))
    add_box(marker_vertices, marker_indices, (0.0, 1.20, 0.0),
            (0.80, 0.20, 0.80))
    write_spm(destination / "signal_marker.spm", ["signal_neon.png"],
              [(0, marker_vertices, marker_indices)])

    write_signal_quads(destination, sections)
    scene = ET.Element("scene")
    track = ET.SubElement(scene, "track", {
        "model": "signal_lab_track.spm", "x": "0", "y": "0", "z": "0"
    })
    gate_points = [
        (0.0, 62.0), (-42.0, 43.0), (-50.0, 10.0), (-61.0, -22.0),
        (-34.0, -49.0), (0.0, -48.0), (25.0, -38.0), (56.0, -28.0),
        (54.0, 8.0), (62.0, 33.0), (31.0, 55.0), (12.0, 65.0),
    ]
    for index, (x, z) in enumerate(gate_points):
        next_x, next_z = gate_points[(index + 1) % len(gate_points)]
        heading = math.degrees(math.atan2(next_x - x, next_z - z))
        ET.SubElement(track, "static-object", {
            "id": f"signal_gate_{index + 1}", "model": "signal_gate.spm",
            "xyz": f"{x:.2f} 0.08 {z:.2f}",
            "hpr": f"0.0 {heading:.2f} 0.0", "scale": "1 1 1",
            "interaction": "ghost", "skeletal-animation": "false",
        })
    for index, (x, z, heading) in enumerate([
            (-22.0, 2.0, 90.0), (8.0, 3.0, 90.0), (38.0, 5.0, 90.0)]):
        ET.SubElement(track, "static-object", {
            "id": f"exercise_panel_{index + 1}", "model": "signal_panel.spm",
            "xyz": f"{x:.2f} 0.26 {z:.2f}",
            "hpr": f"0.0 {heading:.2f} 0.0", "scale": "1 1 1",
            "interaction": "ghost", "skeletal-animation": "false",
        })
    ET.SubElement(scene, "sun", {
        "fog": "true", "fog-color": "5 8 26", "fog-max": "0.72",
        "fog-start": "75", "fog-end": "330", "xyz": "-80 210 160",
        "sun-diffuse": "54 72 130", "ambient": "38 46 92",
    })
    ET.SubElement(scene, "sky-color", {"rgb": "4 6 20"})
    ET.SubElement(scene, "camera", {"far": "500"})
    # A lap group plus ordered activation lines prevents shortcut completion
    # and keeps STK's track-sector/ranking logic well-defined.
    append_signal_race_nodes(scene, sections)
    ET.SubElement(scene, "default-start", {
        "karts-per-row": "1", "forwards-distance": "2.0",
        "sidewards-distance": "3.0", "upwards-distance": "0.2"
    })
    ET.SubElement(scene, "start", {
        "x": "0.0", "y": "0.30", "z": "56.0", "h": "-115.0"
    })
    write_xml(ET.ElementTree(scene), destination / "scene.xml")

    write_xml(ET.ElementTree(ET.Element("track", {
        "name": "Motorica Signal Lab", "version": "7", "groups": "motorica",
        "designer": "MOTORICA RESEARCH LLC",
        "music": "motorica_signal_lab.music",
        "screenshot": "screenshot.jpg", "smooth-normals": "false",
        "default-number-of-laps": "3", "reverse": "N", "clouds": "N",
        "is-during-day": "N", "shadows": "Y",
    })), destination / "track.xml")
    (destination / "materials.xml").write_text(
        '<?xml version="1.0"?>\n<materials>\n'
        '  <material name="signal_neon.png" shader="unlit" ignore="Y"/>\n'
        '  <material name="signal_panel.png" shader="unlit" ignore="Y"/>\n'
        '  <material name="signal_floor.png"/>\n'
        '  <material name="signal_road.png"/>\n'
        '  <material name="signal_zone.png" shader="unlit"/>\n'
        '</materials>\n', encoding="utf-8")

    def texture(name: str, base: tuple[int, int, int],
                accent: tuple[int, int, int]) -> None:
        image = Image.new("RGB", (256, 256), base)
        draw = ImageDraw.Draw(image)
        for step in range(0, 256, 32):
            draw.line((step, 0, step, 255), fill=accent, width=3)
            draw.line((0, step, 255, step), fill=accent, width=3)
        image.save(destination / name)
    texture("signal_road.png", (16, 22, 42), (52, 73, 122))
    texture("signal_floor.png", (5, 8, 20), (14, 21, 42))
    texture("signal_zone.png", (28, 12, 48), (190, 66, 255))
    texture("signal_neon.png", (25, 12, 42), (193, 255, 56))
    texture("signal_panel.png", (7, 29, 46), (0, 222, 255))
    create_signal_preview(destination / "screenshot.jpg", sections)
    preview = Image.open(destination / "screenshot.jpg").resize((512, 288))
    preview.save(destination / "minimap.png")
    (destination / "scripting.as").write_text(
        "// Signal Lab uses only engine-native declarative race data.\n",
        encoding="utf-8")
    (destination / "licenses.txt").write_text(
        "Motorica Signal Lab geometry, route, textures, preview and layout: "
        "MOTORICA RESEARCH LLC, 2026. CC BY-SA 4.0.\n"
        "Motorica Signal Lab soundtrack: MOTORICA RESEARCH LLC, 2026. "
        "CC BY-SA 4.0.\n",
        encoding="utf-8")


def build_signal_lab_soundtrack(overlay: Path) -> None:
    """Generate an original deterministic ambient loop for Signal Lab."""
    destination = overlay / "music"
    destination.mkdir(parents=True, exist_ok=True)
    oggenc = shutil.which("oggenc")
    ffmpeg = shutil.which("ffmpeg")
    if oggenc is None and ffmpeg is None:
        fail("oggenc or ffmpeg is required to generate the Signal Lab soundtrack")

    sample_rate = 44100
    duration_seconds = 40
    with tempfile.TemporaryDirectory(prefix="motorica-signal-audio-") as temp:
        wav_path = Path(temp) / "motorica_signal_lab.wav"
        with wave.open(str(wav_path), "wb") as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            block = bytearray()
            for index in range(sample_rate * duration_seconds):
                time = index / sample_rate
                pulse_time = time % 4.0
                pulse = math.exp(-pulse_time * 5.0) * math.sin(
                    2.0 * math.pi * 440.0 * time)
                sweep = math.sin(2.0 * math.pi *
                    (70.0 + 18.0 * math.sin(time * math.pi / 10.0)) * time)
                carrier = math.sin(2.0 * math.pi * 110.0 * time)
                shimmer = math.sin(2.0 * math.pi * 220.0 * time +
                                   0.8 * math.sin(time * 0.7))
                value = 0.12 * carrier + 0.07 * sweep + 0.045 * shimmer + \
                        0.08 * pulse
                pan = 0.15 * math.sin(time * 0.45)
                left = max(-1.0, min(1.0, value * (1.0 - pan)))
                right = max(-1.0, min(1.0, value * (1.0 + pan)))
                block.extend(struct.pack("<hh", int(left * 32767),
                                         int(right * 32767)))
                if len(block) >= 16384:
                    output.writeframesraw(block)
                    block.clear()
            if block:
                output.writeframesraw(block)
        ogg_path = destination / "motorica_signal_lab.ogg"
        if oggenc is not None:
            subprocess.run([
                oggenc, "-Q", "-q", "4", "-o", str(ogg_path),
                str(wav_path),
            ], check=True)
        else:
            subprocess.run([
                ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path),
                "-c:a", "libvorbis", "-q:a", "4", str(ogg_path),
            ], check=True)

    (destination / "motorica_signal_lab.music").write_text(
        '<?xml version="1.0"?>\n'
        '<music title="Motorica Signal Lab"\n'
        '       composer="MOTORICA RESEARCH LLC"\n'
        '       gain="0.78"\n'
        '       file="motorica_signal_lab.ogg"/>\n',
        encoding="utf-8")
    (destination / "motorica_signal_lab_license.txt").write_text(
        "Motorica Signal Lab soundtrack: MOTORICA RESEARCH LLC, 2026. "
        "CC BY-SA 4.0.\n", encoding="utf-8")


def build_signal_pilot(overlay: Path) -> None:
    destination = overlay / "karts" / "motorica_signal_pilot"
    destination.mkdir(parents=True, exist_ok=True)
    body_vertices: list[tuple[float, float, float, float, float]] = []
    body_indices: list[int] = []
    # Wide centre fuselage plus four separated hover modules make a silhouette
    # that cannot be confused with a wheeled upstream kart.
    add_box(body_vertices, body_indices, (0.0, 0.34, 0.0), (1.15, 0.38, 1.75))
    add_box(body_vertices, body_indices, (0.0, 0.58, 0.28), (0.82, 0.30, 0.72))
    add_box(body_vertices, body_indices, (-0.92, 0.22, 0.18), (0.46, 0.32, 1.42))
    add_box(body_vertices, body_indices, (0.92, 0.22, 0.18), (0.46, 0.32, 1.42))
    add_box(body_vertices, body_indices, (-0.72, 0.28, -0.72), (0.34, 0.25, 0.55))
    add_box(body_vertices, body_indices, (0.72, 0.28, -0.72), (0.34, 0.25, 0.55))
    add_box(body_vertices, body_indices, (0.0, 0.91, -0.05), (0.62, 0.55, 0.52))
    add_box(body_vertices, body_indices, (0.0, 0.94, 0.24), (0.56, 0.20, 0.08))
    write_spm(destination / "signal_pilot.spm", ["signal_pilot.png"],
              [(0, body_vertices, body_indices)])
    (destination / "kart.xml").write_text(
        '<?xml version="1.0"?>\n'
        '<kart name="Signal Pilot" version="3" model-file="signal_pilot.spm"\n'
        '      icon-file="signal_pilot_icon.png"\n'
        '      minimap-icon-file="signal_pilot_icon.png"\n'
        '      shadow-file="signal_pilot_shadow.png" type="medium"\n'
        '      groups="motorica" rgb="0.18 0.88 1.00">\n'
        '  <sounds engine="small"/>\n'
        '  <animations left="0" straight="0" right="0"/>\n'
        '  <nitro-emitter>\n'
        '    <nitro-emitter-a position="-0.72 0.28 -1.02"/>\n'
        '    <nitro-emitter-b position="0.72 0.28 -1.02"/>\n'
        '  </nitro-emitter>\n'
        '</kart>\n', encoding="utf-8")
    texture = Image.new("RGB", (256, 256), (7, 16, 32))
    draw = ImageDraw.Draw(texture)
    draw.rounded_rectangle((16, 20, 240, 236), 28, fill=(26, 49, 82),
                           outline=(0, 222, 255), width=12)
    draw.polygon([(128, 34), (222, 206), (128, 165), (34, 206)],
                 fill=(190, 66, 255), outline=(193, 255, 56))
    texture.save(destination / "signal_pilot.png")
    icon = Image.new("RGBA", (256, 256), (4, 8, 20, 255))
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((20, 82, 236, 178), 36, fill=(22, 46, 78),
                           outline=(0, 222, 255), width=8)
    draw.rounded_rectangle((2, 98, 64, 204), 24, fill=(190, 66, 255),
                           outline=(193, 255, 56), width=6)
    draw.rounded_rectangle((192, 98, 254, 204), 24, fill=(190, 66, 255),
                           outline=(193, 255, 56), width=6)
    draw.polygon([(128, 42), (174, 132), (82, 132)], fill=(193, 255, 56))
    icon.save(destination / "signal_pilot_icon.png")
    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((18, 70, 238, 205), fill=(0, 0, 0, 150))
    shadow.save(destination / "signal_pilot_shadow.png")
    (destination / "licenses.txt").write_text(
        "Signal Pilot model, hover silhouette, textures, icon and shadow: "
        "MOTORICA RESEARCH LLC, 2026. CC BY-SA 4.0.\n",
        encoding="utf-8")


def write_training_challenges(overlay: Path) -> None:
    challenge_dir = overlay / "challenges"
    challenge_dir.mkdir(parents=True, exist_ok=True)
    for challenge_id, laps in [
            ("motorica_precision", 1),
            ("motorica_reaction", 3),
            ("motorica_signal_hold", 2)]:
        challenge = f'''<?xml version="1.0"?>
<challenge version="3">
  <unlock_list list="false"/>
  <track id="motorica_signal_lab" laps="{laps}" reverse="false"/>
  <mode major="single" minor="quickrace"/>
  <requirements trophies="0"/>
  <best><karts number="1"/><requirements position="1"/></best>
  <hard><karts number="1"/><requirements position="1"/></hard>
  <medium><karts number="1"/><requirements position="1"/></medium>
  <easy><karts number="1"/><requirements position="1"/></easy>
</challenge>
'''
        (challenge_dir / f"{challenge_id}.challenge").write_text(
            challenge, encoding="utf-8")


def write_challenge(overlay: Path) -> None:
    challenge_dir = overlay / "challenges"
    challenge_dir.mkdir(parents=True, exist_ok=True)
    challenge = """<?xml version="1.0"?>
<challenge version="3">
  <unlock_list list="false"/>
  <track id="motorica_signal_circuit" laps="3" reverse="false"/>
  <mode major="single" minor="quickrace"/>
  <requirements trophies="0"/>
  <best><karts number="8" aiIdent="motorica_kiki"/><requirements position="1"/></best>
  <hard><karts number="8" aiIdent="motorica_kiki"/><requirements position="1"/></hard>
  <medium><karts number="8" aiIdent="motorica_kiki"/><requirements position="1"/></medium>
  <easy><karts number="8" aiIdent="motorica_kiki"/><requirements position="1"/></easy>
</challenge>
"""
    (challenge_dir / "motorica_signal_circuit.challenge").write_text(
        challenge, encoding="utf-8")


def write_overlay_notes(overlay: Path) -> None:
    notes = """# Motorica standalone asset overlay

This directory is the tracked source of the permanent Motorica Training Hub
gameplay content. It is derived from the compatible `stk-assets` checkout and
keeps each upstream `licenses.txt` file next to the reused assets.

- `motorica_signal_pilot`: original static hover vehicle geometry with four
  outboard hover modules, a visor pilot and Motorica-only materials.
- `motorica_signal_lab`: original generated track mesh, waveform route,
  driveline, quads, checkpoints, twelve neon gates and three exercise zones.
- `motorica_signal_lab.music/.ogg`: original deterministic ambient soundtrack.
- `motorica_precision`, `motorica_reaction`, `motorica_signal_hold`: three
  independent training definitions sharing only the purpose-built Lab.

Regenerate intentionally with `tools/motorica_assets/build_assets.py overlay`.
Never edit `build-ios-assets` as a source of truth.
"""
    (overlay.parent / "README.md").write_text(notes, encoding="utf-8")


def build_overlay(source: Path) -> None:
    verify_source(source)
    if OVERLAY_ROOT.exists():
        shutil.rmtree(OVERLAY_ROOT)
    OVERLAY_ROOT.mkdir(parents=True)
    build_signal_pilot(OVERLAY_ROOT)
    build_signal_lab_track(OVERLAY_ROOT)
    build_signal_lab_soundtrack(OVERLAY_ROOT)
    write_training_challenges(OVERLAY_ROOT)
    write_overlay_notes(OVERLAY_ROOT)


def copy_overlay(base_data: Path) -> None:
    for relative in [
        Path("karts/motorica_signal_pilot"),
        Path("tracks/motorica_signal_lab"),
    ]:
        destination = base_data / relative
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(OVERLAY_ROOT / relative, destination)
    for filename in ["motorica_signal_lab.music", "motorica_signal_lab.ogg",
                     "motorica_signal_lab_license.txt"]:
        destination = base_data / "music" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OVERLAY_ROOT / "music" / filename, destination)
    for challenge in ["motorica_precision", "motorica_reaction",
                      "motorica_signal_hold"]:
        shutil.copy2(
            OVERLAY_ROOT / "challenges" / f"{challenge}.challenge",
            base_data / "challenges" / f"{challenge}.challenge",
        )


def build_base_assets(mobile_base: Path, output: Path, source: Path) -> None:
    if not mobile_base.is_dir():
        fail(f"Mobile base does not exist: {mobile_base}")
    safe_replace_tree(mobile_base, output)

    # Keep only content reachable from the permanent standalone experience.
    # Upstream challenges, grand prix and replays reference tracks that are
    # intentionally absent from this small IPA.
    for directory in [
        output / "tracks",
        output / "karts",
        output / "challenges",
        output / "grandprix",
        output / "replay",
    ]:
        shutil.rmtree(directory)
        directory.mkdir(parents=True)
    copy_overlay(output)

    # The downloaded package intentionally contains no executable code and
    # the minimal standalone catalog intentionally contains no upstream story
    # progression.  Keep the original declarative challenge/GP/replay catalog
    # in a separate, reviewed IPA directory. FileManager exposes this directory
    # only while the app is in Motorica Start mode with a validated full asset
    # package; a direct icon launch continues to see only the Motorica catalog.
    full_catalog = output / "motorica-start-full"
    for name in ["challenges", "grandprix", "replay"]:
        source_directory = REPO_ROOT / "data" / name
        if not source_directory.is_dir():
            fail(f"Full catalog source is missing: {source_directory}")
        shutil.copytree(source_directory, full_catalog / name)

    # These screens live with the reviewed application source rather than the
    # upstream stk-assets checkout. Always inject them into the generated
    # minimal IPA tree; otherwise the native Hub screen exists in the binary
    # but fatally fails when GUIEngine tries to load its layout on first launch.
    motorica_screens = [
        "motorica_hub.stkgui", "motorica_exercise.stkgui",
        "motorica_history.stkgui", "motorica_about.stkgui",
    ]
    screen_directory = output / "gui" / "screens"
    screen_directory.mkdir(parents=True, exist_ok=True)
    for name in motorica_screens:
        source_screen = REPO_ROOT / "data" / "gui" / "screens" / name
        if not source_screen.is_file():
            fail(f"Motorica GUI screen is missing: {source_screen}")
        shutil.copy2(source_screen, screen_directory / name)
    for name in motorica_screens:
        if not (screen_directory / name).is_file():
            fail(f"Generated IPA assets are missing Motorica GUI screen: {name}")

    for relative in [
        Path("karts/motorica_signal_pilot/licenses.txt"),
        Path("tracks/motorica_signal_lab/licenses.txt"),
        Path("music/motorica_signal_lab_license.txt"),
    ]:
        if not (output / relative).is_file():
            fail(f"Motorica asset is missing its license inventory: {relative}")

    packaged = output / "packaged-scripts"
    packaged.mkdir(parents=True, exist_ok=True)
    script_count = 0
    for script in sorted(source.rglob("*.as")):
        relative = script.relative_to(source)
        target = packaged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script, target)
        script_count += 1
    if script_count != 24:
        fail(f"Expected 24 packaged AngelScript files, found {script_count}")

    # Track-local GPU shaders are executable source too. They must never come
    # from the downloaded ZIP. Package them in the reviewed application and
    # let SPShaderManager resolve them through the same pinned registry.
    shader_count = 0
    for shader_suffix in ["*.frag", "*.vert"]:
        for shader in sorted(source.rglob(shader_suffix)):
            relative = shader.relative_to(source)
            target = packaged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shader, target)
            shader_count += 1
    if shader_count == 0:
        fail("Expected at least one packaged track-local shader")

    motorica_script = packaged / "tracks" / "motorica_signal_lab" / "scripting.as"
    motorica_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        OVERLAY_ROOT / "tracks" / "motorica_signal_lab" / "scripting.as",
        motorica_script,
    )

    # The base install must not advertise the upstream catalog through track
    # or kart search paths, even when a full package remains installed.
    tracks = sorted(path.name for path in (output / "tracks").iterdir())
    karts = sorted(path.name for path in (output / "karts").iterdir())
    if tracks != ["motorica_signal_lab"]:
        fail(f"Unexpected base tracks: {tracks}")
    if karts != ["motorica_signal_pilot"]:
        fail(f"Unexpected base karts: {karts}")


def validate_remote_path(relative: PurePosixPath) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        fail(f"Unsafe archive path: {relative}")
    if relative.suffix.lower() not in REMOTE_ALLOWED_EXTENSIONS:
        fail(f"Disallowed remote asset extension: {relative}")


def build_full_archive(source: Path, dist: Path) -> tuple[Path, int, str, list[str]]:
    dist.mkdir(parents=True, exist_ok=True)
    archive = dist / ARCHIVE_NAME
    if archive.exists():
        archive.unlink()

    included: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        relative = PurePosixPath(path.relative_to(source).as_posix())
        if relative.suffix.lower() in {".as", ".frag", ".b3d", ".xcf", ".rtf"}:
            continue
        validate_remote_path(relative)
        included.append(path)

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as output:
        for path in included:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo.from_file(path, arcname=relative)
            info.external_attr &= ~(0o170000 << 16)
            output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)

    digest = hashlib.sha256()
    size = 0
    with archive.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    sha256 = digest.hexdigest()

    with zipfile.ZipFile(archive) as check:
        entries = check.infolist()
        names = [entry.filename for entry in entries]
        for entry in entries:
            validate_remote_path(PurePosixPath(entry.filename))
            unix_type = (entry.external_attr >> 16) & 0o170000
            if unix_type == 0o120000:
                fail(f"Remote archive contains a symbolic link: {entry.filename}")
        if any(name.lower().endswith(".as") for name in names):
            fail("Remote archive unexpectedly contains AngelScript")
    return archive, size, sha256, [path.relative_to(source).as_posix()
                                   for path in included]


def write_manifest(dist: Path, size: int, sha256: str, files: list[str]) -> None:
    manifest = {
        "schemaVersion": 1,
        "assetVersion": ASSET_VERSION,
        "minimumAppBuild": MINIMUM_APP_BUILD,
        "archiveURL": ARCHIVE_URL,
        "sizeBytes": size,
        "sha256": sha256,
        "marker": MARKER,
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (dist / MANIFEST_NAME).write_text(manifest_text, encoding="utf-8")
    (dist / CHECKSUM_NAME).write_text(
        f"{sha256}  {ARCHIVE_NAME}\n", encoding="utf-8")
    (dist / "motorica-stk-full-assets-1.files.txt").write_text(
        "\n".join(files) + "\n", encoding="utf-8")
    (REPO_ROOT / "data" / MANIFEST_NAME).write_text(manifest_text, encoding="utf-8")

    header = f'''// Generated by tools/motorica_assets/build_assets.py. Do not edit.
#ifndef HEADER_MOTORICA_ASSETS_MANIFEST_HPP
#define HEADER_MOTORICA_ASSETS_MANIFEST_HPP

#include <cstdint>

namespace MotoricaAssetsManifest
{{
static const int SCHEMA_VERSION = 1;
static const char* const ASSET_VERSION = "{ASSET_VERSION}";
static const int MINIMUM_APP_BUILD = {MINIMUM_APP_BUILD};
static const char* const ARCHIVE_URL = "{ARCHIVE_URL}";
static const uint64_t SIZE_BYTES = {size}ull;
static const char* const SHA256 = "{sha256}";
static const char* const MARKER = "{MARKER}";
}}

#endif
'''
    (REPO_ROOT / "src" / "utils" / "motorica_assets_manifest.hpp").write_text(
        header, encoding="utf-8")

    size_header = f'''// Generated by tools/motorica_assets/build_assets.py. Do not edit.
#ifndef HEADER_DOWNLOAD_ASSETS_SIZE_HPP
#define HEADER_DOWNLOAD_ASSETS_SIZE_HPP
inline unsigned long long getDownloadAssetsSize()
{{
    return {size}ull;
}}
#endif
'''
    (REPO_ROOT / "src" / "utils" / "download_assets_size.hpp").write_text(
        size_header, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["overlay", "base", "package", "all"])
    parser.add_argument("--source-assets", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--mobile-base", type=Path, default=DEFAULT_MOBILE_BASE)
    parser.add_argument("--base-output", type=Path, default=DEFAULT_BASE_OUTPUT)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()

    source = args.source_assets.resolve()
    verify_source(source)
    if args.command in {"overlay", "all"}:
        build_overlay(source)
        print(f"Overlay: {OVERLAY_ROOT.parent}")
    if args.command in {"base", "package", "all"}:
        if not OVERLAY_ROOT.is_dir():
            fail("Generate the tracked overlay before packaging")
        build_base_assets(args.mobile_base.resolve(), args.base_output.resolve(), source)
        print(f"Base assets: {args.base_output.resolve()}")
    if args.command in {"package", "all"}:
        archive, size, digest, files = build_full_archive(source, args.dist.resolve())
        write_manifest(args.dist.resolve(), size, digest, files)
        print(f"Archive: {archive} ({size} bytes)")
        print(f"SHA-256: {digest}")
        print(f"Remote files: {len(files)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
