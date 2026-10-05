from pathlib import Path
import json, shutil, hashlib, html

r = Path(__file__).resolve().parent
root = r.parent.parent
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
pack = repo / 'FLUXARA_TRACK_ASSET_PACK'
final = r.parent / 'fluxara-user-ski-dash-final'
report = final / 'report'
report.mkdir(exist_ok=True)
load = lambda n: json.loads((r / n).read_text())
info = lambda p: {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
a = load('ski-extraction.json')
live = load('live-verification.json')
window = load('window-fix/runtime-materials.json')
screens = ['preview-ski-windows-fixed.png', 'preview-ski-windows-wide-fixed.png', 'compact-numeric-row-12s.png', 'compact-numeric-row-40s.png', 'compact-numeric-row-70s.png', 'compact-numeric-row-130s.png', 'preview-ski-aurora.png']
for n in screens:
    source_screen = r / ('hud-fix/screenshots' if n.startswith('compact-') else 'screenshots') / n
    assert source_screen.is_file(), n
    (report / 'screenshots').mkdir(exist_ok=True)
    shutil.copy2(source_screen, report / 'screenshots' / n)
validation = {
    'platform': 'iOS Simulator, explicit iphonesimulator',
    'event': 'main-free_for_all-ski-dash',
    'commandEvidence': str(r / 'hud-fix/compact-numeric-row-capture.json'),
    'customTimerSeconds': 90,
    'naturalResultsScreenAt130sVisuallyInspected': True,
    'inspectionCameraBothHouseVariantsVisuallyInspected': True,
    'gameplay40sCompactHudVisuallyInspected': True,
    'compactSingleRowAllSixOpponentsVisuallyInspected': True,
    'translucentCounterAndMinimapPanelsWithRosterPreviewAndScores': True,
    'forcedWin': False,
    'limitations': ['Custom finite FFA probe; not verification of the default campaign timer.', 'Inspection cameras show both house variants; gameplay camera does not expose every window.', 'No FPS benchmark or new user art acceptance recorded.', 'Earlier explicit --track probes ran Three Strikes and are not FFA timer proof.', 'The 70s numeric HUD capture fell during the existing portrait result transition and is archived as transitional evidence, not a final gameplay screenshot.']
}
(r / 'runtime-validation.json').write_text(json.dumps(validation, indent=2))
a['stage'] = 'Integrated; preservation, native, shared material, built/installed and actual runtime evidence saved'
(r / 'ski-extraction.json').write_text(json.dumps(a, indent=2))
evidence = report / 'evidence' / 'coordinate-reuse'
evidence.mkdir(parents=True, exist_ok=True)
for n in ['ski-extraction.json', 'ski-enrichment.json', 'preservation-audit.json', 'native-verification.json', 'canonical-bindings-verification.json', 'live-verification.json', 'runtime-validation.json', 'preview-update.json', 'preview-bundle-verification.json', 'ski-window-fixed-capture.json']:
    shutil.copy2(r / n, evidence / Path(n).name)
shutil.copy2(r / 'window-fix/runtime-materials.json', evidence / 'shared-window-materials.json')
shutil.copytree(r / 'hud-fix', evidence / 'hud-fix', dirs_exist_ok=True)
refs = report / 'references' / 'coordinate-reuse'
refs.mkdir(parents=True, exist_ok=True)
for p in (r / 'references').glob('*.png'):
    shutil.copy2(p, refs / p.name)
previous = report / 'index.html'
if previous.exists() and not (report / 'before-coordinate-reuse.html').exists():
    shutil.copy2(previous, report / 'before-coordinate-reuse.html')
saved = a['sourceBytes'] - a['totalCandidateBytes']
fmt = lambda x: f'{x:,}'.replace(',', ' ')
images = ''.join(f'<figure><img src="screenshots/{n}" loading="lazy"><figcaption>{html.escape(label)}</figcaption></figure>' for n, label in [
    (screens[0], 'Два общих типа домов: самосвечение окон. Проверочная камера игрового движка.'),
    (screens[1], 'Общий вид деревни после исправления. Проверочная камера игрового движка.'),
    (screens[3], 'FFA, 40 секунд: компактный полупрозрачный HUD.'),
    (screens[2], 'FFA, 12 секунд: светящиеся окна обоих типов домов и компактный HUD.'),
    (screens[5], 'Естественное завершение FFA с проверочным таймером 90 секунд.')])
refimages = ''.join(f'<figure><img src="references/coordinate-reuse/{p.name}" loading="lazy"><figcaption>Исходный референс {i}</figcaption></figure>' for i, p in enumerate(sorted((r / 'references').glob('*.png')), 1))
previous.write_text(f'''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Ski Dash — общий пул и окна</title>
<style>body{{max-width:1200px;margin:40px auto;padding:0 24px;font:17px/1.55 system-ui;color:#dcecff;background:#101d2d}}h1,h2{{color:#fff}}a{{color:#8bd5ff}}img{{width:100%;height:auto;border-radius:12px}}figure{{margin:24px 0}}figcaption{{color:#b5c7db}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #42556b}}.refs{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}</style>
<h1>Ski Dash: общий пул, дополнительные ёлки и окна домов</h1>
<p>Перенесены три повторяющиеся гирлянды в одну общую модель. 71 ёлка уже размещалась по координатам; её модель и исходные текстуры теперь находятся в общем игровом пуле. Добавлены ещё 18 экземпляров той же ёлки на снежных уступах. Всего в этом этапе 92 размещения и две общие модели.</p>
<p>По замечанию пользователя обеим общим моделям домов назначено самосвечение окон. Исправление действует на всех картах, использующих эти библиотеки. Модели, текстуры, коллайдеры, центры и направления домов сохранены; изменение двух XML-материалов — 96 байт. Обновлены также семь библиотечных и итоговых файлов Blender.</p>
<p>HUD исправлен по уточнению пользователя: все шесть соперников находятся в одном компактном ряду сверху; внутри каждой карточки — превью из материалов персонажа и актуальные очки. Фоны позиции, кругов, таймера, миникарты и соперников полупрозрачны, со светлой рамкой. Подписи POS/LAP/TIME убраны; высота основных карточек уменьшена до 43 пикселей по актуальному макету. Соответствующие четыре фона исправлены в Figma 100:2 и заново экспортированы с альфа-каналом.</p>
<h2>Вес</h2><table><tr><th>Измерение</th><th>Байты</th></tr>
<tr><td>Карта до этого этапа</td><td>{fmt(a['sourceBytes'])}</td></tr>
<tr><td>Карта после этапа, включая новое превью</td><td>{fmt(a['candidateTrackBytes'])}</td></tr>
<tr><td>Все новые общие модели и текстуры</td><td>{fmt(a['allNewSharedBytes'])}</td></tr>
<tr><td>Дополнение материалов существующих домов</td><td>96</td></tr>
<tr><td>Итого карта + новые общие ресурсы + материалы</td><td>{fmt(a['totalCandidateBytes'])}</td></tr>
<tr><td>Уменьшение с учётом нового превью</td><td>{fmt(saved)}</td></tr>
<tr><td>Уменьшение до замены превью</td><td>50 900</td></tr>
<tr><td>Всё установленное приложение после этапа</td><td>{fmt(live['appBytesAfter'])}</td></tr></table>
<p>Вес приложения измерен для несжатой Debug-сборки iOS Simulator. Это не размер IPA или загрузки App Store. Дополнительные ёлки не добавляют файлов моделей или текстур, но добавляют 71 496 отображаемых треугольников.</p>
<h2>Проверка</h2><p>Основной меш арены и navmesh совпадают побайтно. Исходные 16 размещений домов, игровые точки и атмосферные объекты сохранены. Геометрия, UV, нормали и цвета общей ёлки совпадают с исходником. В итоговом Blender проверены 314 сохранённых мешей и 270 частей общих экземпляров; отсутствующих изображений нет.</p>
<p>Запущено настоящее событие FFA Ski Dash в iOS Simulator с проверочным лимитом 90 секунд. На 130-й секунде получен естественный экран результатов; принудительная победа не использовалась. Окна обоих типов домов просмотрены проверочными камерами движка. Компактный ряд очков и полупрозрачные фоны проверены в игровом кадре. FPS не измерялся; проверка всех окон отдельными игровыми ракурсами не проводилась.</p>
<p>Новое превью получено из движка, выполнены только центральная обрезка и уменьшение до 1024×576. Сгенерированная карточка кампании проверена в собранном и установленном приложении.</p>
<h2>Скриншоты</h2>{images}<h2>Сохранённые референсы</h2><div class="refs">{refimages}</div>
<p>Этот этап сохраняет ранее переделанный стиль Ski Dash; полного нового визуального согласования по четырём референсам не записано. Общая работа по картам 1–10 продолжается.</p>
<p><a href="before-coordinate-reuse.html">Предыдущий отчёт</a> · <a href="evidence/coordinate-reuse/preservation-audit.json">Сохранность арены</a> · <a href="evidence/coordinate-reuse/shared-window-materials.json">Общие окна</a> · <a href="evidence/coordinate-reuse/runtime-validation.json">Игровая проверка</a></p></html>''')
manifest = load('preview-update.json')
manifest.update({'report': str(previous), 'finalBlend': str(final / 'Ski Dash.blend'), 'screenshots': [info(report / 'screenshots' / n) for n in screens], 'evidence': str(evidence), 'mapPlusSharedBytes': a['totalCandidateBytes'], 'appBytes': live['appBytesAfter']})
(report / 'coordinate-reuse-manifest.json').write_text(json.dumps(manifest, indent=2))
lp = root / 'fluxara-user-ski-dash.asset-ledger.json'
ledger = json.loads(lp.read_text())
ledger['coordinateReusePhase'].update({'runtimeValidation': validation, 'report': str(previous), 'preservation': load('preservation-audit.json'), 'preview': load('preview-update.json'), 'liveVerification': live})
ledger['sharedWindowMaterialCorrection']['runtimeValidation'] = validation
lp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
src = pack / 'sources/ski-shared-placement-v1'
src.mkdir(parents=True, exist_ok=True)
for p in r.iterdir():
    if p.is_file() and p.suffix in {'.py', '.js', '.json', '.log'}:
        shutil.copy2(p, src / p.name)
for name in ['window-fix', 'hud-fix', 'screenshots', 'references']:
    shutil.copytree(r / name, src / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns('blend-before', 'pack-before'))
shutil.copytree(report, src / 'report', dirs_exist_ok=True)
progress_path = r.parent / 'shared-placement-1-10/progress.json'
progress = json.loads(progress_path.read_text())
progress['maps']['2'] = {'trackId': a['trackId'], 'storageConversionInstances': 3, 'existingCoordinateFirInstancesPromotedToSharedPool': 71, 'newFirInstances': 18, 'uniqueModels': 2, 'sharedBytes': a['allNewSharedBytes'], 'trackPlusNewSharedAndWindowBytes': a['totalCandidateBytes'], 'naturalFiniteFFAFinish': True, 'sharedHouseWindowsCorrected': True, 'report': str(previous), 'fullyAccepted': False, 'status': 'Coordinate phase and global house window fix delivered; further cross-map enrichment remains'}
for i, folder in [('3', 'dust-cross-shared-placement'), ('4', 'spell-lab-shared-placement')]:
    candidate_root = r.parent / folder
    filename = 'dust-extraction.json' if i == '3' else 'spell-extraction.json'
    q = json.loads((candidate_root / filename).read_text())
    progress['maps'][i] = {'status': 'Isolated extraction candidate; not integrated or runtime validated', 'candidateProof': str(candidate_root / filename), 'originalRuntimeUnchanged': True, 'candidateCoordinateInstances': q['coordinateInstances']}
progress['appBytes'] = live['appBytesAfter']
progress['goalComplete'] = False
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
print('SKI_DELIVERY_SAVED', saved, live['appBytesAfter'])
