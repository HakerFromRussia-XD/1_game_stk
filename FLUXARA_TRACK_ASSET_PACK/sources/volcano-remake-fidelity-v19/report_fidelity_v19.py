from pathlib import Path
import json, shutil, re, hashlib

r=Path(__file__).resolve().parent; w=r/'fidelity-v19'
out=r.parent/'fluxara-user-volcano-remake-final/report'
e=out/'evidence/fidelity-v19'; e.mkdir(exist_ok=True)
b=json.loads((w/'preservation-verification.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text())
audit=json.loads((w/'pool-audit.json').read_text())
assert run['naturalFinishObserved'] and run['visualInspectionCompleted']
assert audit['replacementMapModels']==3 and audit['newTextures']==0
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'): shutil.copy2(p,e/p.name)
figures=[]
for second,caption in [(40,'Исходная фактура камня, решётчатый участок и лава. Новый дым частично виден слева.'),(80,'Замковый участок и ускоритель: прежняя геометрия трассы и каменная фактура сохранены.')]:
    name=f'fidelity-v19-game-{second}.png'
    shutil.copy2(w/f'screenshots/drive-{second}s.png',out/'screenshots'/name)
    figures.append(f'<figure><a href="screenshots/{name}"><img src="screenshots/{name}" alt="Игровой кадр V19"></a><figcaption>iOS Simulator. {caption}</figcaption></figure>')
static='fidelity-v19-smoke-overview.png'; finish='fidelity-v19-natural-finish.png'
shutil.copy2(w/'screenshots/smoke-diagnostic-all.png',out/'screenshots'/static)
shutil.copy2(w/'screenshots/natural-finish.png',out/'screenshots'/finish)
rows=''.join(f"<tr><td>{q['model']}</td><td>{q['sourceBytesWithTexture']:,} → {q['adaptedBytesWithTexture']:,} байт; {q['changePercent']:.2f}%</td><td>{q['triangles']} треугольников, {q['vertices']} вершин</td></tr>"for q in b['smoke'])
section=f'''<section id="fidelity-v19-draft"><h2>Последняя доработка — V19: связные клубы вулканического дыма</h2>
<p>Три объёмных эффекта AshCloud, AshColumn и PyroclasticFlow переделаны из раздельных шаров в связные неровные шлейфы. Форма получена объединением перекрывающихся объёмов с последующим уменьшением числа треугольников. Каждый эффект — одна замкнутая поверхность. Существующие материалы и пиксели дымовой палитры переиспользованы; новых текстур и материалов нет. Положение, поворот, масштаб, начало координат, оси и фактические локальные габариты каждого эффекта совпадают с V18.</p>
<p>Каменная текстура и прежние UV сохранены. Все остальные файлы карты побайтно совпадают с V18, включая основной SPM, дорогу, столкновения, расстановку, текстуры, навигацию, игровые точки/линии и сценарии. 58 уступов и 32 зелёных холма по координатам сохранены.</p>
<table><tr><th>Модель</th><th>Вес с текстурой относительно исходного V1</th><th>Сетка V19</th></tr>{rows}</table>
<p>Верхний предел +20% проверен по весу каждой исходной модели с её реально используемой текстурой. Число полигонов не ограничивалось ±20%. Относительно промежуточного V18 эти модели стали детальнее и суммарно тяжелее на 19&nbsp;061 байт; это включено в итоговый вес. Карта со всеми добавленными общими игровыми ресурсами и сохранёнными ранними вариантами весит <strong>{b['candidateIncludingNewSharedBytes']:,} байт</strong> против {b['v1Bytes']:,} байт V1: уменьшение на {b['savingBytesVsV1']:,} байт ({b['savingBytesVsV1']/b['v1Bytes']*100:.2f}%). Вес приложения этим измерением не определяется.</p>
<p>Повторное открытие Blender подтвердило неизменность геометрии, UV, нормалей, цветов, матриц и материалов 595 прочих мешей. Проверены 7&nbsp;980 углов новых полигонов; все 331 общие части и 180 навигационных квадов сохранены. Три новых прототипа зарегистрированы в канонической библиотеке с прежними материалами. Все {audit['totalLedgerAssetsIncludingHistoricalSources']} ресурсов ведомости, физические пути, хеши и зависимости проверены.</p>
<p>Выполнен полный круг Time Trial: один карт, один круг, seed 4, естественный результат <a href="screenshots/{finish}">#1</a>, без принудительной победы. Ниже два реальных игровых кадра. Полный силуэт дыма виден на <a href="screenshots/{static}">общем диагностическом виде из движка</a>. Скриншоты сохранены без ретуши. Временные ресурсы пробного запуска удалены из установленного приложения.</p>
<p>Первый гладкий вариант выглядел трубой и отвергнут после просмотра в движке. Дефекты сетки в следующих пробах выявлены проверками до сохранения замены; эти пробы находятся только в архиве итераций. Текущий вариант прошёл независимую проверку замыкания, связности, направления граней, габаритов и веса.</p>
<p class="note">Визуальное соответствие референсу ещё не завершено: остаются широкие плоские зелёные поверхности, пропорции скал и замкового окружения, освещение дыма и атмосфера. Основная карта, итоговый пользовательский .blend и превью пока V1. Нет заявления о новой сборке приложения, производительности, обратном режиме или полной проверке кампании.</p>
<p><a href="../../volcano-remake-rework/fidelity-v19/native/Volcano%20Remake.blend">Blender V19</a> · <a href="evidence/fidelity-v19/smoke-changes.json">Модели дыма</a> · <a href="evidence/fidelity-v19/preservation-verification.json">Вес и сохранность</a> · <a href="evidence/fidelity-v19/final-blend-verification.json">Проверка Blender</a> · <a href="evidence/fidelity-v19/runtime-validation.json">Полный игровой круг</a> · <a href="evidence/fidelity-v19/pool-audit.json">Общий пул</a></p>{''.join(figures)}</section>'''
page=out/'index.html'; s=re.sub(r'<section id="fidelity-v19-draft">.*?</section>','',page.read_text(),flags=re.S)
s=s.replace('<section id="fidelity-v18-draft">',section+'<section id="fidelity-v18-draft">',1).replace('Последняя доработка — V18','Предыдущая доработка — V18'); page.write_text(s)
manifest=out/'manifest.json'; m=json.loads(manifest.read_text())
m['files']=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(out.rglob('*'))if p.is_file()and p!=manifest]
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for dest in [pack/'sources/volcano-remake-reference-v1/report',pack/'sources/volcano-remake-fidelity-v19/report']: shutil.copytree(out,dest,dirs_exist_ok=True)
shutil.copy2(Path(__file__),pack/'sources/volcano-remake-fidelity-v19'/Path(__file__).name)
progress=r.parent/'shared-placement-1-10/progress.json'; d=json.loads(progress.read_text())
d['maps']['10'].update({'status':'V19 continuous closed smoke billows, no new textures/materials, source bounds/origins/axes/placements and all other V18 files preserved. Native/canonical verified, one-lap natural TT #1. Reference work unfinished; production/final/preview V1.',
                        'candidate':str(w),'candidateTrackBytes':b['candidateMapBytes'],'candidateBytesIncludingNewSharedRuntime':b['candidateIncludingNewSharedBytes'],
                        'candidateSavedBytesAgainstPrevious':b['savingBytesVsV1'],'candidateOneLapNaturalFinish':True,'lastFullLapVerifiedCandidate':'V19',
                        'lastFullLapNaturalFinish':True,'candidateProductionIntegrated':False,'candidateActiveNativePrototypes':32,'fullyAccepted':False})
d['goalComplete']=False; progress.write_text(json.dumps(d,ensure_ascii=False,indent=2))
plan=r/'next-fidelity-batch.json'; d=json.loads(plan.read_text()); d['baseCandidate']='V19'
d['status']='V19 continuous closed billowing smoke, source bounds and ghost placements retained; all other V18 files exact. Weight 6490579B. Large terrain silhouette and atmosphere unfinished.'
for q in d['priorities']:
    if q['role']=='Volcanic smoke':
        q.update({'completedCandidate':'V19','done':'Three single connected closed surfaces with overlapping irregular billows. Existing smoke palette pixels and material reused; source boxes/origins/axes/placements retained.',
                  'remaining':'Lighting and warm eruption glow still differ from reference. Overall plume composition needs final gameplay/reference acceptance.'})
    if q['role']=='Rounded central cliff support and green terrain':
        q['remaining']='Large planar green faces and disconnected cylindrical caps remain the main visual mismatch. Next pass must improve the large forms around protected route; adding small mounds alone is insufficient.'
plan.write_text(json.dumps(d,indent=2))
print('V19_REPORT_TWO_GAME_FRAMES_AND_FULL_LAP_UPDATED',len(m['files']),flush=True)
