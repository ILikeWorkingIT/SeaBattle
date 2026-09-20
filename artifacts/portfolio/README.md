# Витрина портфолио — Sea Battle

Канон требований и границ продукта:

- [Vision & Scope](../vision-scope.md)
- [ТЗ по ГОСТ 34.602-89](../tz-gost-seabattle.md)

Короткий слой «для скрининга и слайдов». Канон требований и кода не дублируется: полные таблицы — в `requirements/`, исходники диаграмм — в `diagrams/`.

**Аудитория этой поставки:** системный аналитик и архитектор.

## С чего начать (5 минут)

1. [case-study.md](case-study.md) — задача, границы MVP, решения, результат.
2. [architecture.md](architecture.md) — слои as-is и ключи Redis.
3. Диаграммы — таблица ниже и папка [diagrams/](../../diagrams/).
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

Все файлы из `diagrams/`. Слайдовые обзоры и полный канон аналитика — рядом, не дублируют друг друга.

| Тема | Файл |
| --- | --- |
| C4 Context, Container, Component, Deployment | [diagram-c4-001.md](../../diagrams/diagram-c4-001.md) |
| Sequence: выстрел игрока и ход Бэкенда | [diagram-seq-001.md](../../diagrams/diagram-seq-001.md) |
| Sequence: возобновление канала партии | [diagram-seq-002.md](../../diagrams/diagram-seq-002.md) |
| Состояния игровой сессии | [diagram-state-001.md](../../diagrams/diagram-state-001.md) |
| Hunt/Target (слайд) | [diagram-ai-overview.md](../../diagrams/diagram-ai-overview.md) |
| Class: агрегат Session (слайд) | [diagram-class-session-overview.md](../../diagrams/diagram-class-session-overview.md) |
| Class: доменная модель (полный срез, A0148) | [diagram-class-001.md](../../diagrams/diagram-class-001.md) |
| DFD уровень 0 (обзор для витрины) | [diagram-dfd-overview.md](../../diagrams/diagram-dfd-overview.md) |
| DFD уровни 0 и 1 | [diagram-dfd-001.md](../../diagrams/diagram-dfd-001.md) |
| Ключи Redis | [diagram-redis-keys.md](../../diagrams/diagram-redis-keys.md) |
| Flowchart: ход Бэкенда и смена состояния (US-003) | [diagram-mermaid-001.md](../../diagrams/diagram-mermaid-001.md) |
| BPMN: ход Бэкенда и смена состояния партии | [bpmn-001.bpmn](../../diagrams/bpmn-001.bpmn) |
| BPMN: жизненный цикл партии PvE | [bpmn-002.bpmn](../../diagrams/bpmn-002.bpmn) |

Экспорт SVG/PNG для слайдов: [export/](export/). Скриншоты окна: [screenshot-lobby.png](../screenshot-lobby.png), [screenshot-battle.png](../screenshot-battle.png) (папка `screenshots/` зарезервирована).

На схемах канон документов — **Бэкенд**. На экране игроку — **Компьютер**.
