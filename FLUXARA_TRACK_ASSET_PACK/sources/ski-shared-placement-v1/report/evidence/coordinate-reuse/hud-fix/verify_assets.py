from pathlib import Path
import subprocess, hashlib, json
from PIL import Image

r = Path(__file__).resolve().parent
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
app = repo / 'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app'
installed = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', '3B2F19DC-4F76-4F61-9F8D-D5E914A6D123', 'io.fluxara.drift', 'app'], text=True).strip())
rows = []
for name, size in [('counter-small.png', (66, 43)), ('counter-time.png', (120, 43)), ('minimap-panel.png', (46, 60))]:
    paths = [repo / 'iosApp/FluxaraResources/gui/fluxara/hud' / name, app / 'data/gui/fluxara/hud' / name, installed / 'data/gui/fluxara/hud' / name]
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    assert len(set(hashes)) == 1, name
    im = Image.open(paths[0]).convert('RGBA')
    assert im.size == size, (name, im.size)
    assert im.getpixel((im.width // 2, im.height // 2))[3] == 122
    rows.append({'name': name, 'dimensions': size, 'sha256': hashes[0], 'sourceBuiltInstalledExact': True, 'centerAlpha': 122})
(r / 'asset-verification.json').write_text(json.dumps(rows, indent=2))
print('COMPACT_HUD_RGBA_VERIFIED', len(rows))
