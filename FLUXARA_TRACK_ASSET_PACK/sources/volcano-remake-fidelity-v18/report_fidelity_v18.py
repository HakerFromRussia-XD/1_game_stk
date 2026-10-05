from pathlib import Path
import json, shutil, re, hashlib

r = Path(__file__).resolve().parent
w = r/'fidelity-v18'
out = r.parent/'fluxara-user-volcano-remake-final/report'
e = out/'evidence/fidelity-v18'
e.mkdir(exist_ok=True)
b = json.loads((w/'preservation-verification.json').read_text())
run = json.loads((w/'runtime-validation.json').read_text())
audit = json.loads((w/'pool-audit.json').read_text())
assert run['naturalFinishObserved'] and run['visualInspectionCompleted']
assert audit['newRuntimeModels'] == 1 and audit['newTextures'] == 0
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'):
        shutil.copy2(p, e/p.name)
figures = []
for second, caption in [(40, 'Прежняя фактура камня на скалах, исходный решётчатый участок трассы и лава.'),
                        (80, 'Проезд замкового участка и ускоритель: каменная фактура, дорога и игровые линии сохранены.')]:
    name = f'fidelity-v18-game-{second}.png'
    shutil.copy2(w/f'screenshots/drive-{second}s.png', out/'screenshots'/name)
    figures.append(f'<figure><a href="screenshots/{name}"><img src="screenshots/{name}" alt="Игровой кадр V18"></a><figcaption>iOS Simulator. {caption}</figcaption></figure>')
