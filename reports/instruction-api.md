# Как поднять и проверить API

Инструкция для разработчика на этой машине (не замена [`instruction.md`](instruction.md) для чужого ПК). Агент Cursor **не** поднимает Docker, пока вы явно не разрешили. Команды — в обычном PowerShell, не в терминале агента в чате.

Канон: корневой `docker-compose.yml`. Сервисы `redis` и `backend`. API слушает **http://localhost:8000**.

## Что поднимается

| Сервис Compose | Роль | Порт на хосте |
| --- | --- | --- |
| `redis` | сессии (idle TTL 30 мин, лимит 3 слота) и глобальная статистика | нет (только сеть Compose, `redis:6379`) |
| `backend` | FastAPI + Uvicorn, REST + WebSocket | **8000** |

Данные Redis на хосте по умолчанию — `F:/Docker/Redis`. Другой диск или папка — `REDIS_DATA_DIR` в `.env` (образец `.env.example`; рабочий `.env` в Git не коммитить). YAML править не нужно.

## Подъём

Docker Desktop должен быть запущен. Из **корня** репозитория:

```powershell
docker compose up --build
```

Первый запуск качает образы и собирает `backend` из `src/backend/Dockerfile`. Оставить логи в этом окне или уйти в фон:

```powershell
docker compose up --build -d
docker compose ps
```

Оба сервиса должны быть `running`; у `redis` — `healthy`. `backend` стартует после healthcheck Redis.

Остановка:

```powershell
docker compose down
```

Локальный Uvicorn без Compose допустим, если Redis уже доступен (`REDIS_URL` из `.env.example`, обычно `redis://localhost:6379/0`). Канон инфраструктуры — Compose.

## Проверка, что API живой

Это проверка **контейнера `backend`**, не YAML-просмотрщиков.

В браузере (обычный Chrome или Edge, не Simple Browser Cursor):

- живой Swagger процесса: [http://localhost:8000/docs](http://localhost:8000/docs)
- статистика JSON (нули, если партий ещё не было): [http://localhost:8000/statistics](http://localhost:8000/statistics)

Ожидание: HTTP 200. В `/statistics` поля вроде `games`, `playerWins`.

PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/statistics
```

Если порт 8000 занят — `docker compose ps` и `docker compose logs backend`.

## Документация контракта (YAML), не сам сервер

Файл `requirements/openapi.yaml` — спецификация OpenAPI 3.0.3, не работающий бэкенд.

`servers.url` `http://localhost:8000` указывает на живой FastAPI. **Try it out** в любом Swagger сходит в этот URL. Без поднятого `backend` будет ошибка соединения — это не дефект контракта.

Просмотрщики YAML (отдельные процессы):

- Swagger UI: http://127.0.0.1:8080/
- ReDoc: http://127.0.0.1:8081/

Запуск: в проводнике папка `requirements` → `run-openapi-docs.bat`. Если 8080 или 8081 заняты, скрипт берёт следующие свободные порты и печатает фактические URL.

Запасной способ — обычный PowerShell:

```powershell
cd e:\Cursor\SeaBattle\requirements
python preview-openapi.py
```

Не путать порты **8080/8081** (картинка YAML) и **8000** (живой API). Try it out на 8080 работает только при поднятом Compose-`backend`.

## Окно игры

Окно PySide6 API не заменяет и само контейнеры не поднимает. Запуск окна: `src/run-frontend.bat` (не из терминала агента). Клиент бьёт в `http://localhost:8000`. Полный сценарий на чужой машине — [`instruction.md`](instruction.md).
