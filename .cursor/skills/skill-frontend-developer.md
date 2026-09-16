---
name: skill-frontend-developer
description: >-
  Use when the user asks to implement or change the working desktop UI,
  PySide6 widgets, theme tokens, window state, loading/error/empty states,
  REST/WebSocket client glue, test selectors, or runs /frontend. Working UI,
  not a click-only mockup. Do not use for writing tests (/new-tests) or
  running them (/use-tests), and do not implement FastAPI/Redis.
disable-model-invocation: true
owner: front-developer
---

# Рабочий UI desktop-приложения

Скилл автономного frontend-разработчика (ручной вызов `/frontend`). Не подставляй факты другого проекта. Подписи, состав экрана и поведение — только из артефактов репозитория и явного запроса.

Стек продукта: **Python 3.12+ + PySide6**. Каталог: `src/frontend/`. Launcher: `src/run-frontend.bat`. Чеклист «современного фронта» ниже обязателен **по смыслу**.

---

## 1. Роль и редирект

Роль: **Senior Frontend Engineer**. DRY / KISS / изоляция панелей / reuse / токены темы / канон `Axxxx` → ФТ/AC/UC → глоссарий.

| Запрос | Действие |
| --- | --- |
| Макет «вид + клики» | Остановись. Нужна `/ui-prototyping`. |
| FastAPI, Redis, heatmap, правила игры на сервере | `/app-layer`. Здесь не пиши `src/backend/`. |
| Только тесты | `/new-tests`. Только прогон | `/use-tests`. |
| Gradio / Streamlit / браузер «вместо окна» | Отказ: это десктоп-окно. |

После правки UI **не** запускай QA-скиллы в том же ходе. Предложи `/new-tests` и `/use-tests` отдельно.
**Не запускай** `python -m frontend` из терминала агента в чате: окно не видно. Напомни проводник → `src/run-frontend.bat`.

---

## 2. Типизация

- Аннотируй публичные методы, слоты, сигналы, возвращаемые виджеты: `QWidget`, `QPushButton`, `QLabel` и т.д.
- Запрещён `Any` как свалка. Опциональный виджет: `QPushButton | None`.
- Стейт экрана — явный enum / `Literal["idle", "loading", "error", "success"]`, не россыпь магических атрибутов.
- Импорты — вверху модуля.

---

## 3. Архитектура UI

Единственный слой стилей: токены `src/frontend/theme.py` (или уже принятый в пакете канон). Hex в панелях не плоди.

- Не блокируй GUI-поток: REST/WebSocket — `QThread` / `qasync` / воркер, не `time.sleep` в слоте кнопки.
- Клиент HTTP — по OpenAPI (`httpx` и т.п. **только как клиент** к API из config). Сервер не поднимай.
- Подписи игроку: канон документов — «Бэкенд»; на экране — «Компьютер» / EN «Computer», если так в памяти проекта / глоссарии UI.

---

## 4. Три состояния UI

Любая операция с ожиданием сети обязана иметь наблюдаемые **loading / error / empty / success** по канону ФТ. Empty не заменяет Error. Повторный клик во время loading не стартует второй запрос без правила в ФТ.

На закрытии окна: останови воркеры, закрой клиент HTTP/WS, не `join()` без таймаута.

---

## 5. QA-селекторы

На каждом интерактивном виджете:

1. Атрибут экземпляра `self.<роль>` — **не переименовывай** уже используемые тестами.
2. `QObject.setObjectName("<kebab-id>")` (латиница, уникально в окне). HTML `data-testid` не ставь.

Подписи глоссария / i18n не меняй молча.

---

## 6. SOP (один режим)

| Режим | Когда |
| --- | --- |
| **фича** | рабочий экран / кнопка / стейт по ФТ |
| **баг** | регрессия интерфейса, гонка, блокировка |
| **полировка** | вид без смены правил ФТ; селекторы не ломай |

Режим **фича:** нет канона и нет `@` — спроси с рекомендацией, не выдумывай игру.

Порядок: канон → существующий макет `src/frontend/` → минимальный diff → селекторы → не коммить.

---

## Запрещено

- Писать `src/backend/`, Docker, Redis.
- Доменные правила стрельбы / расстановки на клиенте, если канон — сервер (мок без правил — только если уже есть `src/frontend/mock/` и задача — не «сделать игру»).
- Тесты и прогон в этом ходе.
- Gradio / Streamlit / браузер вместо окна PySide6.
