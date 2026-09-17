# Индекс требований → контракт (витрина)

Канон сценариев: [list-uc.md](../../requirements/use-cases/list-uc.md), историй: [us-registry.md](../../requirements/user-stories/us-registry.md). Полные ФТ не копируются.

| US | UC | Возможность | Контракт |
| --- | --- | --- | --- |
| US-001 | UC-001 | Начать PvE | `POST /sessions` → 201 снимок без `backendFleet`; 409 лимит слотов |
| US-002 | UC-002 | Выстрел игрока | WS `/sessions/{id}/ws` кадр `shot` → `shotResolved`; REST shots → отказ |
| US-003 | UC-003 | Ход Бэкенда | те же кадры `shotResolved` со `shooter=Backend`; пустая heatmap → abort или победа |
| US-004 | UC-004 | Конец партии | WS `gameOver`; слот сразу; JSON после доставки удаляется |
| US-005 | UC-005 | Сдача | WS `surrender` → `gameOver` `Surrender`; REST surrender → 400 |
| US-006 | UC-006 | Reconnect того же запуска | повторный WS: `sessionSnapshot`, TTL не refresh; живой второй клиент — отказ |
| US-007 | UC-007 | Статистика сервера | `GET /statistics` |
| US-008 | UC-008 | Язык RU/EN | только Фронтенд (QSettings); поля API нет |

Связи UC: после `MISS` игрока — UC-003; уничтожение флота или сдача — UC-004.

Глоссарий: [glossary.md](../../requirements/glossary.md). Закрытые решения: коды `Axxxx` в [answers-project.md](../../requirements/answers-project.md).
