<div align="center">

# BGITU Hardware Management

### Backend-сервис для учета компьютерного оборудования в корпусах и аудиториях БГИТУ

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Vue" src="https://img.shields.io/badge/Vue-Frontend-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img alt="Redis" src="https://img.shields.io/badge/Redis-Cache%20%2F%20Broker-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img alt="MinIO" src="https://img.shields.io/badge/MinIO-Object%20Storage-C72E49?style=for-the-badge&logo=minio&logoColor=white">
  <img alt="Celery" src="https://img.shields.io/badge/Celery-Tasks-37814A?style=for-the-badge">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img alt="Prometheus" src="https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=for-the-badge&logo=prometheus&logoColor=white">
  <img alt="Grafana" src="https://img.shields.io/badge/Grafana-Dashboards-F46800?style=for-the-badge&logo=grafana&logoColor=white">
</p>

<p>
  <b>Учет оборудования · аудит действий · файлы · аналитика · SSE realtime · уведомления · observability</b>
</p>

</div>

---

## Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Технологический стек](#технологический-стек)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Быстрый старт локально](#быстрый-старт-локально)
- [Запуск через Docker Compose](#запуск-через-docker-compose)
- [Конфигурация](#конфигурация)
- [Хранение файлов](#хранение-файлов)
- [SSE и realtime](#sse-и-realtime)
- [Observability](#observability)
- [API](#api)
- [Seed-данные](#seed-данные)
- [Roadmap](#roadmap)

---

## О проекте

**BGITU Hardware Management** — backend-сервис для централизованного учета компьютерного оборудования, размещенного в учебных корпусах и аудиториях.

Система помогает хранить сведения об аудиториях, оборудовании, файлах, пользователях и действиях в одном месте.
Backend предоставляет REST API для frontend-приложения, поддерживает аутентификацию, аудит, аналитику, фоновые задачи, хранение файлов и realtime-обновления через SSE.

Проект ориентирован на практическую эксплуатацию в образовательной организации: преподаватель или администратор может быстро открыть аудиторию, увидеть оборудование, изменить его состояние и зафиксировать событие в системе.

---

## Возможности

### Учет оборудования

- учет корпусов и аудиторий;
- учет оборудования с координатами на сетке аудитории;
- хранение инвентарных и серийных номеров;
- хранение характеристик оборудования;
- загрузка файлов и аватаров;
- получение аналитики по оборудованию.

### Пользователи и доступ

- аутентификация через access token и refresh token;
- пользователи, роли и приглашения на регистрацию;
- хранение refresh-сессий;
- фоновая очистка устаревших сессий;
- разграничение доступа к защищенным endpoint-ам.

### Аудит и realtime

- журнал действий пользователей;
- фиксация значимых операций;
- SSE-обновления данных аудитории без перезагрузки страницы;
- realtime-уведомления frontend-клиентов;
- Redis-backed Pub/Sub для доставки realtime-событий между backend-инстансами.

### Интеграции и инфраструктура

- MinIO для объектного хранения файлов;
- Celery для фоновых задач;
- Prometheus, Loki, Promtail и Grafana для локальной наблюдаемости.

---

## Технологический стек


| Область         | Технологии                                   |
| --------------- | -------------------------------------------- |
| Backend         | Python 3.13, FastAPI, Pydantic               |
| Database        | PostgreSQL, SQLAlchemy 2.x, asyncpg, Alembic |
| Cache / Broker  | Redis                                        |
| Background jobs | Celery, Celery Beat                          |
| File storage    | Local storage, MinIO                         |
| Realtime        | SSE, Redis Pub/Sub                           |
| Logging         | Loguru                                       |
| Observability   | Prometheus, Loki, Promtail, Grafana          |
| Tooling         | uv, Docker, Docker Compose                   |


---

## Архитектура

```mermaid
flowchart LR
    Client[Frontend SPA / Browser] -->|REST API| API[FastAPI Backend]
    Client -->|SSE /events| API

    API --> DB[(PostgreSQL)]
    API --> Redis[(Redis)]
    API --> Storage[(MinIO / Local storage)]
    API --> Logs[Loguru logs]

    Redis --> Celery[Celery worker]
    Celery --> DB
    Celery --> Redis

    API --> Metrics[Prometheus metrics]

    Prometheus[Prometheus] --> Grafana[Grafana]
    Promtail[Promtail] --> Loki[Loki]
    Loki --> Grafana
```



Основной поток работы:

1. frontend отправляет запрос к backend API;
2. backend проверяет пользователя и права доступа;
3. сервисный слой выполняет бизнес-логику;
4. данные сохраняются в PostgreSQL;
5. при необходимости создается audit log;
6. realtime-событие публикуется через Redis Pub/Sub;
7. подключенные клиенты получают обновление через SSE.

---

## Структура проекта

```text
.
├── api/              # HTTP endpoints
├── core/             # конфиг, безопасность, логирование, seed
├── db/               # engine, sessions, database setup
├── models/           # SQLAlchemy ORM-модели
├── schemas/          # Pydantic-схемы
├── repositories/     # слой доступа к данным
├── services/         # бизнес-логика
├── dependencies/     # FastAPI dependencies
├── tasks/            # Celery tasks
├── utils/            # вспомогательные функции
├── websocket/        # realtime-логика и Redis-backed SSE
├── alembic/          # миграции базы данных
├── static/           # загруженные файлы и аватары
├── logs/             # лог-файлы приложения
└── scripts/          # служебные скрипты запуска
```

---

## Требования

Для локального запуска понадобятся:

- Python 3.13+
- PostgreSQL 17+ или совместимая версия
- Redis 7+
- MinIO, если используется объектное хранилище
- `uv`
- Docker и Docker Compose для контейнерного запуска

---

## Быстрый старт локально

### 1. Подготовить переменные окружения

```powershell
Copy-Item .env.example .env
```

Проверьте минимально необходимые группы переменных:

```text
BGITU__DB__*
BGITU__JWT__ACCESS_SECRET_KEY
BGITU__CELERY__BROKER_URL
BGITU__CELERY__RESULT_BACKEND
BGITU__STORAGE__*
BGITU__WEBSOCKET__*
```

### 2. Поднять инфраструктуру

```powershell
docker compose up -d db redis minio
```

После запуска будут доступны:


| Сервис        | Адрес                   |
| ------------- | ----------------------- |
| PostgreSQL    | `localhost:5433`        |
| Redis         | `localhost:6379`        |
| MinIO API     | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |


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

### 6. Запустить backend

```powershell
uv run uvicorn main:app --reload
```

Приложение будет доступно по адресу:

```text
http://127.0.0.1:8000
```

OpenAPI-документация:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

### 7. Запустить Celery

Worker:

```powershell
uv run celery -A celery_app:celery_app worker -l info
```

Beat:

```powershell
uv run celery -A celery_app:celery_app beat -l info
```

---

## Запуск через Docker Compose

Полный стек поднимается одной командой:

```powershell
docker compose up -d --build
```

Если Docker создал stale-контейнеры со ссылкой на удаленную сеть, используйте безопасный запуск:

```powershell
.\scripts\docker-up.ps1
```

Для Docker Compose в репозитории есть tracked-файл:

```text
.env.docker.example
```

Локальные секреты и переопределения можно положить в:

```text
.env.docker
```

Этот файл игнорируется git.

---

## Конфигурация

Настройки читаются из переменных окружения с префиксом `BGITU__`.


| Группа                | Назначение                                   |
| --------------------- | -------------------------------------------- |
| `BGITU__DB__*`        | подключение к PostgreSQL                     |
| `BGITU__JWT__*`       | access token и время жизни токенов           |
| `BGITU__CELERY__*`    | Redis broker и result backend для Celery     |
| `BGITU__STORAGE__*`   | backend хранения файлов: `local` или `minio` |
| `BGITU__WEBSOCKET__*` | realtime и Redis для SSE                     |
| `BGITU__CORS_ORIGINS` | список разрешенных origin для frontend       |
| `BGITU__FRONTEND_URL` | URL frontend, используется в приглашениях    |


Для PostgreSQL в Docker также нужны:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

Пример `BGITU__CORS_ORIGINS`:

```env
BGITU__CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

---

## Хранение файлов

Файлы оборудования и аватары отдаются через backend API, а не напрямую из bucket.
Так сохраняется проверка прав на endpoint-ах.

```text
/api/v1/hardware/files/{file_id}
/api/v1/hardware/stream/{file_id}
/api/v1/users/me/photo
```

В Docker Compose используется MinIO.

Доступ с хоста:


| Компонент     | Адрес                   |
| ------------- | ----------------------- |
| MinIO API     | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |


Основные переменные:

```env
BGITU__STORAGE__BACKEND=minio
BGITU__STORAGE__ENDPOINT=localhost:9000
BGITU__STORAGE__ACCESS_KEY=minioadmin
BGITU__STORAGE__SECRET_KEY=minioadmin
BGITU__STORAGE__BUCKET=bgitu-files
BGITU__STORAGE__SECURE=false
```

---

## SSE и realtime

SSE endpoint:

```text
/events
```

Подключение к конкретной аудитории:

```text
/events?audience_id=123
```

Подключение ко всем аудиториям:

```text
/events
```

`audience_id` — это `id` аудитории в базе, а не номер кабинета.

Пример подключения с frontend:

```ts
const events = new EventSource(
  `http://localhost:8000/events?audience_id=${audienceId}`
);
```

Payload события:

```json
{
  "audience_updated": 123
}
```

### Как работает доставка событий

```mermaid
sequenceDiagram
    participant API as Backend API
    participant Redis as Redis Pub/Sub
    participant Instance as Backend instance
    participant Client as Frontend EventSource

    API->>Redis: publish audience_updated
    Redis-->>Instance: receive event
    Instance-->>Client: send SSE message
```



Если `BGITU__WEBSOCKET__ENABLED=0`, то:

- `/events` не принимает подключения;
- realtime-события из HTTP endpoint-ов не публикуются;
- Redis-клиенты для SSE не создаются.

## Observability

Для локального мониторинга добавлен стек:

```text
Prometheus + Loki + Promtail + Grafana
```

URL:


| Сервис          | Адрес                           |
| --------------- | ------------------------------- |
| Backend metrics | `http://localhost:8000/metrics` |
| Prometheus      | `http://localhost:9090`         |
| Grafana         | `http://localhost:3000`         |
| Loki            | `http://localhost:3100`         |


Стандартные учетные данные Grafana:

```text
admin / admin
```

---

## API

Основная документация API доступна через Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Основные группы endpoint-ов:

```text
/api/v1/auth
/api/v1/users
/api/v1/offices
/api/v1/audiences
/api/v1/hardware
/api/v1/analytics/hardware
/api/v1/notifications
```

---

## Seed-данные

Команда:

```powershell
uv run python -m core.seed
```

Добавляет:

- корпус с `id=1`;
- корпус с `id=2`;
- суперпользователя `admin / admin`.

> После первого запуска пароль суперпользователя лучше изменить.

---

## Roadmap

- [x] CRUD по корпусам
- [x] CRUD по аудиториям
- [x] CRUD по оборудованию
- [x] Координаты оборудования на сетке аудитории
- [x] Access token и refresh token
- [x] Роли пользователей
- [x] Приглашения на регистрацию
- [x] Загрузка файлов
- [x] Аудит действий
- [x] Аналитика по оборудованию
- [x] SSE realtime-обновления
- [x] Celery-задачи
- [x] MinIO-хранилище
- [x] Observability stack
- [x] Frontend realtime-уведомления
- [ ] Расширенная аналитика неисправностей
- [ ] История обслуживания оборудования
- [ ] Заявки на ремонт
- [ ] Экспорт отчетов

---

## Автор

**Мишин А.М.**

ФГБОУ ВО «Брянский государственный инженерно-технологический университет»
Кафедра «Информационные технологии»

---



**BGITU Hardware Management**
Учебный проект для автоматизации учета компьютерного оборудования университета.
