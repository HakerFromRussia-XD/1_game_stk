from pathlib import Path
import hashlib,json,re,shutil,subprocess
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';out=r.parent/'fluxara-user-volcano-remake-final/report';e=out/'evidence/fidelity-v43';e.mkdir(exist_ok=True)
b=json.loads((w/'preservation-verification.json').read_text());n=json.loads((w/'final-blend-verification.json').read_text());i=json.loads((w/'integration-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());capture=json.loads((w/'integrated-drive-capture.json').read_text());assert len(capture['screenshots'])==2 and i['workingSourceIntegrated']
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((w/'candidate-asset-ledger.json').read_text());ledger.update({'productionIntegrated':True,'integration':i,'finalBlend':i['finalBlend'],'preservation':b,'budget':b,'runtimeValidation':run})
for target in [pool,ledger]:
 for q in target['objects']:
  if q['id']in ['volcano-fidelity-v43-continuous-terrain','volcano-fidelity-v43-continuous-terrain-runtime']:
   q['productionIntegrated']=True
   for use in q.get('uses',[]):
    if use.get('candidate')=='V43':use['status']='Integrated continuous source landscape restoration. Natural candidate TT finish observed; installed source views inspected. User visual approval pending.'
 target['assets']=target['objects']+target['materials']+target['textures']
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,e/f.name)
for dest,src in [('fidelity-v43-game-40.png','integrated/drive-40s.png'),('fidelity-v43-game-80.png','integrated/drive-80s.png'),('fidelity-v43-natural-finish.png','drive/drive-140s.png'),('fidelity-v43-overview.jpg','overview/preview.jpg')]:shutil.copy2(w/'screenshots'/src,out/'screenshots'/dest)
percent=b['savingVsV1Bytes']/b['v1Bytes']*100
section=f'''<section id="fidelity-v43-continuous-landscape"><h2>V43: возвращён цельный ландшафт v13–v14</h2>
<p>После замечания о парящих скалах восстановлены исходные соединённые каменные склоны и травяные поверхности V14. Вместо разрозненных столбов и отдельных островков возвращены 1508 каменных треугольников, 427 травяных и 72 треугольника центральной скалы. Ещё 702 исходных каменных треугольника уже находятся в основной модели и сохранены без дублирования. Камень и трава имеют 367 общих точек стыков исходной геометрии.</p>
<p>Убраны 329 размещений разрозненного окружения, включая каменные столбы, отдельные травяные крышки, холмики, дополнительные деревья и облака. 104 куста возвращены на исходные места V14. Сохранены текущие башни, крыши, факелы и вулканический дым. Прежние варианты и донорские модели остаются в общей библиотеке и архиве.</p>
<p>Полотно трассы и программные точки не менялись. Основной SPM побайтно совпадает с V42; исходные физические объекты, их материалы и положения сохранены. Восстановленная визуальная земля использует одну общую модель с размещением по координатам и взаимодействием ghost. Новые пиксели текстур не создавались; существующая каменная текстура сохранена. Извлечённая исходная модель и её UV-вариант имеют одинаковый вес. Новый прототип находится в физической общей библиотеке; проверены {len(pool['assets'])} уникальных ID.</p>
<p>Итоговый <a href="../Volcano%20Remake.blend">Volcano Remake.blend</a>, основные ресурсы карты, установленный iOS Simulator и превью обновлены. После повторного открытия Blender проверены 497 остальных сохранённых мешей и 394 остальных матрицы. Прежний итоговый файл сохранён вне папки результата.</p>
<p>Все файлы карты, принятая история общих игровых ресурсов и миниатюра кампании: <b>{b['allCandidateAndAcceptedHistoryBytes']:,} байт</b> против {b['v1Bytes']:,} исходных. Экономия <b>{percent:.2f}%</b>. Превью карты занимает {i['previewBytes']:,} байт, миниатюра — {i['campaignThumbnailBytes']:,} байт; обе включены в сумму. Новый размер сборки приложения не измерялся.</p>
<p>Обычный круг черновика завершился естественным финишем #1. После переноса сделаны и просмотрены два игровых кадра основной установленной карты — ниже. <a href="screenshots/fidelity-v43-overview.jpg">Обзор из игрового движка</a> · <a href="screenshots/fidelity-v43-natural-finish.png">Финиш</a> · <a href="evidence/fidelity-v43/preservation-verification.json">Сохранность и вес</a> · <a href="evidence/fidelity-v43/integration-verification.json">Интеграция</a>.</p>
<p class="note">Визуальное согласование этого исправления ещё не получено. Общая работа по картам 1–10 остаётся открытой. Карты 6–9 здесь не менялись; полный заезд карты 7 пользователь проверяет сам. Нижние разделы — история прежних вариантов.</p>
<figure><a href="screenshots/fidelity-v43-game-40.png"><img src="screenshots/fidelity-v43-game-40.png" alt="Соединённый ландшафт установленной карты V43"></a><figcaption>Склоны и зелёные поверхности вновь образуют общую землю вокруг дороги.</figcaption></figure>
<figure><a href="screenshots/fidelity-v43-game-80.png"><img src="screenshots/fidelity-v43-game-80.png" alt="Край трассы и склон V43"></a><figcaption>Подъём: исходная дорога сохранена, разрозненные парящие столбы убраны.</figcaption></figure></section>'''
page=out/'index.html';s=re.sub(r'<section id="fidelity-v43-continuous-landscape">.*?</section>','',page.read_text(),flags=re.S);s=s.replace('<section id="fidelity-v42-stone-scale">',section+'<section id="fidelity-v42-stone-scale">',1);s=re.sub(r'<div class="tags">.*?</div>',f'<div class="tags"><span>Цельный ландшафт V43</span><span>Вес −{percent:.2f}% к V1</span><span>193 общих части</span></div>',s,count=1,flags=re.S);page.write_text(s)
progress=r.parent/'shared-placement-1-10/progress.json';a=json.loads(progress.read_text());a['maps']['10'].update({'status':'V43 contiguous original V14 cliff/grass restoration integrated into source, simulator, sole final Blender and matching preview. Main model/control/physics unchanged. 329 scattered decorative placements removed;104 bush poses restored. Visual approval pending.','candidate':str(w),'candidateTrackBytes':b['candidateAllFilesBytes'],'candidateBytesIncludingNewSharedRuntime':b['allCandidateAndAcceptedHistoryBytes'],'candidateSavedBytesAgainstPrevious':b['savingVsV1Bytes'],'lastFullLapVerifiedCandidate':'V43 candidate','lastFullLapNaturalFinish':True,'candidateProductionIntegrated':True,'candidateRegisteredNativePrototypes':56,'candidateNativeSharedParts':193,'candidateRoundedCliffPlacements':0,'candidateAdditionalLargeCliffGroups':0,'candidateAdditionalLeafTrees':0,'newCoordinateHillPlacements':0,'candidateAdditionalGreeneryInstances':0,'removedScatteredLandscapePlacements':329,'fullyAccepted':False,'previewPath':i['preview']});a['goalComplete']=False;progress.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();manifest=out/'manifest.json';m=json.loads(manifest.read_text());m['files']=[{'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted(out.rglob('*'))if f.is_file()and f!=manifest];manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2))
def clone(src,dst):
 dst=Path(dst)
 if dst.exists():
  if Path(src).read_bytes()==dst.read_bytes():return str(dst)
  dst.unlink()
 subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True);return str(dst)
arc=pack/'sources/volcano-remake-fidelity-v43'
for folder in ['candidate','native','screenshots','shared-runtime']:shutil.copytree(w/folder,arc/folder,dirs_exist_ok=True,copy_function=clone)
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,arc/f.name)
for f in r.glob('*fidelity_v43*.py'):shutil.copy2(f,arc/f.name)
for f in r.glob('fidelity-v43*.log'):shutil.copy2(f,arc/f.name)
for dst in [pack/'sources/volcano-remake-reference-v1/report',arc/'report']:shutil.copytree(out,dst,dirs_exist_ok=True,copy_function=clone)
print('V43_CONTINUOUS_LANDSCAPE_REPORT_AND_ARCHIVES_SAVED',len(m['files']),flush=True)
