from pathlib import Path
import subprocess, shutil, hashlib, json

r = Path(__file__).resolve().parent
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
source = repo / 'iosApp/FluxaraResources'
app = repo / 'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app'
device = '3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
track = 'fluxara-user-ski-dash'
shutil.copy2(source / 'tracks' / track / 'screenshot.png', app / 'data/tracks' / track / 'screenshot.png')
subprocess.run(['/bin/sh', str(repo / 'cmake/PrepareFluxaraCampaignPreviews.sh'), str(source / 'tracks'), str(source / 'fluxara-campaign.xml'), str(app / 'data/gui/fluxara/campaign-previews')], check=True)
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
subprocess.run(['xcrun', 'simctl', 'install', device, str(app)], check=True)
installed = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', device, 'io.fluxara.drift', 'app'], text=True).strip())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
thumb = Path('data/gui/fluxara/campaign-previews') / (track + '.jpg')
assert sha(app / thumb) == sha(installed / thumb)
assert sha(source / 'tracks' / track / 'screenshot.png') == sha(installed / 'data/tracks' / track / 'screenshot.png')
(r / 'preview-bundle-verification.json').write_text(json.dumps({'resourceOnlyRefresh': True, 'sourceTrackPreviewBuiltInstalledExact': True, 'campaignThumbnailBuiltInstalledExact': True, 'thumbnailBytes': (app / thumb).stat().st_size, 'thumbnailSha256': sha(app / thumb), 'previewEvidence': str(r / 'preview-update.json')}, indent=2))
print('PREVIEW_RESOURCE_REFRESH_VERIFIED')
