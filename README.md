# BGITU Hardware Management

Backend-сервис для учёта компьютерного оборудования в корпусах и аудиториях.  
Проект построен на FastAPI, PostgreSQL и Redis. Внутри есть CRUD по корпусам, аудиториям и оборудованию, аутентификация, аудит действий, работа с файлами, аналитика и realtime-обновления через WebSocket.

## Что есть в проекте

- аутентификация с access token и refresh token
- пользователи, роли и приглашения на регистрацию
- корпуса, аудитории и оборудование с координатами на сетке
- загрузка файлов к единицам оборудования
- аудит действий пользователей
- аналитика по оборудованию
- Celery-задачи для фоновой очистки сессий
- WebSocket для обновления данных аудиторий без перезагрузки страницы

## Стек

- Python 3.13
- FastAPI
- SQLAlchemy 2.x + asyncpg
- PostgreSQL
- Redis
- Celery
- Alembic
- Loguru
- uv

## Структура проекта

- `api/` — HTTP endpoints
- `core/` — конфиг, безопасность, логирование, seed
- `db/` — создание engine и сессий
- `models/` — ORM-модели
- `schemas/` — Pydantic-схемы
- `repositories/` — работа с базой
- `services/` — бизнес-логика
- `dependencies/` — FastAPI dependencies
- `tasks/` — Celery tasks
- `utils/` — вспомогательные функции
- `websocket/` — realtime-логика и Redis-backed WebSocket
- `alembic/` — миграции
- `static/` — загруженные файлы и аватары
- `logs/` — лог-файлы приложения

## Требования

- Python 3.13+
- PostgreSQL 17+ или совместимая версия
- Redis 7+
- `uv` для локального запуска
- Docker и Docker Compose, если запускать инфраструктуру контейнерами

## Быстрый старт локально

### 1. Подготовить переменные окружения

Скопируйте пример:

```powershell
Copy-Item .env.example .env
```

Проверьте минимум:

- `BGITU__DB__*`
- `BGITU__JWT__ACCESS_SECRET_KEY`
- `BGITU__CELERY__BROKER_URL`
- `BGITU__CELERY__RESULT_BACKEND`
- `BGITU__WEBSOCKET__*`

### 2. Поднять PostgreSQL и Redis

Если локально базы нет, можно поднять только инфраструктуру:

```powershell
docker compose up -d db redis redis_gui
```

После этого будут доступны:

- PostgreSQL на `localhost:5433`
- Redis на `localhost:6379`
- Redis Insight на `http://localhost:5540`

### 3. Установить зависимости

```powershell
uv sync
```

### 4. Применить миграции

```powershell
uv run alembic upgrade head
```

### 5. Заполнить базу начальными данными

```powershell
uv run python -m core.seed
```

Seed добавляет:

- корпуса с `id=1` и `id=2`
- суперпользователя `admin / admin`

### 6. Запустить backend

```powershell
uv run uvicorn main:app --reload
```

По умолчанию приложение будет доступно на `http://127.0.0.1:8000`.

Документация OpenAPI:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

### 7. Запустить Celery

Worker:

```powershell
uv run celery -A celery_app:celery_app worker -l info
```

Beat:

```powershell
uv run celery -A celery_app:celery_app beat -l info
```

## Запуск через Docker Compose

Для backend-части обычно достаточно:

```powershell
docker compose up --build db redis redis_gui backend celery_worker celery_beat
```

Важно: сервис `frontend` в `docker-compose.yaml` сейчас ссылается на внешний путь:

```text
E:\University\JS\frontend_computers
```

Если этого каталога на машине нет, запускайте compose без сервиса `frontend` или сначала исправьте `build` в `docker-compose.yaml`.

## Конфигурация

Все настройки читаются из `.env` с префиксом `BGITU__`.

Основные группы:

- `BGITU__DB__*` — подключение к PostgreSQL
- `BGITU__JWT__*` — access token и время жизни токенов
- `BGITU__CELERY__*` — Redis broker и backend для Celery
- `BGITU__WEBSOCKET__*` — realtime и Redis для WebSocket
- `BGITU__CORS_ORIGINS` — список разрешённых origin для фронтенда
- `BGITU__FRONTEND_URL` — URL фронтенда, используется в приглашениях

Пример `BGITU__CORS_ORIGINS` должен быть JSON-массивом в одну строку:

```env
BGITU__CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

## WebSocket и realtime

WebSocket endpoint:

```text
/ws
```

Можно подключаться двумя способами:

- `/ws?audience_id=123` — получать обновления только по одной аудитории
- `/ws` — получать обновления по всем аудиториям

Здесь `audience_id` — это именно `id` аудитории в базе, а не номер кабинета вроде `105`.

Пример подключения с фронтенда:

```ts
const ws = new WebSocket(`ws://localhost:8000/ws?audience_id=${audienceId}`);
```

Сейчас во внешний сокет уходит payload такого вида:

```json
{"audience_updated": 123}
```

### Как это работает внутри

- backend держит сами объекты `WebSocket` только локально, в памяти процесса
- Redis хранит реестр активных соединений и активных backend-инстансов
- при изменении аудитории событие публикуется в Redis Pub/Sub
- все backend-инстансы получают это событие
- каждый инстанс отправляет сообщение только своим локальным сокетам

Если `BGITU__WEBSOCKET__ENABLED=0`, то:

- `/ws` не принимает подключения
- realtime-события из HTTP endpoints не публикуются
- Redis-клиенты для WebSocket не создаются