static = 'fidelity-v18-green-mounds-overview.png'
finish = 'fidelity-v18-natural-finish.png'
shutil.copy2(w/'screenshots/smoke-diagnostic-all.png', out/'screenshots'/static)
shutil.copy2(w/'screenshots/natural-finish.png', out/'screenshots'/finish)
section = f'''<section id="fidelity-v18-draft"><h2>Последняя доработка — V18: каменная фактура сохранена, добавлены зелёные холмы</h2>
<p>По замечанию «С текстурой камня было лучше» прежнее изображение Rock13_col.jpg и UV существующих каменных объектов сохранены. К V17 добавлены 32 декоративных холма по координатам: одна отдельная копия модели из пула Lap Catch. Коричневые бока исходного объекта не подходили к референсу; вариант с ними отвергнут после просмотра в движке и сохранён в архиве итераций. В текущей копии используется зелёный цвет вершин, полученный из существующей палитры ландшафта. Исходная модель и её текстура в пуле не менялись.</p>
<table><tr><th>Показатель</th><th>Результат</th></tr>
<tr><td>Карта и все добавленные общие игровые ресурсы</td><td>{b['candidateIncludingNewSharedBytes']:,} байт против {b['v1Bytes']:,} байт V1. Уменьшение на {b['savingBytesVsV1']:,} байт ({b['savingBytesVsV1']/b['v1Bytes']*100:.2f}%). Включены также сохранённые ранние варианты новых ресурсов.</td></tr>
<tr><td>Модель холма с её текстурами</td><td>{b['sourceModelWithTextureBytes']:,} → {b['targetModelWithTextureBytes']:,} байт ({b['modelWithTextureChangePercent']:.2f}%). 360 треугольников, 222 вершины; геометрия, нормали, оси, центр и локальные габариты исходные. Верхний предел +20% соблюдён. Ограничение ±20% на число полигонов не применяется.</td></tr>
<tr><td>Дополнительные игровые файлы</td><td>Одна модель на 32 координаты. Новых текстур — 0. Прежний материал цвета вершин переиспользован.</td></tr>
<tr><td>Постановка и сохранность</td><td>Каждая вершина основания проверена по поверхности: основание заглублено минимум на 0.40 м. Запас описывающей сферы до дороги {b['minimumRoadSphereMarginMeters']:.2f} м, до исходных навигационных квадов {b['minimumOriginalNavigationQuadSphereMarginMeters']:.2f} м. Все прежние объекты, файлы моделей, текстур и управления побайтно совпадают с V17. Дорога, физика и игровые точки/линии не менялись.</td></tr>
<tr><td>Blender и общий пул</td><td>32 активных прототипа, 88 материалов и 331 общая часть. Один новый прототип зарегистрирован в канонической библиотеке, существующий материал переиспользован. {audit['totalLedgerAssetsIncludingHistoricalSources']} ресурсов в ведомости этой карты с историческими источниками; все пути, зависимости и хеши проверены.</td></tr></table>
<p>Повторное открытие Blender подтвердило сохранность геометрии, нормалей, цветов, материалов, UV и матриц 571 прежнего меша. Все 32 новых матрицы соответствуют сцене движка. Выполнен полный круг Time Trial: один карт, один круг, seed 4, естественный результат <a href="screenshots/{finish}">#1</a>, без принудительной победы. Ниже два сохранённых игровых кадра; расстановка холмов видна на <a href="screenshots/{static}">общем диагностическом виде из движка</a>. Скриншоты не ретушировались; округлая чёрная область экрана симулятора сохранена. Временные пробные ресурсы удалены из установленного приложения; существующая библиотека донорской модели не менялась.</p>
<p class="note">Это отдельный кандидат. Основная карта, итоговый пользовательский .blend и превью пока остаются V1. Широкие плоские зелёные поверхности, регулярная цепочка дыма, пропорции замкового окружения и атмосфера ещё отличаются от референса. Нет заявления о завершённом визуале, новом весе приложения, производительности, проверке обратного режима или всей кампании.</p>
<p><a href="../../volcano-remake-rework/fidelity-v18/native/Volcano%20Remake.blend">Blender V18</a> · <a href="evidence/fidelity-v18/hill-placements.json">32 координаты и источник модели</a> · <a href="evidence/fidelity-v18/preservation-verification.json">Вес и сохранность</a> · <a href="evidence/fidelity-v18/final-blend-verification.json">Проверка Blender</a> · <a href="evidence/fidelity-v18/runtime-validation.json">Полный игровой круг</a> · <a href="evidence/fidelity-v18/pool-audit.json">Общий пул</a></p>{''.join(figures)}</section>'''
page = out/'index.html'
s = re.sub(r'<section id="fidelity-v18-draft">.*?</section>', '', page.read_text(), flags=re.S)
s = s.replace('<section id="fidelity-v17-draft">', section+'<section id="fidelity-v17-draft">', 1)
s = s.replace('Последняя доработка — V17', 'Предыдущая доработка — V17')
page.write_text(s)
manifest = out/'manifest.json'
m = json.loads(manifest.read_text())
m['files'] = [{'path': str(p.relative_to(out)), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p != manifest]
manifest.write_text(json.dumps(m, ensure_ascii=False, indent=2))
pack = Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for dest in [pack/'sources/volcano-remake-reference-v1/report', pack/'sources/volcano-remake-fidelity-v18/report']:
    shutil.copytree(out, dest, dirs_exist_ok=True)
shutil.copy2(Path(__file__), pack/'sources/volcano-remake-fidelity-v18'/Path(__file__).name)
progress = r.parent/'shared-placement-1-10/progress.json'
d = json.loads(progress.read_text())
d['maps']['10'].update({'status': 'V18: stone pixels and existing UVs retained; 32 coordinate green mounds from one adapted pooled model, no new texture. Native/canonical verified, one-lap natural TT #1. Reference fidelity unfinished; production/final/preview V1.',
                        'candidate': str(w), 'candidateTrackBytes': b['candidateMapBytes'],
                        'candidateBytesIncludingNewSharedRuntime': b['candidateIncludingNewSharedBytes'],
                        'candidateSavedBytesAgainstPrevious': b['savingBytesVsV1'],
                        'candidateOneLapNaturalFinish': True, 'lastFullLapVerifiedCandidate': 'V18',
                        'lastFullLapNaturalFinish': True, 'candidateProductionIntegrated': False,
                        'candidateActiveNativePrototypes': 32, 'newCoordinateHillPlacements': 32,
                        'fullyAccepted': False})
d['goalComplete'] = False
progress.write_text(json.dumps(d, ensure_ascii=False, indent=2))
plan = r/'next-fidelity-batch.json'
d = json.loads(plan.read_text())
d['baseCandidate'] = 'V18'
d['status'] = 'V18 retains stone texture/UVs and adds 32 green mounds via one adapted pooled model. Weight 6471518B. Reference work unfinished.'
for q in d['priorities']:
    if q['role'] == 'Rounded central cliff support and green terrain':
        q.update({'sourceModel': 'output/volcano-remake-rework/fidelity-v18/candidate/volcano_track.spm',
                  'terrainDetailBatchCompletedCandidate': 'V18',
                  'terrainDetailBatch': '32 coordinate hills, adapted pooled model with source geometry retained and green vertex colors. Original brown hill donor and its texture unchanged.',
                  'remaining': 'Broad planar terrain and separated cylindrical cliff caps still differ from reference; new small mounds alone do not solve the large silhouette.'})
plan.write_text(json.dumps(d, indent=2))
print('V18_REPORT_TWO_GAME_FRAMES_AND_FULL_LAP_UPDATED', len(m['files']), flush=True)
