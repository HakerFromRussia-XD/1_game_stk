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
import sys
import tempfile
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
    """Create a Motorica-only circuit on the open soccer-field surface.

    The field supplies only the licensed collision floor and perimeter.  The
    route, spline sampling, variable-width cross sections, quads and graph are
    generated here and do not reuse another STK race's driveline.
    """
    controls = [
        (0.0, 45.0), (-24.0, 40.0), (-35.0, 20.0), (-21.0, -2.0),
        (-35.0, -29.0), (-18.0, -49.0), (5.0, -43.0),
        (29.0, -50.0), (36.0, -25.0), (21.0, -4.0),
        (36.0, 19.0), (24.0, 41.0),
    ]
    samples_per_segment = 6
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
                "model": "crystal_ball.spm",
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

- `motorica_kiki`: separate kart ID and derived palette; original Kiki remains untouched.
- `motorica_night_island`: standalone overworld with a Motorica-only challenge ID.
- `motorica_signal_circuit`: generated 72-section closed route with custom
  driveline, quads, checkpoints, starts, night styling and UFO decorations;
  it is the fixed three-lap race used by all six island points.

Regenerate intentionally with `tools/motorica_assets/build_assets.py overlay`.
Never edit `build-ios-assets` as a source of truth.
"""
    (overlay.parent / "README.md").write_text(notes, encoding="utf-8")


def build_overlay(source: Path) -> None:
    verify_source(source)
    if OVERLAY_ROOT.exists():
        shutil.rmtree(OVERLAY_ROOT)
    OVERLAY_ROOT.mkdir(parents=True)
    build_motorica_kiki(source, OVERLAY_ROOT)
    build_night_island(source, OVERLAY_ROOT)
    build_signal_circuit(source, OVERLAY_ROOT)
    write_challenge(OVERLAY_ROOT)
    write_overlay_notes(OVERLAY_ROOT)


def copy_overlay(base_data: Path) -> None:
    for relative in [
        Path("karts/motorica_kiki"),
        Path("tracks/motorica_night_island"),
        Path("tracks/motorica_signal_circuit"),
    ]:
        destination = base_data / relative
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(OVERLAY_ROOT / relative, destination)
    shutil.copy2(
        OVERLAY_ROOT / "challenges" / "motorica_signal_circuit.challenge",
        base_data / "challenges" / "motorica_signal_circuit.challenge",
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

    # These screens live with the reviewed application source rather than the
    # upstream stk-assets checkout. Always inject them into the generated
    # minimal IPA tree; otherwise the native Hub screen exists in the binary
    # but fatally fails when GUIEngine tries to load its layout on first launch.
    motorica_screens = ["motorica_hub.stkgui", "motorica_about.stkgui"]
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
        Path("karts/motorica_kiki/licenses.txt"),
        Path("tracks/motorica_night_island/licenses.txt"),
        Path("tracks/motorica_signal_circuit/licenses.txt"),
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

    motorica_script = packaged / "tracks" / "motorica_night_island" / "scripting.as"
    motorica_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        OVERLAY_ROOT / "tracks" / "motorica_night_island" / "scripting.as",
        motorica_script,
    )

    # The base install must not advertise the upstream catalog through track
    # or kart search paths, even when a full package remains installed.
    tracks = sorted(path.name for path in (output / "tracks").iterdir())
    karts = sorted(path.name for path in (output / "karts").iterdir())
    if tracks != ["motorica_night_island", "motorica_signal_circuit"]:
        fail(f"Unexpected base tracks: {tracks}")
    if karts != ["motorica_kiki"]:
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
    parser.add_argument("command", choices=["overlay", "package", "all"])
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
    if args.command in {"package", "all"}:
        if not OVERLAY_ROOT.is_dir():
            fail("Generate the tracked overlay before packaging")
        build_base_assets(args.mobile_base.resolve(), args.base_output.resolve(), source)
        archive, size, digest, files = build_full_archive(source, args.dist.resolve())
        write_manifest(args.dist.resolve(), size, digest, files)
        print(f"Base assets: {args.base_output.resolve()}")
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
