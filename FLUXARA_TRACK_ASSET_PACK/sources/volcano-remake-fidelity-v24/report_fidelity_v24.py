from pathlib import Path
import hashlib, json, re, shutil
r=Path(__file__).resolve().parent; w=r/'fidelity-v24'
out=r.parent/'fluxara-user-volcano-remake-final/report'; e=out/'evidence/fidelity-v24'; e.mkdir(exist_ok=True)
b=json.loads((w/'preservation-verification.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text()); audit=json.loads((w/'pool-audit.json').read_text())
p=json.loads((w/'atmosphere-changes.json').read_text()); native=json.loads((w/'final-blend-verification.json').read_text())
assert run['naturalFinishObserved'] and run['visualInspectionCompleted'] and audit['newNativePrototypes']==3
assert b['originalStoneGeometryUVsAndPixelFilesUnchanged'] and audit['newTorchRuntimeBytesAdded']==0
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'): shutil.copy2(f,e/f.name)
figures=[]
for second,caption in [(40,'Дорожный кадр: исходное покрытие, каменная фактура и тёплая нижняя часть дыма.'),(140,'Каменная арка и её фактура сохранены. Карт находится на исходной дороге.')]:
    name=f'fidelity-v24-game-{second}.png'; shutil.copy2(w/f'screenshots/drive-{second}s.png',out/'screenshots'/name)
    figures.append(f'<figure><a href="screenshots/{name}"><img src="screenshots/{name}" alt="Игровой кадр V24"></a><figcaption>iOS Simulator. {caption}</figcaption></figure>')
for name,src in [('fidelity-v24-overview.png',w/'screenshots/smoke-diagnostic-all.png'),('fidelity-v24-natural-finish.png',w/'screenshots/natural-finish.png'),('fidelity-v24-ramp-80.png',w/'screenshots/drive-80s.png')]:
    shutil.copy2(src,out/'screenshots'/name)
rows=''.join(f'<tr><td>{q["model"]}</td><td>{q["originalModelWithTextureBytes"]:,}</td><td>{q["adaptedModelWithTextureBytes"]:,}</td><td>{q["modelWithTextureChangePercent"]:.2f}%</td></tr>' for q in p['smoke'])
section=f'''<section id="fidelity-v24-draft"><h2>Последняя доработка — V24: каменная фактура сохранена, дым и факелы</h2>
<p>По замечанию «С текстурой камня было лучше» сохранены нынешний Rock13_col.jpg и его общая копия размером 39&nbsp;938 байт: SHA-256 6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd. Пиксели, UV камня, каменные грани и прежние размещения не менялись. Текстура не заменялась одноцветной палитрой.</p>
<p>У трёх моделей дыма изменены только цвета вершин и удалены больше не используемые текстурные координаты. Нижние поверхности получили тёплый оранжевый оттенок, верхние — холодный серый. Это заранее заданная окраска, а не динамическое освещение лавой. Геометрия, нормали, индексы, габариты, центры, направления и существующие размещения дыма совпали с V23. Использован прежний общий материал цвета вершин; новых пикселей или авторских материалов нет. Старые файлы палитр оставлены и включены в вес карты.</p>
<p>На шести башнях размещён существующий бронзовый факел из пула. Его геометрия, четыре материала, изображения, анимация пламени и конфигурация искр переиспользуются без изменения. Факел и эффект уже присутствуют в установленном приложении: новые файлы факела не добавляются, карта хранит шесть координат и ссылки на библиотеку. Размер модели с реально используемыми изображениями не изменился, 0%. Конфигурация эффекта сохранена в Blender как исходный XML; это не утверждение о воспроизведении частиц в Blender.</p>
<table><tr><th>Модель дыма</th><th>Исходная модель с текстурой, байт</th><th>V24, байт</th><th>Изменение</th></tr>{rows}</table>
<table><tr><th>Вес</th><th>Результат</th></tr>
<tr><td>Карта + все новые общие игровые ресурсы, включая исторические варианты</td><td>{b['candidateIncludingNewSharedBytes']:,} байт</td></tr>
<tr><td>Интегрированный V1</td><td>{b['v1Bytes']:,} байт</td></tr>
<tr><td>Уменьшение относительно V1</td><td>{b['savingBytesVsV1']:,} байт; {b['savingBytesVsV1']/b['v1Bytes']*100:.2f}%</td></tr>
<tr><td>Изменение относительно V23</td><td>+{b['changeBytesAgainstIntermediateV23']:,} байт</td></tr>
<tr><td>Новые файлы факела в приложении</td><td>0 байт; существующая библиотека {b['directReusedExistingTorchRuntimeLibraryBytes']:,} байт переиспользована</td></tr></table>
<p>Верхний предел +20% проверен по весу каждой модели с используемой текстурой. Полигональная сетка этим процентом не ограничивается. Само полотно, исходные столкновения, сценарии и программные точки/линии сохранились. Независимая проверка габаритов новых факелов относительно 2&nbsp;032 защищённых треугольников дороги дала запас {b['independentTorchProtectedRoadSphereMarginMeters']:.3f} м. Все прочие файлы кандидата совпали с V23.</p>
<p>Blender открывается: активны 35 прототипов, 92 определения материалов и 339 общих частей. Проверены {native['newIndexedCornersChecked']:,} угла новых прототипов; остальные {native['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV23']} мешей совпали с V23 по геометрии, UV, нормалям, цветам, матрицам и материалам. Четыре определения материалов факела взяты из существующего пула. В каноническую библиотеку добавлены только три прототипа дыма, без новых материалов или изображений. В ведомости {audit['totalLedgerAssetsIncludingHistoricalSources']} ресурсов: реальные пути, хеши и зависимости проверены. Исправлен отсутствовавший индекс уже существующей конфигурации искр; её игровой файл не менялся.</p>
<p>Один полный круг Time Trial в симуляторе завершился естественным результатом <a href="screenshots/fidelity-v24-natural-finish.png">#1</a>, без принудительной победы. На кадре 40 карт на дороге; на <a href="screenshots/fidelity-v24-ramp-80.png">кадре 80</a> он летит под краем рампы; на кадре 140 вновь на дороге; результат снят на 190-й секунде. В исходном V1 уже наблюдалось опасное прохождение рампы. Причина не исправлена, все регрессии не исключены. Временные карты и скопированные ресурсы удалены из установленного приложения; донорские библиотеки и конфигурации эффекта совпадают с исходными байтами. Предупреждения материалов совпали с V23.</p>
<p>Все изображения сняты без ретуши. <a href="screenshots/fidelity-v24-overview.png">Общий диагностический вид из движка</a> показывает факелы и окраску дыма, но не является дорожным игровым кадром. Два игровых кадра приведены ниже.</p>
<p class="note">Точное сходство с референсом ещё не достигнуто. Большие каменные стены, повторяющиеся уступы, пропорции замка и композиция атмосферы требуют работы. Основная карта, итоговый пользовательский .blend и превью пока V1. Размер новой сборки приложения, производительность, обратный режим и вся кампания здесь не проверялись.</p>
<p><a href="../../volcano-remake-rework/fidelity-v24/native/Volcano%20Remake.blend">Blender V24</a> · <a href="evidence/fidelity-v24/atmosphere-changes.json">Дым и факелы</a> · <a href="evidence/fidelity-v24/preservation-verification.json">Вес и сохранность</a> · <a href="evidence/fidelity-v24/final-blend-verification.json">Проверка Blender</a> · <a href="evidence/fidelity-v24/runtime-validation.json">Игровой круг</a> · <a href="evidence/fidelity-v24/pool-audit.json">Общий пул</a></p>{''.join(figures)}</section>'''
page=out/'index.html'; s=re.sub(r'<section id="fidelity-v24-draft">.*?</section>','',page.read_text(),flags=re.S)
s=s.replace('Последняя доработка — V23','Предыдущая доработка — V23')
s=s.replace('<section id="fidelity-v23-draft">',section+'<section id="fidelity-v23-draft">',1); page.write_text(s)
manifest=out/'manifest.json'; m=json.loads(manifest.read_text())
m['files']=[{'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(out.rglob('*')) if f.is_file() and f!=manifest]
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for dest in [pack/'sources/volcano-remake-reference-v1/report',pack/'sources/volcano-remake-fidelity-v24/report']: shutil.copytree(out,dest,dirs_exist_ok=True)
shutil.copy2(Path(__file__),pack/'sources/volcano-remake-fidelity-v24'/Path(__file__).name)
progress=r.parent/'shared-placement-1-10/progress.json'; data=json.loads(progress.read_text())
data['maps']['10'].update({'status':'V24 retains stone pixels/UVs, warms smoke vertex colors and places six existing pooled torches. Native/canonical/ledger verified, natural one-lap #1. Unsafe ramp traversal remains observed. Reference fidelity unfinished; production/final/preview V1.',
    'candidate':str(w),'candidateTrackBytes':b['candidateMapBytes'],'candidateBytesIncludingNewSharedRuntime':b['candidateIncludingNewSharedBytes'],
    'candidateSavedBytesAgainstPrevious':b['savingBytesVsV1'],'candidateOneLapNaturalFinish':True,
    'lastFullLapVerifiedCandidate':'V24','lastFullLapNaturalFinish':True,'candidateProductionIntegrated':False,
    'candidateActiveNativePrototypes':35,'fullyAccepted':False})
data['goalComplete']=False; progress.write_text(json.dumps(data,ensure_ascii=False,indent=2))
plan=r/'next-fidelity-batch.json'; data=json.loads(plan.read_text()); data['baseCandidate']='V24'; data.pop('inProgressCandidate',None)
data['status']='V24 warm underside vertex colors and six direct pooled torches verified. Stone pixels/UVs retained. Total6612071B. Reference match unfinished; prioritize major wall silhouettes and castle composition. Ramp AI issue unresolved.'
for q in data['priorities']:
    if q['role']=='Rounded central cliff support and green terrain': q['remaining']='Keep stone texture. Preserve narrow roadside strips12/13/15. Prioritize massive stone-wall silhouettes, repeated cliff composition and castle proportions; do not raise road strips. V24 only atmosphere colors and existing torch placements.'
plan.write_text(json.dumps(data,indent=2))
print('V24_REPORT_UPDATED',len(m['files']),flush=True)
