# Витрина портфолио — Sea Battle

Канон требований и границ продукта:

- [Vision & Scope](../vision-scope.md)
- [ТЗ по ГОСТ 34.602-89](../tz-gost-seabattle.md)

Короткий слой «для скрининга и слайдов». Канон требований и кода не дублируется: полные таблицы — в `requirements/`, исходники диаграмм — в `diagrams/`.

**Аудитория этой поставки:** системный аналитик и архитектор.

## С чего начать (5 минут)

1. [case-study.md](case-study.md) — задача, границы MVP, решения, результат.
2. [architecture.md](architecture.md) — слои as-is и ключи Redis.
3. Диаграммы C4 / sequence / state в [diagrams/](../../diagrams/) (имена `diagram-c4-001`, `diagram-seq-*`, `diagram-state-001`).
4. [demo-script.md](demo-script.md) — как показать окно на собеседовании.

English one-pager: [../../README.en.md](../../README.en.md).

## Документы

| Файл | Зачем |
| --- | --- |
| [case-study.md](case-study.md) | Кейс 1–2 страницы |
| [architecture.md](architecture.md) | Слои, протокол, хранение |
| [demo-script.md](demo-script.md) | Сценарий 5–7 минут |
| [requirements-index.md](requirements-index.md) | US/UC → OpenAPI (для аналитика) |
| [adr/](adr/) | Короткие ADR (для архитектора) |

## Диаграммы (исходники текстовые)

| Тема | Файл |
| --- | --- |
| C4 Context, Container, Component, Deployment | [diagrams/diagram-c4-001.md](../../diagrams/diagram-c4-001.md) |
| Sequence: выстрел и ход Бэкенда | [diagrams/diagram-seq-001.md](../../diagrams/diagram-seq-001.md) |
| Sequence: reconnect | [diagrams/diagram-seq-002.md](../../diagrams/diagram-seq-002.md) |
| Состояния сессии | [diagrams/diagram-state-001.md](../../diagrams/diagram-state-001.md) |
| Hunt/Target для слайда | [diagrams/diagram-ai-overview.md](../../diagrams/diagram-ai-overview.md) |
| Class: агрегат Session | [diagrams/diagram-class-session-overview.md](../../diagrams/diagram-class-session-overview.md) |
| DFD уровень 0 (обзор) | [diagrams/diagram-dfd-overview.md](../../diagrams/diagram-dfd-overview.md) |
| Ключи Redis | [diagrams/diagram-redis-keys.md](../../diagrams/diagram-redis-keys.md) |
| BPMN жизненный цикл партии | [diagrams/bpmn-002.bpmn](../../diagrams/bpmn-002.bpmn) |

Канон аналитика (не затирался): `diagram-mermaid-001.md` (ход Бэкенда), `diagram-class-001.md`, `diagram-dfd-001.md`, `bpmn-001.bpmn`.

Экспорт SVG/PNG для слайдов: [export/](export/). Скриншоты окна — по отдельному запросу в `screenshots/` (папка зарезервирована).

На схемах канон документов — **Бэкенд**. На экране игроку — **Компьютер**.
