# Отчёт гейта стадии

Анатомист заполняет по `/qc-stage`. ПМ читает вердикт. Не утверждает этап за пользователя.

## Манифест стадии

- stage-id: S-08
- команда из `.cursor/list-commands.md`: отдельной slash-команды нет; id среза `reports/checklist.md` § S-08; гейт `/qc-stage` → `.cursor/skills/skill-agent-anatomist.md`
- исполнитель: anatomist (конвейер: front-developer UC-008; tester `/new-tests`; `/use-tests` FAIL оракул сдачи; `/new-tests` правка оракула; `/use-tests` PASS 279)
- дата: 2026-09-17

`stage-id` в запросе ПМ (`S-08`) совпал с `reports/pm-state.md`; строка `- stage-id:` не менялась. Поля `approval` / `status` / `Stage: … APPROVED` не трогались. Код `src/` и `tests/` этим ходом не менялись.

Срез **S-08** только фронт: смена языка UC-008; язык сессии на бэкенде не хранить (A0091). Бэкенд в срез не входит. Критерии чеклиста: меню RU/EN; подписи включая «Компьютер» / Computer; сервер не требует поля языка; FT-008 координаты; FT-073 без пересоздания сессии; FT-060/062 QSettings.

Контекст конвейера (факт, не вердикт): UI — `I18n` + меню `menu-language`; `SettingsStore` / `QSettings("SeaBattle", "Frontend")` ключ `language`; POST `/sessions` без тела; WS shot/surrender без языка; оракул `VALIDATION_ERROR` → `err_validation`; `/use-tests` — 279 passed (`reports/test-run.md`).

## Артефакты

| Ожидаемый путь | Есть | Замечание |
| --- | --- | --- |
| `src/frontend/i18n.py` | да | Каталоги `ru` / `en`; «Компьютер» / Computer; `toast_lang` про сессию без пересоздания |
| `src/frontend/settings_store.py` | да | QSettings ключ `language`; мусор → FT-060; persist `RU`\|`EN`; `language_changed` |
| `src/frontend/ui/main_window.py` | да | Меню RU/EN (`menu-language*`); `_on_language` → `_retranslate`; партия не стартует заново |
| `src/frontend/ui/dialogs.py` | да | `SurrenderDialog` / game-over / stats `retranslate`/`bind` |
| `src/frontend/ui/battle_screen.py` | да | `bind_scene` + `set_language` досок; заголовки флота |
| `src/frontend/ui/board_widget.py` | да | Буквы через `letters_for(self.language)` |
| `src/frontend/ui/lobby_screen.py` | да | Lead/KPI/вкладки с i18n |
| `src/frontend/domain/types.py` | да | RU А–К без «Ё»/«Й»; EN A–J; `CellCoordinate.code` числовой |
| `src/frontend/client/session_start.py` | да | POST `/sessions`, `data=None`, поле `language` нет |
| `src/frontend/client/statistics.py` | да | GET `/statistics`, языка в запросе нет |
| `src/frontend/client/party_channel.py` | да | `shot`/`surrender` JSON без языка; i18n только для канона ошибок |
| `src/backend/` | да | Символа `language` в коде бэка нет; срез его не требовал |
| `tests/test_should_switch_interface_language_when_menu_chosen.py` | да | Меню, бой/коды, диалоги, ошибка канала, QSettings, ОС-локаль |
| `tests/test_should_show_surrender_when_player_confirms.py` | да | Оракул BUG-001: `VALIDATION_ERROR` → `window.i18n.t("err_validation")` |
| `tests/test_should_post_sessions_when_client_starts.py` | да | Пустое тело POST (нет поля языка) |
| `tests/coverage.md` | да | Строки UC-008 / FT-008 / FT-060 / FT-062 / FT-073; шапка ещё «прогон не выполнялся» |
| `reports/test-run.md` | да | 2026-09-17 11:08:02 (UTC+5), **PASS**, collected 279; 279 passed, 0 failed |
| `requirements/use-cases/uc-008-change-language.md` | да | Канон сценария |
| `requirements/functional-requirements.md` | да | FT-008, FT-060, FT-062, FT-073 (также FT-059/061 в UC) |
| `requirements/answers-project.md` A0091 | да | Язык только на фронте |
| `reports/checklist.md` § S-08 | да | «Срез готов: [ ]» — отметку гейт не ставит |

