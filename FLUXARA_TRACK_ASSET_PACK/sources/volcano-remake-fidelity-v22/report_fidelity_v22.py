from pathlib import Path
import hashlib
import json
import re
import shutil

r = Path(__file__).resolve().parent
w = r/'fidelity-v22'
out = r.parent/'fluxara-user-volcano-remake-final/report'
e = out/'evidence/fidelity-v22'
e.mkdir(exist_ok=True)
b = json.loads((w/'preservation-verification.json').read_text())
run = json.loads((w/'runtime-validation.json').read_text())
audit = json.loads((w/'pool-audit.json').read_text())
native = json.loads((w/'final-blend-verification.json').read_text())
assert run['naturalFinishObserved'] and run['visualInspectionCompleted']
assert audit['newNativePrototypes'] == 2 and audit['newTextures'] == 0
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'):
        shutil.copy2(p, e/p.name)
figures = []
for second, caption in [(40, 'Сохранённая каменная фактура; новые уступы видны над стеной справа.'), (140, 'Каменная арка и исходная дорога после возвращения AI на маршрут.')]:
    name = f'fidelity-v22-game-{second}.png'
    shutil.copy2(w/f'screenshots/drive-{second}s.png', out/'screenshots'/name)
    figures.append(f'<figure><a href="screenshots/{name}"><img src="screenshots/{name}" alt="Игровой кадр V22"></a><figcaption>iOS Simulator. {caption}</figcaption></figure>')
for name, src in [
    ('fidelity-v22-overview.png', w/'screenshots/smoke-diagnostic-all.png'),
    ('fidelity-v22-natural-finish.png', w/'screenshots/natural-finish.png'),
    ('fidelity-v22-ramp-80.png', w/'screenshots/drive-80s.png'),
    ('baseline-v1-ramp-80.png', r/'ai-v1-comparison/screenshots/v1-80s.png'),
    ('baseline-v1-natural-finish.png', r/'ai-v1-comparison/screenshots/v1-190s.png')]:
    shutil.copy2(src, out/'screenshots'/name)
