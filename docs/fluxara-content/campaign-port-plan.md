# План переноса кампании Fluxara

## Исправление объёма после уточнения пользователя

**25normal+25time-trial отменено.** Прежние два режима относятся только к STORY challenge XML, а не ко всей игре. Пользователь требует пользовательские трассы для КАЖДОГО режима. Список50линейных трасс — исходный pool, не финальная кампания. Arena/soccer/CTF/egg должны войти в отбор; частные рекомендации ниже о25/25и5normal+5timed больше не действуют.

Полный пользовательский набор (CTF AI отсутствует в штатном `RaceManager::hasAI`, `src/race/race_manager.hpp:197`; это отдельная задача для офлайн-кампании):

| Режим | Совместимый контент | Источник в src |
|---|---|---|
| Normal Race | Линейный маршрут с graph/quads | states_screens/race_setup_screen.cpp:87–91 |
| Time Trial | Линейный маршрут; цель времени/ghost | states_screens/race_setup_screen.cpp:94–97 |
| Follow the Leader | Линейный маршрут с AI; выбывание за лидером | states_screens/race_setup_screen.cpp:100–110 |
| Battle: Three Strikes | arena, navmesh для одиночного игрока с AI | states_screens/race_setup_screen.cpp:113–116,238; arenas_screen.cpp:104–120 |
| Battle: Free-for-All | arena/navmesh, время и попадания | states_screens/track_info_screen.cpp:589–599 |
| Capture the Flag | ctf-флаг, сцена с командными флагами/стартами; доступен online | race/race_manager.hpp:120; states_screens/dialogs/server_configuration_dialog.hpp:74 |
| Soccer | soccer-флаг, мяч/ворота/navmesh; параметры лимит времени или голов | states_screens/race_setup_screen.cpp:118–121; track_info_screen.cpp:600–605 |
| Easter Egg Hunt | Непустой easter_eggs.xml; один local player | states_screens/race_setup_screen.cpp:123–134; tracks/track.cpp:635–646 |
| Ghost Replay Race | TimeTrial с подходящим replay данной трассы | states_screens/race_setup_screen.cpp:137–139,257 |
| Lap Trial | Линейный маршрут; максимум кругов за лимит времени | states_screens/race_setup_screen.cpp:141–144,263 |
| Grand Prix | Major-формат последовательности трасс, не новый тип геометрии | race/race_manager.hpp:95–96; data/grandprix/*.grandprix |

Overworld/Tutorial/Cutscene также есть в enum (`race/race_manager.hpp:126`–128), но это служебный мир, обучение, ролик; не включать их в квоту соревновательных трасс. Online/offline и difficulty — параметры/контекст, не дополнительные модели трасс.

Подсчёт `mode_coverage_inventory.py`:552скачанных track-пакета;468линейных graph/quads,1arena сnavmesh,80soccer сnavmesh,7сctf-флагом,76снепустыми egg-layout,4неподдерживаемых версии. Флаги пересекаются. В original app44track.xml:9arenas,6soccer,7ctf,9egg-layout,21линейная graph/quads. Это отдельно от21STORY-трассы.

Причина неполноты прежнего каталога: source manifest имеет отдельный `<arena>` tag, который прежний downloader исключал. Есть72уникальныхarena,70v6/7,69изнихsource-approved. Все72пакета скачаны иZIP-проверены:525490686байт;source/licenseсохранены,отчёт`.codex-downloads/fluxara-addon-catalog/arena-download-report.json`. Режимныеpoolи5превьюдлякаждого находятся в`user-mode-candidates.json/.md` и`previews/mode-*.jpg`.

Равная квота пока не утверждена:10игровых вариантов доGP дают50слотов по5; карты могут поддерживать несколько режимов, поэтому50слотов не гарантируют50уникальных карт. Если объединятьGhost сTimeTrial иBattle-варианты вfamily, получится7семейств, минимум56слотов по8. Это арифметические варианты, не принятое решение. Финально нужны минимум50unique maps иравное количество на выбранном уровнеmode grouping;GPоборачиваетсобытия. Квота не разрешает подменятьarenaлинейной картой или считатьCTFготовым offline без реализации. Всеghost требуютподходящих replay, самиgeo-файлы не доказываютghost-ready.

Исследование и план, 18 сентября 2026. Этот документ не меняет игровой процесс. Последняя инструкция пользователя имеет приоритет: в списке нужны завершённость, кубки и закрытый участок, открывающийся после прохождения определённого количества трасс.

## Что установлено в оригинале

`data/challenges` содержит 28 XML: 21 одиночное испытание, 4 Grand Prix, 3 записи только разблокировки. Объединение track id одиночных испытаний и всех этапов используемых GP содержит **21 уникальную трассу**, а не 25 и не 28. Четыре GP повторно используют 20 этих трасс; Fort Magma — отдельная финальная трасса. Воспроизводимый подсчёт: `python3 tools/fluxara_content/original_campaign_inventory.py`. Каталог challenges сравнен с `/private/tmp/original-stk-pre-fluxara.app/data/challenges`: `diff -rq` не вывел различий; в архивном оригинале также 28 файлов.

Уникальные id: abyss, black_forest, candela_city, cocoa_temple, cornfield_crossing, fortmagma, gran_paradiso_island, hacienda, lighthouse, mines, minigolf, olivermath, ravenbridge_mansion, sandtrack, scotland, snowmountain, snowtuxpeak, stk_enterprise, volcano_island, xr591, zengarden.

Источники: `data/grandprix/1_penguinplayground.grandprix:3`, `2_offthebeatentrack.grandprix:3`, `3_tothemoonandback.grandprix:3`, `4_atworldsend.grandprix:3`; `data/challenges/fortmagma.challenge:4`. Не считайте имя challenge именем трассы: `green_valley.challenge:4` указывает на black_forest.

Оригинальная кампания реально использует **два режима**: quickrace (19 challenge, включая 3 GP) и timetrial (6 challenge, включая 1 GP). Поддержка followtheleader в парсере существует, но ни один оригинальный challenge её не использует. Источники: `src/challenges/challenge_data.cpp:153`–171; примеры `data/challenges/olivermath.challenge:5`, `sandtrack.challenge:5`, `gp3.challenge:5`. Arena/soccer — другие типы контента, не разновидности этих линейных заездов: `src/race/race_manager.hpp:114`–121; `src/tracks/track.cpp:573`–577.

Прогресс оригинала хранится по challenge и сложности. Прохождение высокой сложности закрывает и нижние: `src/challenges/challenge_status.cpp:71`–78. Сохранение пишет highest solved=easy/medium/hard/best: `challenge_status.cpp:94`–110. Очки сложности: 6/7/8/10, GP умножается на3 (`story_mode_status.hpp:37`–38); учитывается максимальная пройденная сложность, а не сумма повторных побед (`story_mode_status.cpp:145`–168). Это **кубки сложности**, а не автоматическое bronze/silver/gold за места3/2/1.

Разблокировка оригинала задаётся XML trophy-порогом, также поддержан счётчик challenges (`challenge_data.cpp:126`–128). Например финал требует trophies=190 и challenges=24 (`fortmagma.challenge:6`). Успех проверяет трассу, число соперников, устранение, место, нитро, круги, время/ghost (`challenge_data.cpp:490`–548), а не просто показ экрана результатов. Завершение идёт через `PlayerProfile::raceFinished()` (`player_profile.cpp:322`–325) и `StoryModeStatus::raceFinished()` (`story_mode_status.cpp:303`–318); сохранение профиля вызывается после unlock (`story_mode_status.cpp:267`–278).

## Предлагаемая новая кампания

**50 уникальных трасс**, что превышает исходные21. Список кандидатов и превью: `campaign-50-candidates.json`, `campaign-50-candidates.md`, `previews/campaign-50-01.jpg`, `previews/campaign-50-02.jpg`. Это не список готовых импортированных и проверенных трасс: 50 исходных пакетов весят около811MiB, требуют проверки зависимостей, вида и оптимизации. Одобренный Canyon сохраняется; его старое превью с дирижаблем нужно заменить реальным одобренным игровым кадром.

Полная режимная матрица приведена в исправлении выше. Режим — поле события, а тип карты задаёт совместимость. Для каждого timed-события нужны измеренные целевые времена/ghost, дляarena/CTF/soccer — сцена иnavmesh, дляegg — реальные egg layouts.25/25не применяется.

Разбиение иunlock-пороги пока не утверждены: они зависят от финальной режимной матрицы. Пример для50слотов —5участков по10сunlock8/16/24/32unique completions; это только вариант, не правило реализации. Счётчик общего выполнения считает каждую track id один раз независимо от повторов, сложности и режима. Не заменять требование пользователя счётчикомtrophy points.

Кубки рекомендовано сохранить в исходной семантике сложности: лучший выполненный уровень easy/medium/hard/best. Карточка отдельно показывает «пройдено» и лучший кубок; повторная более слабая попытка не ухудшает награду. Если продукт предпочитает медали за места, это отдельное изменение правил, его не смешивать с original trophy semantics. Для обычного режима рекомендуемый исходный success-condition — победа, как у оригинальных normal challenges; timed — выполнение цели. Эти правила и difficulty доступны из event definition, а не из картинки кубка.

## Данные и локальное сохранение

Предлагаемый `FluxaraCampaignDefinition`: schemaVersion, campaignId, revision, ordered segments; segmentId, requiredCompletedTracks; events с immutable eventId, trackId, title/localizationKey, preview, mode, laps, reverse, kartCount, difficultyGoals. Подтверждать все trackId в TrackManager, но сохранять явно заданный порядок. Не сортировать кампанию по порядку загрузки ресурсов и не использовать локализованное имя как ключ.

`FluxaraCampaignProgress` — отдельный versioned раздел внутри профиля, например `<fluxara-campaign version="1" id="main">`; eventId, highestSolvedDifficulty, bestFinishTime, bestPosition, completed, lastRecordedRaceId. Предлагаемая точка интеграции с существующим profile save/load: `src/config/player_profile.cpp:137`–138 и267–268. Не перетирать original story-mode: совпадение «21 трасса» не означает идентичность событий; достижения пользователя оригинала сохраняются, но автоматически не превращаются в прохождение новых маршрутов.

При отсутствии нового раздела создать пустой прогресс. Неизвестные/временно отсутствующие eventId сохранить для будущих версий. Улучшения монотонны: highestSolved=max(old,new), bestTime=min(valid times); повторный result callback с тем же raceId идемпотентен. Завершение/кубки вычислять по подтверждённому race result, не при нажатии Next. Сохранять сразу до перехода со страницы результата через существующий PlayerManager save. Отмена, DNF, авария, AI profile run, демонстрационный старт не дают человеческий прогресс.

## Контракт UI для агента интерфейса

Текущий `FluxaraCampaignScreen::init` перечисляет Fluxara-группу, фильтрует arena/soccer/internal и показывает единственную карточку (`src/states_screens/fluxara_campaign_screen.cpp:27`–53,56–81). Его `choose` напрямую открывает RaceSetup (`:117`–125); сейчас нет campaign-order, прогресса или gate. Заменить источником моделей карточек, сохранив утверждённые материалы кнопок и отдельные иконки.

Модель карточки: eventId, trackId, name, previewTexture, modeBadge, completed, bestCup, available, lockReason, segmentId. Модель закрытого участка: required, currentUniqueCompleted, remaining, readable label «Пройди ещё N трасс». Показывать всю кампанию в прокручиваемом списке; closed cards видны, их Start недоступен. Не скрывать закрытый участок и не перегружать сцены всех50трасс ради превью; загружать только видимые thumbnail-текстуры. В RaceSetup передавать eventId и фиксированные условия; free race остаётся отдельным контекстом.

Result: сначала записать подтверждённый результат, затем строить cup/completed display; Next выбирает следующее доступное событие в campaign-order, не modulo по TrackManager. Разблокировку показывать один раз по переходу locked→available. Back/reopen/profile-switch сохраняют корректное состояние. Доступность проверять повторно при launch, а не только цветом кнопки.

## Порядок реализации и проверка

1. Сформировать event manifest минимум50unique maps с покрытием каждого пользовательского режима иравнойквотой, добавить недостающиеarenaпакеты, сохранитьsource/license/previewmapping. Ghost/CTF/eggготовность проверять отдельно.25/25отменено;точныеunlock-пороги не утверждены.
2. Реализовать definition/progress service и совместимую загрузку/сохранение профиля; idempotent result запись отдельно от UI.
3. Перенести список/кубки/закрытые участки в утверждённый Figma стиль; подключить eventId к setup/result/Next.
4. Импортировать отобранные пакеты партиями, проверять зависимости и runtime по одной трассе; сохранять лицензии и не менять траектории.
5. На симуляторе проверить новый профиль, сохранённый профиль, успех/провал/повтор, ровно N−1/N для unlock, повторное открытие/перезапуск, доступность Next, DNF/AI-профиль без награды и50карточек без загрузки50сцен. Это будущие критерии приёмки, сейчас игровые тесты не запускались.

Материалы не доказывают финальную мобильную производительность, лицензионную пригодность всех пакетов или готовность App Store. Они дают воспроизводимый исходный объём кампании и конкретный контракт её переноса.
