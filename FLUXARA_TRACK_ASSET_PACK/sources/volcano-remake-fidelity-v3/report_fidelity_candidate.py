from pathlib import Path
import hashlib
import html
import json
import re
import shutil
from urllib.parse import unquote,urlsplit

r=Path(__file__).resolve().parent
work=r/'fidelity-v2'
out=r.parent/'fluxara-user-volcano-remake-final/report'
page=out/'index.html'
old=page.read_bytes()
history=work/'report-history'
history.mkdir(exist_ok=True)
shutil.copy2(page,history/(hashlib.sha256(old).hexdigest()[:12]+'-index.html'))
evidence=out/'evidence/fidelity-v2'
evidence.mkdir(parents=True,exist_ok=True)
for name in ['changes.json','preservation.json','budget.json','runtime-validation.json',
             'drive-capture.json','production-preservation.json','unused-support-maps.json',
             'final-blend-verification.json','imagegen-prompt.txt']:
    shutil.copy2(work/name,evidence/name)
for name in ['drive-12s.png','drive-40s.png','drive-80s.png','drive-150s.png','castle-wide.png']:
    shutil.copy2(work/'screenshots'/name,out/'screenshots'/('fidelity-v2-'+name))
budget=json.loads((work/'budget.json').read_text())
section=f'''<section id="fidelity-v2-draft"><h2>Доработка V2 — отдельный черновик</h2>
<p>Входной декоративный зубчатый элемент заменён каменным арочным проездом: 294 → 300 треугольников, внешние границы, центр и начало координат сохранены. Масштаб кладки стен уменьшен втрое. Скалы получили новую лиловую каменную фактуру, отдельный материал мха и проекцию UV по поверхности; геометрия скал сохранена.</p>
<p>Вес папки черновика: <strong>{budget['candidateTrackBytes']:,} байт</strong>, ещё на {budget['savedBytesAgainstPrevious']:,} байт меньше предыдущей версии. Неиспользуемые старые карты рельефа и блеска сохранены вне игрового пакета. Общая геометрия: {budget['candidateTriangles']:,} треугольник, +{budget['triangleChangePercentAgainstOriginal']:.2f}% к исходной карте. Новых общих игровых библиотек не добавлено.</p>
<p>Черновик прошёл один круг Time Trial с одной машиной и естественным финишем. Кадры ниже сняты с игровой камеры в iOS Simulator. Полный заезд кампании, обратное направление и производительность этим тестом не подтверждены.</p>
<p class="note">Это отдельная временная карта для проверки. Основные игровые ресурсы, итоговый проект и превью кампании пока сохраняют предыдущую версию. До референса ещё остаются заметные отличия: размеры крупных замковых форм, яркие эффекты и лавовые шипы у входа, небо и дым. Этот черновик не является завершённой или согласованной десятой картой.</p>
<p><a href="../../volcano-remake-rework/fidelity-v2/native/Volcano%20Remake.blend">Редактируемый черновик V2</a> · <a href="evidence/fidelity-v2/preservation.json">Сохранность дороги</a> · <a href="evidence/fidelity-v2/budget.json">Бюджет черновика</a> · <a href="evidence/fidelity-v2/runtime-validation.json">Проверка заезда</a></p>
<figure><a href="screenshots/fidelity-v2-drive-12s.png"><img src="screenshots/fidelity-v2-drive-12s.png" alt="Черновик V2: подъезд к арке"></a><figcaption><strong>Черновик V2: подъезд к арке</strong><span>Новая кладка и арочный проезд; текущие полупрозрачные счётчики HUD.</span></figcaption></figure>
<figure><a href="screenshots/fidelity-v2-drive-40s.png"><img src="screenshots/fidelity-v2-drive-40s.png" alt="Черновик V2: поворот у лавы"></a><figcaption><strong>Черновик V2: поворот у лавы</strong><span>Реальная игровая камера. Освещение лавы и дым ещё требуют доработки.</span></figcaption></figure>
<p>Сохранены также <a href="screenshots/fidelity-v2-drive-80s.png">верхний мост</a> и <a href="screenshots/fidelity-v2-drive-150s.png">естественный финиш</a>. Новая текстура камня создана встроенным imagegen; <a href="evidence/fidelity-v2/imagegen-prompt.txt">точный запрос генерации</a> сохранён вместе с доказательствами. Повторение 3×3 просмотрено отдельно.</p></section>'''
s=old.decode()
s=re.sub(r'<section id="fidelity-v2-draft">.*?</section>','',s,flags=re.S)
s=s.replace('<h2>Референс</h2>',section+'<h2>Референс</h2>',1)
s=s.replace('Кадры ниже сохранены из проверок версии окружения, указанной в подписях. Они сняты до последнего общего исправления HUD: полупрозрачных панелей, компактных счётчиков и ряда соперников. Это реальные кадры прошлой проверки, а не новые снимки текущего интерфейса.',
            'Основные кадры предыдущей версии сняты до общего исправления HUD. В разделе черновика V2 добавлены новые игровые кадры с текущими полупрозрачными панелями. Версия каждой проверки указана в подписи; черновик не заменяет итоговую поставку.')
page.write_text(s)
missing=[]
for link in re.findall(r'(?:src|href)="([^"]+)"',s):
    if not urlsplit(link).scheme and not link.startswith('#') and not (out/unquote(link.split('#')[0])).exists():
        missing.append(link)
assert not missing,missing
manifest={'brokenLocalLinks':missing,'files':[{'path':str(p.relative_to(out)),
    'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
shutil.copytree(out,pack/'sources/volcano-remake-reference-v1/report',dirs_exist_ok=True)
shutil.copytree(out,pack/'sources/volcano-remake-fidelity-v2/report',dirs_exist_ok=True)
print('FIDELITY_REPORT_UPDATED',page)
