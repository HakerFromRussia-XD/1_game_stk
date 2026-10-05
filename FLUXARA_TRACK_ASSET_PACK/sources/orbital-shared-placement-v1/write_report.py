from pathlib import Path
import datetime, json, shutil

r=Path(__file__).resolve().parent
w=r/'delivery-v1'
root=r.parent.parent
final=r.parent/'fluxara-user-orbital-soccer-final'
report=final/'report'
(report/'screenshots').mkdir(parents=True,exist_ok=True)
evidence=report/'evidence/coordinate-reuse'
evidence.mkdir(parents=True,exist_ok=True)
weights=json.loads((w/'weight.json').read_text())
for f in (w/'screenshots/candidate').glob('*.jpg'):
    shutil.copy2(f,report/'screenshots'/('coordinate-'+f.name))
for name in ['weight.json','native-verification.json','canonical-reuse-verification.json','preservation.json','asset-registration.json','integration.json','screenshots.json']:
    shutil.copy2(w/name,evidence/name)
for sec in [22,40]:
    f=r.parent/f'orbital-soccer-rework/approved-v5/screenshots/v5-game-{sec}s.png'
    shutil.copy2(f,report/'screenshots'/f.name)
shutil.copy2(r.parent/'orbital-soccer-rework/approved-version.json',evidence/'approved-version-v5.json')
fmt=lambda x:f'{x:,}'.replace(',',' ')
rows=[('Исходные ресурсы карты',weights['originalBytes']),('Карта с новым превью',weights['candidateOwnBytes']),('Два общих экспорта, XML и два алиаса текстуры',weights['newSharedGameBytes']),('Новое превью кампании, учтено целиком',weights['campaignThumbnailBytesChargedInFull']),('Итог с новыми общими ресурсами и превью',weights['candidateTotalBytes']),('Уменьшение',weights['savingBytes'])]
table=''.join(f'<tr><td>{label}</td><td>{fmt(value)}</td></tr>' for label,value in rows)
html=f'''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Карта 5 — ORBITAL</title><style>body{{background:#102237;color:#e7f3ff;font:17px/1.55 system-ui;margin:0}}main{{max-width:1080px;margin:auto;padding:32px}}h1{{line-height:1.2}}img{{width:100%;border-radius:16px}}figure{{margin:28px 0}}figcaption{{color:#abc7df}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #41617c;padding:10px;text-align:left}}a{{color:#79dfff}}</style><main>
<p>FLUXARA DRIFT · КАРТА 05 · 02.10.2026</p><h1>ORBITAL Simulation — Soccer</h1>
<p>Сохранён согласованный вид V5. Шесть существующих экземпляров светильников и боковых панелей модуля переведены в две общие модели. Добавлены 14 таких же светильников вдоль двух существующих бордюров. Всего 20 частей размещаются по координатам.</p>
<p>Кольца, модуль, лунное окружение и все исходные размеры, центры и направления сохранены. Нижняя часть новых светильников заглублена в бордюр на 4 сантиметра. Полотно, навигационная сетка, программные точки и линии, ворота, игровые объекты и скрипты сохранены.</p>
<p>Геометрия и изображения двух моделей взяты из существующей физической библиотеки без переделки. Новых пикселей текстур моделей нет. Два алиаса по 158 байт сохраняют разные настройки материала: светильник — unlit, панели модуля — solid. 168 повторявшихся треугольников заменены экземплярами общих моделей. Основное уменьшение веса получено техническим уменьшением прежнего крупного превью; экономия от самого извлечения этих малых моделей невелика.</p>
<table><tr><th>Ресурсы этапа</th><th>Байты</th></tr>{table}</table><p>Общее уменьшение: {weights['savingPercent']:.2f}%. В расчёт входят все новые общие игровые файлы и целиком новое превью кампании. Файлы Blender и отчёта в размер игровых ресурсов не включены.</p>
<p>Изменения сохранены в проекте, ресурсах установленного приложения iOS Simulator и единственном итоговом файле Blender. Превью карты и кампании заменены кадром текущей сцены. Новая сборка приложения и новые заезды или проверки выезда не выполнялись.</p>
<figure><img src="screenshots/coordinate-overview.jpg"><figcaption>Текущая сцена: дополнительные огни на бордюрах. Статичная камера игрового движка; кадр используется для превью.</figcaption></figure>
<figure><img src="screenshots/coordinate-ring.jpg"><figcaption>Сохранённые кольца и модуль согласованной V5. Статичная камера игрового движка.</figcaption></figure>
<p><a href="evidence/coordinate-reuse/weight.json">Вес</a> · <a href="evidence/coordinate-reuse/integration.json">Сохранение</a> · <a href="evidence/coordinate-reuse/approved-version-v5.json">Согласованная V5</a></p>
<details><summary>Игровые кадры ранее согласованной V5, до добавления огней</summary><figure><img src="screenshots/v5-game-22s.png"><figcaption>Архивный кадр футбольной игры V5, 22 секунды. Не является новым заездом.</figcaption></figure><figure><img src="screenshots/v5-game-40s.png"><figcaption>Архивный кадр футбольной игры V5, 40 секунд. Не является новым заездом.</figcaption></figure></details></main></html>'''
(report/'index.html').write_text(html)
lp=root/'fluxara-user-orbital-simulation---soccer.asset-ledger.json'
ledger=json.loads(lp.read_text())
ledger['coordinateReusePhase']['screenshots']=json.loads((w/'screenshots.json').read_text())
repo=Path('/Users/motoricallc/Downloads/fluxara-drift')
pp=repo/'FLUXARA_TRACK_ASSET_POOL.json'
pool=json.loads(pp.read_text())
for rows in [pool['objects'],pool['assets'],ledger['assets']]:
    for q in rows:
        if q['id']=='orbital-soccer-runtime-v5':
            if 'runtimeResourceSourcePath' in q:q['previousRuntimeResourceSourcePath']=q.pop('runtimeResourceSourcePath')
            if 'runtimePath' in q:q['previousRuntimePath']=q.pop('runtimePath')
            q['status']='Historical approved V5 baked assembly; current resources use coordinate extraction.'
            q['currentRemainderAssetId']='orbital-shared-v1-baked-remainder'
            for use in q.get('uses',[]):
                if use.get('trackId')=='fluxara-user-orbital-simulation---soccer':use['status']='Historical V5 assembly; replaced by current baked remainder and shared placements.'