## Чек-лист верификации

| # | Критерий | Результат | Заметка |
| --- | --- | --- | --- |
| 1 | Артефакт на правильном пути | pass | UI `src/frontend/`; тесты `tests/test_should_*`; прогон `reports/test-run.md`; бэк не цель среза |
| 2 | Нет правок вне Input Manifest роли | pass | Этот ход пишет только `reports/review-report.md`. След конвейера: front-developer `src/frontend/`; tester `tests/` + `coverage.md` + `test-run.md`. В `src/backend/` нет `language`; поле языка на сессию не введено |
| 3 | Существующий точечный скилл не затёрт | pass | `/qc-ft-nft` → `skill-quality-control-ft-nft.md`; `/qc-us-uc` → `skill-quality-control-us-uc.md`; `/qc-ddd` → `skill-quality-control-ddd.md`; `/qc-stage` → `skill-agent-anatomist.md`; `/frontend` / `/new-tests` / `/use-tests` — те же скиллы |
| 4 | Критерии приёмки стадии проверяемы | pass | Меню RU/EN, подписи Computer, пустой POST, буквы FT-008, sessionId/`.code`/TTL без нового POST, QSettings/ОС. Нет неизмеримого «быстро» |

Критерии «срез готов» из § S-08 (проверка по репозиторию, без отметки `[x]`):

| Критерий чеклиста | Факт |
| --- | --- |
| Переключить RU/EN на экране | Меню `menu-language` / `menu-language-ru` / `menu-language-en`; тесты лобби RU↔EN |
| Подписи «Компьютер» / Computer | i18n `side_backend`, lead, KPI, доска, флот; assert в UI-тестах |
| Сервер не требует поля языка | Клиент POST `data is None`; WS без `language`; OpenAPI: UI language frontend-only; бэк без поля `language`; API-тест POST с телом → 400 (чужой срез, инвариант A0091) |
| FT-008 координаты | `RU_LETTERS` / `EN_LETTERS`; журнал и доски после смены языка; `.code` остаётся `"00"` |
| FT-073 без пересоздания сессии | Тот же `_live_scene` / `session_id` / `ttl_seconds`; счётчики `CreateSessionWorker.start` и party start не растут; HTTP на смене запрещён |
| FT-060 / FT-062 QSettings | Нет ключа + `ru_RU` → RU; `de_DE` → EN; ключ EN важнее ОС ru; мусор не сохраняется |
| Только фронт (A0091) | Язык в `SettingsStore`; бэкенд срез не меняет |
| Автотесты | `reports/test-run.md`: **279 passed**. GUI не открывался. BUG-001 закрыт правкой оракула, продукт сдачи не трогали |

## Замечания

| ID | Уровень | Суть | Где |
| --- | --- | --- | --- |
| S08-01 | minor | Шапка `tests/coverage.md` пишет «прогон полного набора не выполнялся»; канон прогона — `reports/test-run.md` (279 PASS) | `tests/coverage.md` |
| S08-02 | minor | § S-08 чеклиста без `[x]`. ПМ обновляет чеклист сам; «Срез готов» этим гейтом не отмечать | `reports/checklist.md` § S-08 |
| S08-03 | minor | Автотесты не открывают GUI и не делают kill/relaunch процесса. Ручная сверка: пункт меню на живом окне; следующий запуск после выбора языка (FT-062) — за пользователем | `src/run-frontend.bat`; карта покрытия |
| S08-04 | minor | `pm-state.md` «последний `/qc-stage`» ещё S-07; `/use-tests` там 270. Это след прошлого гейта, не код | `reports/pm-state.md` |
| S08-05 | minor | NFT-016 «число подписей на прежнем языке = 0» покрыто выборкой (лобби, бой, три диалога, ошибка канала), не полным перебором ключей `STRINGS` | `tests/test_should_switch_interface_language_when_menu_chosen.py` |

Critical: нет.
Major: нет.

## Вердикт

- `pass` — нет critical и major. Можно просить пользователя утвердить этап.
- `fail` — есть critical или major. ПМ возвращает исполнителя, глобальный этап не меняет.

Вердикт: **pass**
