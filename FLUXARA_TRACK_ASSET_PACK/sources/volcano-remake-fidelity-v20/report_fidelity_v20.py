from pathlib import Path
import json, shutil, re, hashlib

r=Path(__file__).resolve().parent; w=r/'fidelity-v20'
out=r.parent/'fluxara-user-volcano-remake-final/report'
e=out/'evidence/fidelity-v20'; e.mkdir(exist_ok=True)
b=json.loads((w/'preservation-verification.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text())
audit=json.loads((w/'pool-audit.json').read_text())
assert run['naturalFinishObserved'] and run['visualInspectionCompleted']
assert audit['newNativePrototypes']==1 and audit['newTextures']==1 and not audit['newImagePixels']
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'): shutil.copy2(p,e/p.name)
figures=[]
for second,caption in [(40,'Каменная фактура и прежний решётчатый участок сохранены.'),(80,'Замковый участок: фактура камня сохранена, дорога и ускоритель прежние.')]:
    name=f'fidelity-v20-game-{second}.png'
    shutil.copy2(w/f'screenshots/drive-{second}s.png',out/'screenshots'/name)
    figures.append(f'<figure><a href="screenshots/{name}"><img src="screenshots/{name}" alt="Игровой кадр V20"></a><figcaption>iOS Simulator. {caption}</figcaption></figure>')
static='fidelity-v20-terrain-overview.png'; finish='fidelity-v20-natural-finish.png'
shutil.copy2(w/'screenshots/smoke-diagnostic-all.png',out/'screenshots'/static)
shutil.copy2(w/'screenshots/natural-finish.png',out/'screenshots'/finish)
section=f'''<section id="fidelity-v20-draft"><h2>Последняя доработка — V20: объём зелёных площадок с сохранением фактуры камня</h2>
<p>Сохранены текущие пиксели каменной текстуры, UV, нормали, цвета и геометрия каменных поверхностей V19. По замечанию пользователя «С текстурой камня было лучше» камень не заменён плоским цветом. Эта фактура — сохранённый вариант V19 размером 39&nbsp;938 байт; она не является исходным до переделки изображением Rock13_col.jpg размером 1&nbsp;065&nbsp;543 байта.</p>
<p>16 из 33 компонентов зелёного декоративного ландшафта получили дополнительный объём: 427 исходных треугольников преобразованы в 1&nbsp;800 визуальных треугольников, подняты 552 вершины. Границы площадок, общий локальный габарит, начало координат и оси сохранены; подъём ограничен расстоянием до дороги. Независимая проверка реального расстояния между изменёнными гранями и 2&nbsp;032 защищёнными треугольниками проезда дала минимум {b['independentChangedFaceRoadTriangleMarginMeters']:.3f} м. Исходные столкновения сохранены отдельной точной моделью из всех 427 треугольников с прежними индексами, UV, нормалями и цветами. Дорога и игровые точки/линии не изменены.</p>
<p>Декоративный ландшафт находится в одном общем игровом файле модели и размещается одной записью координат. Переиспользована прежняя зелёная палитра: добавлен один общий файл с новым именем, но с теми же пикселями, без нового материала или нового изображения в Blender. Имена текстуры в заголовках трёх вулканических SPM заменены на этот общий файл; геометрия и все их атрибуты побайтно совпадают с V19. Центральная площадка из восьми граней пока не переделана. 58 уступов, 32 холма и клубы дыма V19 сохранены.</p>
<table><tr><th>Измерение</th><th>Результат</th></tr>
<tr><td>Исходная модель выделенного участка с исходной текстурой до переделки</td><td>{b['originalComponentWithTextureBytes']:,} байт</td></tr>
<tr><td>Новая видимая модель + точная модель столкновений + реально используемая палитра</td><td>{b['adaptedVisibleAndCollisionModelsWithTextureBytes']:,} байт; {b['componentWithTextureChangePercent']:.2f}%</td></tr>
<tr><td>Карта со всеми добавленными общими игровыми ресурсами, включая старые собственные варианты</td><td>{b['candidateIncludingNewSharedBytes']:,} байт</td></tr>
<tr><td>Исходный интегрированный V1</td><td>{b['v1Bytes']:,} байт</td></tr>
<tr><td>Уменьшение относительно V1</td><td>{b['savingBytesVsV1']:,} байт; {b['savingBytesVsV1']/b['v1Bytes']*100:.2f}%</td></tr>
<tr><td>Изменение относительно промежуточного V19</td><td>+{b['changeBytesAgainstIntermediateV19']:,} байт</td></tr></table>
<p>Предел +20% относится к весу модели с текстурой. Число полигонов не ограничивалось ±20%. Для исходного участка взята геометрия, сопоставленная с оригинальной моделью до переделки, и её исходная текстура размером 1&nbsp;065&nbsp;543 байта; сравнение не подменено промежуточной палитрой V19. Вес приложения этой проверкой не измерялся.</p>
<p>Blender повторно открыт и проверен: 603 прочих меша сохранили геометрию, UV, нормали, цвета, матрицы и материалы; исходный зелёный меш точно скопирован в скрытую модель столкновений. Проверены 5&nbsp;400 углов новых полигонов, все 332 общие части и 180 навигационных квадов. Один новый прототип зарегистрирован в канонической библиотеке; {audit['totalLedgerAssetsIncludingHistoricalSources']} ресурсов ведомости имеют реальные файлы, проверенные хеши и зависимости. Старые предупреждения о текстурах движка остались теми же, новых не добавлено.</p>
<p>Выполнен один полный круг Time Trial в симуляторе: seed 4, один карт, естественный результат <a href="screenshots/{finish}">#1</a>, без принудительной победы. Ниже два настоящих игровых кадра. <a href="screenshots/{static}">Общий диагностический вид в движке</a> показывает формы окружения. Скриншоты сохранены без ретуши; временная карта и её временные ресурсы удалены из установленного приложения.</p>
<p class="note">Доработка изолирована: основная карта, итоговый пользовательский .blend и превью ещё V1. Соответствие референсу не завершено: передняя центральная зелёная площадка, плоские компоненты рядом с дорогой, круглые шапки уступов, пропорции замка и освещение ещё требуют работы. Улучшение дальних форм не считается исправлением этих участков. Нет заявления о новой сборке приложения, производительности, обратном режиме или полной проверке кампании.</p>
<p><a href="../../volcano-remake-rework/fidelity-v20/native/Volcano%20Remake.blend">Blender V20</a> · <a href="evidence/fidelity-v20/terrain-changes.json">Геометрия ландшафта</a> · <a href="evidence/fidelity-v20/preservation-verification.json">Вес и сохранность</a> · <a href="evidence/fidelity-v20/final-blend-verification.json">Проверка Blender</a> · <a href="evidence/fidelity-v20/runtime-validation.json">Игровой круг</a> · <a href="evidence/fidelity-v20/pool-audit.json">Общий пул</a></p>{''.join(figures)}</section>'''
page=out/'index.html'; s=re.sub(r'<section id="fidelity-v20-draft">.*?</section>','',page.read_text(),flags=re.S)
s=s.replace('<section id="fidelity-v19-draft">',section+'<section id="fidelity-v19-draft">',1).replace('Последняя доработка — V19','Предыдущая доработка — V19'); page.write_text(s)
manifest=out/'manifest.json'; m=json.loads(manifest.read_text())
m['files']=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(out.rglob('*'))if p.is_file()and p!=manifest]
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for dest in [pack/'sources/volcano-remake-reference-v1/report',pack/'sources/volcano-remake-fidelity-v20/report']: shutil.copytree(out,dest,dirs_exist_ok=True)
shutil.copy2(Path(__file__),pack/'sources/volcano-remake-fidelity-v20'/Path(__file__).name)
progress=r.parent/'shared-placement-1-10/progress.json'; d=json.loads(progress.read_text())
d['maps']['10'].update({'status':'V20 rounds 16 green terrain components, exact source collision geometry retained, current stone texture/UVs unchanged. Native/canonical verified, natural one-lap TT #1. Central near-road forms still unfinished; production/final/preview V1.',
                        'candidate':str(w),'candidateTrackBytes':b['candidateMapBytes'],'candidateBytesIncludingNewSharedRuntime':b['candidateIncludingNewSharedBytes'],
                        'candidateSavedBytesAgainstPrevious':b['savingBytesVsV1'],'candidateOneLapNaturalFinish':True,'lastFullLapVerifiedCandidate':'V20',
                        'lastFullLapNaturalFinish':True,'candidateProductionIntegrated':False,'candidateActiveNativePrototypes':33,'fullyAccepted':False})
d['goalComplete']=False; progress.write_text(json.dumps(d,ensure_ascii=False,indent=2))
plan=r/'next-fidelity-batch.json'; d=json.loads(plan.read_text()); d['baseCandidate']='V20'
d['status']='V20 rounds 16 large green components, retains original collision mesh and current stone pixels/UVs. Weight 6533910B. Central/near-road forms and atmosphere unfinished.'
for q in d['priorities']:
    if q['role']=='Rounded central cliff support and green terrain':
        q.update({'completedCandidate':'V20 partial', 'done':'16 of 33 green components rounded using one shared ghost model; original 427 collision faces retained exact; independent changed-face road clearance 5.336m.',
                  'remaining':'Central 8-face crest (V19 buffer 3) and near-road terrain components 12/13/15 remain planar. 58 disc-capped cliffs still differ from reference. Address these actual large foreground forms next; distant relief alone is insufficient.'})
plan.write_text(json.dumps(d,indent=2))
print('V20_REPORT_TWO_GAME_FRAMES_AND_FULL_LAP_UPDATED',len(m['files']),flush=True)
