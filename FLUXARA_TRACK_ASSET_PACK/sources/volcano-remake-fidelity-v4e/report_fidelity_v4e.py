from pathlib import Path
import hashlib,json,re,shutil
from urllib.parse import unquote,urlsplit
r=Path(__file__).resolve().parent;w=r/'fidelity-v4e';out=r.parent/'fluxara-user-volcano-remake-final/report';page=out/'index.html'
history=w/'report-history';history.mkdir(exist_ok=True);shutil.copy2(page,history/(hashlib.sha256(page.read_bytes()).hexdigest()[:12]+'-index.html'))
evidence=out/'evidence/fidelity-v4e';evidence.mkdir(parents=True,exist_ok=True)
for name in ['changes.json','preservation.json','budget.json','runtime-validation.json','drive-capture.json','final-blend-verification.json','canonical-bindings-verification.json','pool-audit.json','imagegen-prompt.txt']:
 shutil.copy2(w/name,evidence/name)
for name in ['drive-12s.png','drive-40s.png','drive-80s.png','drive-150s.png']:
 shutil.copy2(w/'screenshots'/name,out/'screenshots'/('fidelity-v4e-'+name))
b=json.loads((w/'budget.json').read_text())
section=f'''<section id="fidelity-v4e-draft"><h2>Текущая доработка V4E — пять дымовых эффектов</h2>
<p>Пять декоративных дымовых моделей получили перекрывающиеся двусторонние плоскости с целым прозрачным изображением клубов. Исходные внешние границы, локальные центры, начала координат, направления, масштабы и число треугольников каждого из этих мешей сохранены. Их форма и UV изменены. Восемь старых анимаций смещения текстуры удалены только у ghost-эффектов; анимации движения, поворота и масштаба сохранены.</p>
<p>Прозрачный спрайт создан встроенным imagegen, затем технически уменьшен до RGBA 256×256. Вместо непрозрачных прямоугольников в игре видны клубы дыма. Освещаемый материал и большее перекрытие сделали их плотнее, чем в промежуточных опытах. <a href="evidence/fidelity-v4e/imagegen-prompt.txt">Точный запрос генерации</a> сохранён.</p>
<p>Папка кандидата: <strong>{b['candidateTrackBytes']:,} байт</strong>, на {b['savedBytesAgainstPrevious']:,} байт меньше основной V1. Новых общих игровых библиотек нет; <strong>{b['candidateTriangles']:,} треугольников</strong>, +{b['triangleChangePercentAgainstOriginal']:.2f}% к исходной карте. Это бюджет всей карты, а не подтверждение диапазона веса каждого отдельного объекта.</p>
<p>Основная модель, дорожные поверхности и остальные SPM совпадают побайтно с V3. Игровые точки и линии сохранены. Число треугольников новых дымовых прототипов в редактируемом Blender совпадает с SPM, включая обратные стороны. Проверены 85 частей общих размещений, встроенные XML, файлы текстур и привязки общего каталога.</p>
<p>Один круг Time Trial с одной машиной в iOS Simulator завершился естественно, место #1; принудительная победа не использовалась. Кадры ниже сняты с игровой камеры. Названия файлов обозначают задержку по системным часам, а не точное значение игрового таймера.</p>
<p class="note"><strong>Карта ещё не завершена.</strong> На верхнем маршруте остаются большие плоские дымовые объёмы; часть новых клубов вытянута из-за исходных тонких габаритов. Крупные формы замка и лавовые шипы пока далеки от референса. V4E сохранена отдельно: основная карта, её итоговый Blender-файл и превью кампании по-прежнему используют V1. Полный заезд кампании, обратное направление и производительность не подтверждены.</p>
<p><a href="../../volcano-remake-rework/fidelity-v4e/native/Volcano%20Remake.blend">Редактируемый кандидат V4E</a> · <a href="evidence/fidelity-v4e/preservation.json">Сохранность</a> · <a href="evidence/fidelity-v4e/budget.json">Вес и полигоны</a> · <a href="evidence/fidelity-v4e/pool-audit.json">Реальный пул и повторное использование</a> · <a href="evidence/fidelity-v4e/runtime-validation.json">Проверка заезда</a></p>
<figure><a href="screenshots/fidelity-v4e-drive-40s.png"><img src="screenshots/fidelity-v4e-drive-40s.png" alt="V4E: дым на повороте у лавы"></a><figcaption><strong>V4E: поворот у лавы, таймер 00:30</strong><span>Прямоугольники исчезли, но силуэт дыма ещё требует доработки.</span></figcaption></figure>
<figure><a href="screenshots/fidelity-v4e-drive-80s.png"><img src="screenshots/fidelity-v4e-drive-80s.png" alt="V4E: верхний маршрут и оставшиеся плоские объёмы"></a><figcaption><strong>V4E: верхний маршрут, таймер 01:18</strong><span>Плоские объёмы над трассой пока сохраняются; этот недостаток не скрыт.</span></figcaption></figure>
<p>Дополнительно сохранены <a href="screenshots/fidelity-v4e-drive-12s.png">входная арка</a> и <a href="screenshots/fidelity-v4e-drive-150s.png">естественный финиш</a>. Опытные V4, V4B и V4C с прямоугольными артефактами не перенесены в игру. Новая текстура и пять новых SPM зарегистрированы физическими файлами; остальные текстуры и неизменённые модели повторно используют пути V3.</p></section>'''
s=re.sub(r'<section id="fidelity-v4e-draft">.*?</section>','',page.read_text(),flags=re.S)
s=s.replace('<h2>Референс</h2>',section+'<h2>Референс</h2>',1)
s=s.replace('В разделе черновика V2 добавлены новые игровые кадры с текущими полупрозрачными панелями.','В разделах отдельных кандидатов V2, V3 и V4E добавлены новые игровые кадры с текущими полупрозрачными панелями.');page.write_text(s)
missing=[link for link in re.findall(r'(?:src|href)="([^"]+)"',s) if not urlsplit(link).scheme and not link.startswith('#') and not (out/unquote(link.split('#')[0])).exists()];assert not missing,missing
(out/'manifest.json').write_text(json.dumps({'brokenLocalLinks':missing,'files':[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']},indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for prefix in ['volcano-remake-reference-v1','volcano-remake-fidelity-v2','volcano-remake-fidelity-v3','volcano-remake-fidelity-v4e']:shutil.copytree(out,pack/'sources'/prefix/'report',dirs_exist_ok=True)
shutil.copy2(Path(__file__),pack/'sources/volcano-remake-fidelity-v4e'/Path(__file__).name)
print('V4E_REPORT_UPDATED',page)
