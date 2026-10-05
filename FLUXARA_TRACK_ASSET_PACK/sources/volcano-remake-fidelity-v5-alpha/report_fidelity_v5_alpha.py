from pathlib import Path
import hashlib
import json
import re
import shutil
from urllib.parse import unquote, urlsplit

r = Path(__file__).resolve().parent
w = r / 'fidelity-v5-alpha'
out = r.parent / 'fluxara-user-volcano-remake-final/report'
page = out / 'index.html'
evidence = out / 'evidence/fidelity-v5-alpha'
evidence.mkdir(parents=True, exist_ok=True)
history = w / 'report-history'
history.mkdir(exist_ok=True)
shutil.copy2(page, history / (hashlib.sha256(page.read_bytes()).hexdigest()[:12] + '-index.html'))
proofs = ['preservation.json', 'budget.json', 'runtime-validation.json',
          'layout-changes.json', 'tint-changes.json', 'drive-capture.json',
          'smoke-diagnostic-all.json', 'final-blend-verification.json',
          'canonical-bindings-verification.json', 'pool-audit.json']
for name in proofs:
    shutil.copy2(w / name, evidence / name)
for name in ['drive-40s.png', 'drive-80s.png', 'drive-150s.png', 'smoke-diagnostic-all.png']:
    shutil.copy2(w / 'screenshots' / name, out / 'screenshots' / ('fidelity-v5-alpha-' + name))
for name in ['drive-40s.png', 'drive-80s.png']:
    shutil.copy2(r / 'fidelity-v5/screenshots' / name, out / 'screenshots' / ('rejected-v5-' + name))
b = json.loads((w / 'budget.json').read_text())
runtime = json.loads((w / 'runtime-validation.json').read_text())
assert runtime['candidateOneLapTimeTrial']['naturalFinishObserved']
assert len(json.loads((w / 'final-blend-verification.json').read_text())['threeSmokeEffectsAboveRoad']) == 3
section = f'''<section id="fidelity-v5-alpha-draft"><h2>Последняя доработка — V5 Alpha</h2>
<p>У трёх основных дымовых эффектов восстановлена исходная геометрия с прозрачной текстурой: AshCloud, AshColumn и PyroclasticFlow. Пять остальных эффектов используют геометрию V4E. Все восемь получают сливовый оттенок через цвет вершин и прозрачность Alpha Blend; одна существующая RGBA-текстура повторно используется без новых копий.</p>
<p>Изменено размещение только трёх декоративных объектов с interaction=ghost: высота AshCloud увеличена на 43,61 единицы, масштаб 0,35 → 0,18; AshColumn поднят на 83,6 единицы без изменения масштаба; PyroclasticFlow поднят на 130 единиц, статический масштаб 0,35 → 0,12, значения и ручки кривой высоты сдвинуты на 130, значения и ручки трёх кривых масштаба умножены на 0,12. Это изменения размещений на карте, а не локальных размеров, начал координат или осей моделей. Все остальные узлы сцены совпадают с V4E.</p>
<p>Полотно трассы, его вершины, нормали, UV, цвета и индексы совпадают с оригиналом. Исходные track.xml, quads.xml, graph.xml, scripting.as и easter_eggs.xml сохранены побайтно. У трёх восстановленных эффектов локальная геометрия и UV совпадают с оригиналом; у остальных пяти — с V4E. Проверено, что три поднятых эффекта остаются выше максимальной высоты дороги с запасом, в том числе на всём цикле анимации PyroclasticFlow. Эта проверка касается именно трёх объектов и не заменяет проверку остальных эффектов.</p>
<table><tr><th>Показатель кандидата</th><th>Результат</th></tr>
<tr><td>Папка карты</td><td>{b['candidateTrackBytes']:,} байт; на {b['savedBytesAgainstPrevious']:,} байт меньше основной V1</td></tr>
<tr><td>Треугольники</td><td>{b['candidateTriangles']:,}; +{b['triangleChangePercentAgainstOriginal']:.2f}% к оригиналу, в общем бюджете +20%</td></tr>
<tr><td>Дополнительные общие игровые ресурсы</td><td>0 байт; используется существующая текстура</td></tr>
<tr><td>Регистрация в пуле</td><td>8 редактируемых прототипов, 8 SPM, 2 определения материала; физические пути и зависимости проверены</td></tr></table>
<p>Общий вес карты уменьшился. Это не утверждение, что каждый отдельный меш вместе с текстурой укладывается в ±20% от оригинала: часть пяти ранее переделанных карточек имеет большее изменение веса, а исходные большие текстуры заменены общей меньшей. Число треугольников всех восьми дымовых моделей сохранено относительно соответствующих исходников.</p>
<p>В iOS Simulator проверен один круг Time Trial с одной машиной: естественный финиш #1 без принудительной победы. На двух приложенных игровых кадрах дорога открыта. Сохранённый Blender-файл повторно открыт: позиции, индексы, UV, цвета восьми прототипов и ключи с ручками кривых совпадают с экспортом. Проверены 85 частей общих размещений, текстуры и встроенные XML. В канонической библиотеке проверены привязки моделей карт 6–10 и свечение окон домов.</p>
<p class="note"><strong>Карта 10 ещё не завершена.</strong> Несколько дымовых эффектов остаются похожи на вытянутые лепестки или столбы. Формы замка, скал, вулканов и лавовых шипов всё ещё отличаются от референса. Кандидат сохранён отдельно; основная игровая карта, итоговый Blender-файл и превью кампании сохраняют V1. Полный заезд кампании, обратное направление и производительность кандидата не подтверждены. Новый билд приложения на этом этапе не выполнялся.</p>
<p><a href="../../volcano-remake-rework/fidelity-v5-alpha/native/Volcano%20Remake.blend">Редактируемый кандидат V5 Alpha</a> · <a href="evidence/fidelity-v5-alpha/preservation.json">Сохранность полотна и игровых данных</a> · <a href="evidence/fidelity-v5-alpha/layout-changes.json">Изменённые размещения</a> · <a href="evidence/fidelity-v5-alpha/budget.json">Вес и треугольники</a> · <a href="evidence/fidelity-v5-alpha/runtime-validation.json">Граница проверки заезда</a> · <a href="evidence/fidelity-v5-alpha/final-blend-verification.json">Blender и высота дыма</a> · <a href="evidence/fidelity-v5-alpha/pool-audit.json">Проверка физических общих ресурсов</a></p>
<figure><a href="screenshots/fidelity-v5-alpha-drive-40s.png"><img src="screenshots/fidelity-v5-alpha-drive-40s.png" alt="V5 Alpha: игровой поворот у лавы"></a><figcaption><strong>V5 Alpha — поворот у лавы</strong><span>Игровая камера текущего кандидата; дым расположен в фоне.</span></figcaption></figure>
<figure><a href="screenshots/fidelity-v5-alpha-drive-80s.png"><img src="screenshots/fidelity-v5-alpha-drive-80s.png" alt="V5 Alpha: верхняя часть маршрута"></a><figcaption><strong>V5 Alpha — верхняя часть маршрута</strong><span>Игровая камера. Крупные замковые формы ещё требуют переделки.</span></figcaption></figure>
<p>Отдельно сохранены <a href="screenshots/fidelity-v5-alpha-drive-150s.png">естественный финиш</a> и <a href="screenshots/fidelity-v5-alpha-smoke-diagnostic-all.png">статический обзор камерой движка</a>. Статический обзор не является скриншотом заезда. Задержки 40/80/150 секунд в именах файлов относятся к системным часам, не к игровому таймеру.</p>
<h3>Отклонённый опыт V5 с непрозрачными объёмами</h3><p>Объёмные клубы перекрывали дорогу во время анимации: <a href="screenshots/rejected-v5-drive-40s.png">первый игровой кадр</a>, <a href="screenshots/rejected-v5-drive-80s.png">второй игровой кадр</a>. Естественный финиш не подтверждает приемлемый визуал. Этот вариант отклонён и не перенесён в основную карту.</p></section>'''
s = re.sub(r'<section id="fidelity-v5-alpha-draft">.*?</section>', '', page.read_text(), flags=re.S)
s = s.replace('<section id="fidelity-v2-draft">', section + '<section id="fidelity-v2-draft">', 1)
s = s.replace('Текущая доработка V4E — пять дымовых эффектов', 'Предыдущая доработка V4E — пять дымовых эффектов')
s = s.replace('В разделах отдельных кандидатов V2, V3 и V4E добавлены', 'В разделах отдельных кандидатов V2, V3, V4E и V5 Alpha добавлены')
page.write_text(s)
missing = [link for link in re.findall(r'(?:src|href)="([^"]+)"', s)
           if not urlsplit(link).scheme and not link.startswith('#')
           and not (out / unquote(link.split('#')[0])).exists()]
