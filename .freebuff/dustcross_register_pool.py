# Register pass-B results in FLUXARA_TRACK_ASSET_POOL.json + hashes.
import json, hashlib, os, datetime

ROOT = "/Users/motoricallc/Downloads/fluxara-drift"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

work = f"{ROOT}/track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend"
pool_path = f"{ROOT}/FLUXARA_TRACK_ASSET_POOL.json"
with open(pool_path) as f:
    pool = json.load(f)

have = {o["id"] for o in pool["objects"]}
new_entries = [
    {
        "id": "dustcross-workfile-v1",
        "kind": "object-group",
        "displayName": "Dust Cross split combat rework workfile (pass B large forms)",
        "sourceMap": "fluxara-user-dust-cross-split-combat",
        "reuseTier": "authored",
        "categories": ["canyon", "arena", "dirt"],
        "source": "track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend",
        "uses": [{
            "trackId": "fluxara-user-dust-cross-split-combat",
            "status": "pass B large forms placed: mesas x3 (pack SnowCliff 01-03, reskin red sandstone), perimeter barriers x150 (pack ArenaBarrier), waterfall (pack SplitFalls flows reskinned), bridges (pack CanyonArchedBridge + posts/rails/ends), pennants/bunting/chevrons/grandstands/tents (pack + authored boxes), ramps x2 (authored bmesh)",
            "adaptation": "Donor course hidden in DonorLegacy_Stage_HIDDEN; course SPM underlay protected read-only with locked transforms"
        }],
        "dependencies": [
            "ski-dash-canyon-mesa-0-rock", "ski-dash-canyon-mesa-1-rock", "ski-dash-canyon-mesa-2-rock",
            "ski-dash-red-white-concrete-barrier", "canyon-split-waterfalls", "canyon-arched-bridge",
            "canyon-bridge-assembly", "canyon-bridge-pennants", "ski-dash-bunting-span-v1",
            "ski-dash-chevron-board-v1"
        ],
        "file": {"path": "track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend",
                 "bytes": os.path.getsize(work), "sha256": sha(work)},
        "evidence": [
            "Control frames frame-001..009 in track-reworks/dust-cross-split-combat/progress/",
            "Donor file hash unchanged: 21fc45d2a2d20bfab902df5ccf4d18e36d7d5d03a0bbe5b67abaa5834f5b9793"
        ]
    },
    {
        "id": "dustcross-ramp-jump-v1",
        "kind": "prop",
        "displayName": "Dust Cross authored ramp jump with chevron face and start gate",
        "sourceMap": "fluxara-user-dust-cross-split-combat",
        "reuseTier": "authored",
        "categories": ["arena", "trackside"],
        "source": "track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend#Object/DC_RampA",
        "uses": [{
            "trackId": "fluxara-user-dust-cross-split-combat",
            "status": "placed x2 (DC_RampA north-center, DC_RampB east rotated -90deg)",
            "adaptation": "bmesh wedge, metal grid deck material DC_Ramp_MetalGrid, chevron front DC_Chevron_Yellow, frame DC_Ramp_Frame, gate posts DC_Ramp_Gate"
        }],
        "dependencies": [],
        "evidence": ["Per refs 01: two grid ramps with chevron faces and start gates over the arena"]
    },
    {
        "id": "dustcross-sandstone-reskin-v1",
        "kind": "material",
        "displayName": "Dust Cross red sandstone reskin materials (A/B/cap)",
        "sourceMap": "fluxara-user-dust-cross-split-combat",
        "reuseTier": "authored",
        "categories": ["canyon", "cliff"],
        "source": "track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend#Material/DC_Sandstone_Red_A",
        "uses": [{
            "trackId": "fluxara-user-dust-cross-split-combat",
            "status": "applied to three mesa rock pairs and waterfall shelf",
            "adaptation": "Flat-color placeholder for pass B; texture pass will replace with seamless sandstone albedo (3x3 rule)"
        }],
        "dependencies": ["canyon-main-atlas"],
        "evidence": ["refs 02/03/04 palette: terracotta red rock, pale sand cap"]
    },
]

added = 0
for e in new_entries:
    if e["id"] not in have:
        pool["objects"].append(e)
        added += 1

if "fluxara-user-dust-cross-split-combat" not in [t["trackId"] for t in pool["sourceTracks"]]:
    pool["sourceTracks"].append({
        "trackId": "fluxara-user-dust-cross-split-combat",
        "role": "third map / current target",
        "evidence": "iosApp/FluxaraResources/tracks/fluxara-user-dust-cross-split-combat and track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend"
    })

pool["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
with open(pool_path, "w") as f:
    json.dump(pool, f, indent=2, ensure_ascii=False)
print(f"pool updated: +{added} entries, sourceTracks now: {[t['trackId'] for t in pool['sourceTracks']]}")
print("workfile sha256:", sha(work)[:16], "…")
print("SCRIPT_OK")
