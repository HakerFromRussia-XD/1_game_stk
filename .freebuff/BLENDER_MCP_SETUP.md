# Blender MCP — как я подключён к Blender в этой сессии

Статус: **работает, два инстанса Blender одновременно**:
- Инстанс №1 (PID 856, порт **9876**) — занят Codex/Кодексом (сцена `Ski Dash - Winter`). Мне туда **писать нельзя**.
- Инстанс №2 (PID 5347, порт **9877**) — мой, запущен через `open -na Blender --args --python .freebuff/blender_mcp_second_instance_startup.py` (свежая стартовая сцена).

**Дисциплина:** у каждого инстанса — свой .blend-файл. Никогда не открывать один и тот же файл в двух инстансах. Прежде чем открыть в «своём» инстансе файл трассы, убедиться, что он не открыт у Кодекса (спросить или проверить `get_scene_info` на 9876).

## Запуск второго инстанса (если упал/закрыт)
```bash
open -na "Blender" --args --python "$PWD/.freebuff/blender_mcp_second_instance_startup.py"
```
`open -n` обязателен: GUI-приложение, запущенное через `&`/`nohup` из shell, умирает при закрытии сессии (проверено). Стартовый скрипт включает аддон `blender_mcp` и стартует сервер на порту 9877.

## Что где лежит
- Клиент: `.freebuff/blender_mcp_client.py` (JSON-over-TCP, один запрос = одно соединение)
- Смоук-скрипт: `.freebuff/smoke_scene_summary.py`
- Скриншот вьюпорта: `.freebuff/viewport_smoke.png` (метод `offscreen`, 800×430)

## Команды клиента
```bash
# инстанс Кодекса (порт 9876 — только чтение!):
python3 .freebuff/blender_mcp_client.py scene
# МОЙ инстанс (порт 9877 — здесь работаю):
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py scene
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py object <name>
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py viewport --out путь/к/кадру.png
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py code  '<python>'
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py file  script.py [аргументы]
BLENDER_MCP_PORT=9877 python3 .freebuff/blender_mcp_client.py call  <тип> '<json params>'
```

- `file script.py args...` — тело скрипта исполняется внутри Blender; внутри доступна переменная `argv` (список аргументов). Скрипт обязан напечатать `SCRIPT_OK` при успехе.
- Пути для `viewport` подставляйте абсолютные (аддон резолвит относительно cwd Blender); клиент теперь абсолютизирует сам.

## Текущее состояние сцены
- Сцена: `Ski Dash - Winter` — 356 объектов (355 MESH + 1 CAMERA), 686 мешей, 39 материалов, 94 изображения
- Коллекции: `Ski Dash | original SPM + reused winter scenery`, `SkiDash_Winter_Replacements`, плюс 5 донорских `Fluxara_Canyon_*` из библиотеки ассетов

## Известные ограничения
- Это аддон blender-mcp (shaharjason/blender-mcp fork), а не официальный MCP-клиент Codebuff — но протокол простой, и все команды проходят.
- `SCRIPT_OK` печатается дважды: один раз моим обёрточным кодом, один раз выводом скрипта — это норма.
- Скриншот через offscreen-рендер вьюпорта; требует, чтобы окно Blender было живо (не закрыто).