assert not missing, missing
(out / 'manifest.json').write_text(json.dumps({'brokenLocalLinks': missing,
    'files': [{'path': str(p.relative_to(out)), 'bytes': p.stat().st_size,
               'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json']}, indent=2))
pack = Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for prefix in ['volcano-remake-reference-v1', 'volcano-remake-fidelity-v2',
               'volcano-remake-fidelity-v3', 'volcano-remake-fidelity-v4e',
               'volcano-remake-fidelity-v5', 'volcano-remake-fidelity-v5-alpha']:
    shutil.copytree(out, pack / 'sources' / prefix / 'report', dirs_exist_ok=True)
shutil.copy2(Path(__file__), pack / 'sources/volcano-remake-fidelity-v5-alpha' / Path(__file__).name)
progress_path = r.parent / 'shared-placement-1-10/progress.json'
progress = json.loads(progress_path.read_text())
progress['maps']['10'].update({
    'status': 'V5 Alpha: original transparent core smoke geometry restored, eight effects tinted; three decorative effects raised above road, curves verified. Natural one-lap finish, native and canonical assets indexed. Castle, cliffs, lava and stretched sprite forms remain unfinished. Production and preview unchanged.',
    'candidate': str(w), 'candidateTrackBytes': b['candidateTrackBytes'],
    'candidateSavedBytesAgainstPrevious': b['savedBytesAgainstPrevious'],
    'candidateTriangleChangePercent': b['triangleChangePercentAgainstOriginal'],
    'candidateOneLapNaturalFinish': True, 'candidateProductionIntegrated': False,
    'fullyAccepted': False})
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
print('V5_ALPHA_REPORT_UPDATED', page)