pool['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
progressPath=r.parent/'shared-placement-1-10/progress.json'
progress=json.loads(progressPath.read_text())
progress['maps']['5']={'trackId':'fluxara-user-orbital-simulation---soccer','status':'Approved V5 preserved; six existing shared parts and fourteen additional curb lamps integrated. Preview and report saved.','sourceAndInstalledIntegrated':True,'storageConversionInstances':6,'uniqueModels':2,'newLightInstances':14,'totalCoordinateParts':20,'newSharedGameBytes':weights['newSharedGameBytes'],'originalWeightBytes':weights['originalBytes'],'trackPlusNewSharedAndCampaignPreviewBytes':weights['candidateTotalBytes'],'savingBytes':weights['savingBytes'],'report':str(report/'index.html'),'newDrivingTestPerformed':False,'newBuildPerformed':False,'originalStyleApproval':'V5','newPlacementsIndividuallyApproved':False}
progress['stage']='Map 5 coordinate enrichment, preview and report saved. Cross-map work remains active.'
progress['goalComplete']=False
progressPath.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
archive=repo/'FLUXARA_TRACK_ASSET_PACK/sources/orbital-shared-placement-v1'
archive.mkdir(parents=True,exist_ok=True)
for f in r.glob('*.py'):shutil.copy2(f,archive/f.name)
for f in w.glob('*.json'):shutil.copy2(f,archive/f.name)
for name in ['orbital-extraction.json','orbital-match.json']:shutil.copy2(r/name,archive/name)
shutil.copytree(report,archive/'report',dirs_exist_ok=True)
shutil.copy2(lp,archive/lp.name)
print('ORBITAL_REPORT_AND_PROGRESS_SAVED',weights['savingBytes'],flush=True)