section = f'''<section id="fidelity-v22-draft"><h2>Последняя доработка — V22: каменная фактура сохранена, уступы шире</h2>
<p>По замечанию пользователя сохранена текущая текстура камня размером 39&nbsp;938 байт: пиксели, UV и исходные цвета вершин не изменены. Форма общей копии уступа стала менее регулярной; зелёный верх закруглён внутрь прежнего габарита. Один SPM с 432 треугольниками используется в 58 размещениях по координатам. Исходная общая модель V16 и донорский объект сохранены.</p>
<p>Изменены только 58 ранее добавленных декоративных уступов: 56 стали шире в 1,55 раза и ниже до 0,83 прежней высоты, два — шире в 1,35 раза и ниже до 0,88. Их горизонтальные позиции, направления и верхняя мировая высота сохранены; вертикальное начало координат размещения сдвинуто для сохранения этой высоты. Локальные размеры, начало координат и оси самой общей модели сохранены. Мировые размеры новых декоративных экземпляров изменены намеренно. Исходные объекты карты, все другие файлы V21, дорога, физические меши и программные точки/линии не менялись.</p>
<p>Проверенный запас ограничивающей сферы до 2&nbsp;032 защищённых треугольников проезда — {b['independentProtectedRoadSphereMarginMeters']:.3f} м. Основания расположены минимум на {b['minimumFootingDepthBelowOriginalTerrainMeters']:.3f} м ниже исходного рельефа в центральной точке каждого размещения; это проверка центра, а не всей расширенной площади опоры.</p>
<table><tr><th>Измерение</th><th>Результат</th></tr>
<tr><td>Исходный объект пула с обеими текстурами</td><td>{b['sourcePoolModelWithTexturesBytes']:,} байт</td></tr>
<tr><td>Адаптированный уступ с используемой каменной текстурой</td><td>{b['adaptedModelWithTextureBytes']:,} байт; {b['modelWithTextureChangePercent']:.2f}%</td></tr>
<tr><td>Карта + все новые общие игровые ресурсы, включая сохранённые ранние варианты</td><td>{b['candidateIncludingNewSharedBytes']:,} байт</td></tr>
<tr><td>Интегрированный V1</td><td>{b['v1Bytes']:,} байт</td></tr>
<tr><td>Уменьшение относительно V1</td><td>{b['savingBytesVsV1']:,} байт; {b['savingBytesVsV1']/b['v1Bytes']*100:.2f}%</td></tr>
<tr><td>Добавлено относительно V21</td><td>{b['changeBytesAgainstIntermediateV21']:,} байт</td></tr></table>
<p>Предел +20% выполнен для веса модели с используемыми текстурами. Количество полигонов приведено только для информации. Новых файлов текстур, пикселей и материалов нет. Повторные размещения не создают отдельные копии SPM; дополнительные записи координат включены в размер scene.xml. Размер приложения заново не измерялся.</p>
<p>При повторном открытии Blender {native['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV21']} прочих мешей точно совпали с V21 по геометрии, UV, нормалям, цветам, матрицам и материалам. У 116 частей декоративных уступов заменены общая геометрия и матрицы. Два новых прототипа используют прежние материалы; активны 34 прототипа, 88 материалов и 333 общие части. Проверены 1&nbsp;296 углов новых прототипов и 180 навигационных квадов. Старые прототипы сохранены скрытыми. Два новых объекта добавлены в каноническую библиотеку; все {audit['totalLedgerAssetsIncludingHistoricalSources']} ресурсов ведомости имеют реальные файлы с проверенными хешами и зависимостями.</p>
<p>Полный круг Time Trial: один карт, один круг, seed 4, естественный результат <a href="screenshots/fidelity-v22-natural-finish.png">#1 на 190-й секунде</a>. На <a href="screenshots/fidelity-v22-ramp-80.png">80-й секунде</a> карт находится в воздухе под краем рампы; на 140-й он снова на дороге. При сравнительном запуске неизменённого V1 в том же приложении, режиме и seed также наблюдается <a href="screenshots/baseline-v1-ramp-80.png">опасное прохождение рампы</a> и <a href="screenshots/baseline-v1-natural-finish.png">финиш</a>. Это подтверждает наличие проблемы до текущей доработки, но один прогон с кадрами по времени не исключает всех регрессий и не доказывает одинаковую причину. Дорога и исходная геометрия столкновений сохранены; безошибочное прохождение AI не заявляется.</p>
<p>Ниже два игровых кадра без ретуши. Новые пропорции уступов лучше видны на <a href="screenshots/fidelity-v22-overview.png">общем диагностическом виде в движке</a>. Слишком бледная проба окраски отклонена, исходные зелёные цвета вершин возвращены. Временная карта и скопированные ресурсы удалены из установленного приложения; донорская библиотека не изменена. Предупреждения о материалах совпали с V21.</p>
<p class="note">Сходство с референсом ещё не достигнуто: остаются плоские площадки рядом с дорогой, большие повторяющиеся каменные стены, пропорции замка и освещение атмосферы. Основная карта, итоговый пользовательский .blend и превью пока V1. Новая сборка приложения, производительность, обратный режим и вся кампания здесь не проверялись.</p>
<p><a href="../../volcano-remake-rework/fidelity-v22/native/Volcano%20Remake.blend">Blender V22</a> · <a href="evidence/fidelity-v22/cliff-changes.json">Общие уступы и размещения</a> · <a href="evidence/fidelity-v22/preservation-verification.json">Вес и сохранность</a> · <a href="evidence/fidelity-v22/final-blend-verification.json">Проверка Blender</a> · <a href="evidence/fidelity-v22/runtime-validation.json">Игровой круг</a> · <a href="evidence/fidelity-v22/ai-v1-comparison.json">Сравнение с V1</a> · <a href="evidence/fidelity-v22/pool-audit.json">Общий пул</a></p>{''.join(figures)}</section>'''
page = out/'index.html'
s = re.sub(r'<section id="fidelity-v22-draft">.*?</section>', '', page.read_text(), flags=re.S)
s = s.replace('Последняя доработка — V21', 'Предыдущая доработка — V21')
s = s.replace('<section id="fidelity-v21-draft">', section+'<section id="fidelity-v21-draft">', 1)
page.write_text(s)
manifest = out/'manifest.json'
m = json.loads(manifest.read_text())
m['files'] = [{'path':str(p.relative_to(out)), 'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p != manifest]
manifest.write_text(json.dumps(m, ensure_ascii=False, indent=2))
pack = Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for dest in [pack/'sources/volcano-remake-reference-v1/report', pack/'sources/volcano-remake-fidelity-v22/report']:
    shutil.copytree(out, dest, dirs_exist_ok=True)
shutil.copy2(Path(__file__), pack/'sources/volcano-remake-fidelity-v22'/Path(__file__).name)
progress = r.parent/'shared-placement-1-10/progress.json'
data = json.loads(progress.read_text())
data['maps']['10'].update({'status':'V22 widens 58 copied cliffs with existing stone pixels/UVs and source grass colors. Native/canonical/ledger and natural one-lap #1 verified. V1 comparison shows preexisting unsafe ramp traversal but does not exclude all regressions. Near-road forms, large walls and lighting unfinished; production/final/preview V1.', 'candidate':str(w), 'candidateTrackBytes':b['candidateMapBytes'], 'candidateBytesIncludingNewSharedRuntime':b['candidateIncludingNewSharedBytes'], 'candidateSavedBytesAgainstPrevious':b['savingBytesVsV1'], 'candidateOneLapNaturalFinish':True, 'lastFullLapVerifiedCandidate':'V22', 'lastFullLapNaturalFinish':True, 'candidateProductionIntegrated':False, 'candidateActiveNativePrototypes':34, 'fullyAccepted':False, 'preexistingUnsafeRampTraversalObserved':True, 'allTraversalRegressionsExcluded':False})
data['goalComplete'] = False
progress.write_text(json.dumps(data, ensure_ascii=False, indent=2))
plan = r/'next-fidelity-batch.json'
data = json.loads(plan.read_text())
data['baseCandidate'] = 'V22'
data['status'] = 'V22 improves width and organic profile of 58 added cliffs, retains stone pixels/UVs and source grass colors. Weight 6551953B. V1 comparison observed unsafe ramp traversal already present; regressions not fully excluded. Large foreground and background forms/lighting remain unfinished.'
for q in data['priorities']:
    if q['role'] == 'Rounded central cliff support and green terrain':
        q.update({'completedCandidate':'V22 partial', 'done':'Central crest rounded in V21 and sixteen terrain components in V20. Fifty-eight new copied cliff placements wider/shorter in V22 with stone texture, original source models retained.', 'remaining':'Near-road components 12/13/15 remain planar; large stone-wall silhouettes and repeated cliff tops still differ from reference. Improve major forms and lighting.'})
data['aiComparison'] = {'baseline':'V1', 'preexistingUnsafeRampTraversalObserved':True, 'allRegressionsExcluded':False, 'evidence':str(w/'ai-v1-comparison.json')}
plan.write_text(json.dumps(data, indent=2))
print('V22_REPORT_TWO_GAME_FRAMES_UPDATED', len(m['files']), flush=True)
