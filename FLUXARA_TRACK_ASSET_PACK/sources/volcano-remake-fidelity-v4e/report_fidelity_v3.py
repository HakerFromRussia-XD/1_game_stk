from pathlib import Path
import hashlib,json,re,shutil
from urllib.parse import unquote,urlsplit
r=Path(__file__).resolve().parent;w=r/'fidelity-v3';out=r.parent/'fluxara-user-volcano-remake-final/report';page=out/'index.html'
history=w/'report-history';history.mkdir(exist_ok=True)
shutil.copy2(page,history/(hashlib.sha256(page.read_bytes()).hexdigest()[:12]+'-index.html'))
evidence=out/'evidence/fidelity-v3';evidence.mkdir(parents=True,exist_ok=True)
for name in ['changes.json','preservation.json','budget.json','runtime-validation.json','drive-capture.json','stationary-approach-capture.json','production-preservation.json','final-blend-verification.json','canonical-bindings-verification.json','sky-projection.json','imagegen-prompt.txt']:
 shutil.copy2(w/name,evidence/name)
for name in ['approach-15s.png','drive-12s.png','drive-40s.png','drive-80s.png','drive-150s.png','castle-wide.png']:
 shutil.copy2(w/'screenshots'/name,out/'screenshots'/('fidelity-v3-'+name))
b=json.loads((w/'budget.json').read_text())
section=f'''<section id="fidelity-v3-draft"><h2>Доработка V3 — небо и свечение у входа</h2>
<p>Создано отдельное тёплое небо с голубым верхом, золотистым горизонтом и розовыми облаками. Панорама преобразована в шесть граней куба 512×512; четыре боковых стыка проверены по совпадению направлений и исходных пикселей до JPEG-сжатия. Это не подтверждает идеальный горизонтальный стык исходной генерации или все стыки куба.</p>
<p>Яркость цветов вершин двух декоративных свечений снижена до 12% и 8%. Их геометрия, размеры, центры, UV и коллизии сохранены; материалы остаются аддитивными и игнорируемыми физикой. Вся геометрия V3 совпадает с V2, все игровые XML и текстуры покрытия совпадают побайтно.</p>
<p>Вес черновика <strong>{b['candidateTrackBytes']:,} байт</strong>, на {b['savedBytesAgainstPrevious']:,} байт меньше основной версии V1. Новых общих игровых библиотек нет. {b['candidateTriangles']:,} треугольник, +{b['triangleChangePercentAgainstOriginal']:.2f}% к исходной карте.</p>
<p>Один круг Time Trial с одной машиной завершился естественным финишем #1 в iOS Simulator. Первый кадр ниже снят с игровой камеры у старта без AI-движения; второй — из заезда с AI. Целевая задержка снимка по системным часам не равна точному показанию игрового таймера.</p>
<p class="note">V3 сохраняется отдельно: основная карта, её итоговый Blender-проект и превью кампании пока используют V1. Карта ещё не завершена: дым остаётся угловатым и чрезмерно крупным, крупные замковые формы и лавовые шипы отличаются от референса. Полный заезд кампании, обратное направление и производительность этой проверкой не подтверждены.</p>
<p><a href="../../volcano-remake-rework/fidelity-v3/native/Volcano%20Remake.blend">Редактируемый черновик V3</a> · <a href="evidence/fidelity-v3/preservation.json">Сохранность геометрии</a> · <a href="evidence/fidelity-v3/budget.json">Вес и полигоны</a> · <a href="evidence/fidelity-v3/runtime-validation.json">Проверка заезда</a></p>
<figure><a href="screenshots/fidelity-v3-approach-15s.png"><img src="screenshots/fidelity-v3-approach-15s.png" alt="V3: игровая камера у въезда"></a><figcaption><strong>V3: игровая камера у въезда</strong><span>Машина стоит у старта; свечение больше не закрывает каменную арку.</span></figcaption></figure>
<figure><a href="screenshots/fidelity-v3-drive-40s.png"><img src="screenshots/fidelity-v3-drive-40s.png" alt="V3: поворот с лавой и тёплым небом"></a><figcaption><strong>V3: поворот у лавы</strong><span>Новые цвета неба; угловатый дым виден и требует следующей доработки.</span></figcaption></figure>
<p>Сохранены <a href="screenshots/fidelity-v3-drive-80s.png">верхняя часть маршрута</a>, <a href="screenshots/fidelity-v3-drive-150s.png">естественный финиш</a> и <a href="screenshots/fidelity-v3-castle-wide.png">отдельный статический обзор в движке</a>. Небо создано встроенным imagegen; <a href="evidence/fidelity-v3/imagegen-prompt.txt">точный запрос</a> сохранён. Донорское небо других карт не изменено.</p></section>'''
s=re.sub(r'<section id="fidelity-v3-draft">.*?</section>','',page.read_text(),flags=re.S)
s=s.replace('<h2>Референс</h2>',section+'<h2>Референс</h2>',1);page.write_text(s)
missing=[link for link in re.findall(r'(?:src|href)="([^"]+)"',s) if not urlsplit(link).scheme and not link.startswith('#') and not (out/unquote(link.split('#')[0])).exists()]
assert not missing,missing
(out/'manifest.json').write_text(json.dumps({'brokenLocalLinks':missing,'files':[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']},indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for prefix in ['volcano-remake-reference-v1','volcano-remake-fidelity-v2','volcano-remake-fidelity-v3']:
 shutil.copytree(out,pack/'sources'/prefix/'report',dirs_exist_ok=True)
sources=pack/'sources/volcano-remake-fidelity-v3'
for p in w.glob('*.json'):
 if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
shutil.copytree(w/'screenshots',sources/'screenshots',dirs_exist_ok=True)
shutil.copy2(r/'capture_fidelity_v3_stationary.py',sources/'capture_fidelity_v3_stationary.py')
shutil.copy2(Path(__file__),sources/Path(__file__).name)
print('V3_REPORT_UPDATED',page)
