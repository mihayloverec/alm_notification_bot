# ALM Notification Bot — Design Spec

**Дата:** 2026-05-15
**Статус:** утверждено к реализации

## 1. Цель

Telegram-бот для уведомления игроков о событиях в турнирах. Игроки подписываются на интересующие турниры и получают рассылки от админов. Админы могут управлять турнирами и рассылать сообщения (с markdown и медиа).

## 2. Сценарии использования

### Игрок
- Запускает бота через `/start`, видит главное меню.
- Просматривает список активных турниров с описаниями.
- Подписывается на один или несколько турниров.
- Видит свои подписки, может отписаться.
- Получает рассылки от админа по подписанным турнирам и общие рассылки.

### Админ
- Добавляет новый турнир (название + описание).
- Редактирует существующий турнир (название и/или описание).
- Закрывает/открывает турнир (флаг `is_active`). Закрытые скрываются из меню подписки игрока, подписки в БД сохраняются.
- Делает рассылку:
  - по конкретному турниру (только подписчикам);
  - по всем пользователям бота.
- Видит отчёт по результатам рассылки.

## 3. Стек

- **Python 3.12**
- **aiogram 3.x** (async Telegram Bot framework)
- **aiosqlite** (async SQLite)
- **pytest** + **pytest-asyncio** для тестов
- **python-dotenv** для загрузки `.env`
- Деплой: **Docker + docker-compose**

## 4. Структура проекта

```
alm_notification_bot/
├── .env.example
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── data/                       # volume для SQLite (gitignored)
├── docs/specs/                 # эта спека
├── src/bot/
│   ├── __init__.py
│   ├── __main__.py             # точка входа, запуск polling
│   ├── config.py               # загрузка и валидация .env
│   ├── db.py                   # инициализация БД, миграции схемы
│   ├── states.py               # FSM-состояния (StatesGroup)
│   ├── texts.py                # все строки UI (RU)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── tournaments.py
│   │   └── subscriptions.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py           # /start, /help
│   │   ├── user.py             # подписки, мои турниры
│   │   ├── admin.py            # /admin, управление турнирами
│   │   └── broadcast.py        # FSM рассылки
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── broadcast.py        # rate-limited отправка
│   └── middlewares/
│       ├── __init__.py
│       └── admin_only.py
└── tests/
    ├── __init__.py
    ├── conftest.py             # фикстура in-memory БД
    ├── test_repositories.py
    └── test_broadcast_recipients.py
```

## 5. Данные

SQLite, схема создаётся при старте, если БД пустая. Простой механизм версии схемы — поле `PRAGMA user_version` (на будущее, при наличии миграций).

```sql
CREATE TABLE users (
    user_id     INTEGER PRIMARY KEY,           -- Telegram user id
    username    TEXT,
    first_name  TEXT,
    is_blocked  INTEGER NOT NULL DEFAULT 0,    -- 1 если пользователь заблокировал бота
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tournaments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    user_id       INTEGER NOT NULL,
    tournament_id INTEGER NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, tournament_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);

CREATE INDEX idx_subscriptions_tournament ON subscriptions(tournament_id);
CREATE INDEX idx_tournaments_active ON tournaments(is_active);
```

`PRAGMA foreign_keys = ON` при подключении.

## 6. UX

### 6.1 Игрок

- `/start` → upsert в `users`, приветствие + главное меню (inline):
  - `[📋 Турниры]` `[✅ Мои подписки]`
- **Турниры**: список активных турниров (кнопка на каждый турнир — её имя). Тап → карточка с `name` и `description`, кнопка `[➕ Подписаться]` или `[➖ Отписаться]` (в зависимости от текущего статуса), кнопка `[⬅️ Назад]`.
- **Мои подписки**: список подписок пользователя. Закрытые турниры показываются с пометкой `[Закрыт]`, чтобы игрок понимал, почему не приходят уведомления, и мог отписаться. Тап → карточка + кнопка отписки.

Если активных турниров нет — сообщение «Сейчас нет активных турниров».

### 6.2 Админ

Доступ к админ-командам ограничен middleware `admin_only`, который проверяет `user_id in config.admin_ids`.

- `/admin` → меню (inline):
  - `[➕ Добавить турнир]` `[📝 Управление]` `[📢 Рассылка]`
- **Добавить турнир** (FSM `AddTournament`):
  1. «Введите название» → ждём текст → сохраняем в state.
  2. «Введите описание» (с подсказкой «можно с markdown») → ждём текст.
  3. Превью карточки (как её увидит игрок: `name` + `description` с применённым markdown) + `[✅ Сохранить]` `[❌ Отмена]`.
  4. На «Сохранить» — INSERT, ответ «Турнир добавлен», возврат в админ-меню.
- **Управление**: список ВСЕХ турниров (активных и закрытых, с пометкой). Тап → карточка + кнопки:
  - `[✏️ Название]` (FSM `EditTournamentName`) — ввод нового, сохранение.
  - `[✏️ Описание]` (FSM `EditTournamentDescription`) — ввод нового, сохранение.
  - `[🔒 Закрыть]` / `[🔓 Открыть]` — toggle `is_active`.
- **Рассылка** (FSM `Broadcast`):
  1. «Выберите аудиторию»: `[👥 Все]` или кнопки на каждый турнир (только активные).
  2. «Пришлите сообщение для рассылки (можно с markdown и одной картинкой)».
  3. Превью: бот пересылает сообщение админу + «Получателей: N. Отправить?» `[✅ Да]` `[❌ Нет]`.
  4. На «Да» — запуск рассылки, прогресс не показываем (избегаем флуда обновлений), в конце — отчёт:
     `✅ Отправлено: X | 🚫 Заблокировали бота: Y | ⚠️ Ошибки: Z`.

## 7. Сервис рассылки

Файл: `src/bot/services/broadcast.py`.

**Алгоритм:**

```
recipients = repositories.users.get_recipients(tournament_id=None | int)
# если tournament_id is None: все users где is_blocked=0
# иначе: JOIN subscriptions, users где is_blocked=0 и есть подписка

counters = {sent: 0, blocked: 0, errors: 0}

for user_id in recipients:
    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=source_chat_id,
            message_id=source_message_id,
        )
        counters.sent += 1
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        # retry once
        try:
            await bot.copy_message(...)
            counters.sent += 1
        except Exception:
            counters.errors += 1
    except TelegramForbiddenError:
        # пользователь заблокировал бота / удалил чат
        users_repo.mark_blocked(user_id)
        counters.blocked += 1
    except TelegramBadRequest as e:
        # "chat not found", "user is deactivated" и пр.
        users_repo.mark_blocked(user_id)
        counters.blocked += 1
    except Exception:
        log.exception(...)
        counters.errors += 1

    await asyncio.sleep(1 / 25)  # ~25 msg/sec, запас от лимита 30

return counters
```

Рассылка запускается в `asyncio.create_task` от хендлера подтверждения, чтобы не блокировать апдейты. Админу, запустившему рассылку, сразу отвечаем «Рассылка запущена», финальный отчёт приходит отдельным сообщением ему же по завершении.

Markdown в сообщениях: админ сам задаёт форматирование при отправке сообщения боту (Telegram-клиент кодирует его в `entities`). `copy_message` сохраняет `entities` как есть, так что бот не парсит markdown сам и не валидирует — что прислано, то и копируется.

## 8. Конфиг (`.env`)

```
BOT_TOKEN=             # обязательно
ADMIN_IDS=             # обязательно, через запятую: "123,456"
DB_PATH=/app/data/bot.db
LOG_LEVEL=INFO
```

`config.py` валидирует: `BOT_TOKEN` непустой, `ADMIN_IDS` распарсился в список int (минимум один). При невалидной конфигурации — `RuntimeError` на старте.

## 9. Логирование

- `logging.basicConfig(level=LOG_LEVEL)` → stdout (docker подхватит).
- Формат: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- ERROR — необработанные исключения в хендлерах (через `errors_handler`) и ошибки рассылки.
- INFO — старт бота, добавление/закрытие турнира, начало/конец рассылки с цифрами.

## 10. Docker

**Dockerfile** (single-stage, slim):
```
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src ./src
CMD ["python", "-m", "bot"]
```

**docker-compose.yml**:
```yaml
services:
  bot:
    build: .
    container_name: alm_notification_bot
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
```

## 11. Тесты

`tests/conftest.py` — фикстура, создающая in-memory SQLite (`:memory:`) с применённой схемой.

`tests/test_repositories.py`:
- create/get tournament, edit name/description, toggle is_active
- list active tournaments
- subscribe/unsubscribe идемпотентны
- get_recipients(None) возвращает только незаблокированных
- get_recipients(tournament_id) возвращает только подписчиков и только незаблокированных
- mark_blocked корректно меняет флаг

`tests/test_broadcast_recipients.py`:
- сценарий: 3 пользователя, 2 турнира, разные подписки и `is_blocked` — проверяем, что фильтрация рецептов рассылки корректна.

## 12. Решения, отложенные на потом (вне MVP)

- Альбомы (media group) — сейчас только одно сообщение.
- Удаление турниров — есть только закрытие.
- Управление админами через бота — список в `.env`.
- Расписание рассылок / отложенная отправка — нет.
- Аналитика, dashboard — нет.
- Миграции схемы БД через alembic — пока вручную (`user_version` зарезервировано).

## 13. Критерии готовности

- `docker compose up -d --build` запускает бота, он откликается на `/start`.
- Игрок может подписаться/отписаться на активный турнир.
- Админ может добавить, отредактировать и закрыть турнир.
- Админ может разослать сообщение с markdown и картинкой по всем и по конкретному турниру; получает отчёт.
- Заблокированные пользователи помечаются и исключаются из последующих рассылок.
- Тесты репозиториев и подбора получателей проходят (`pytest`).
- Чувствительных данных в репозитории нет, `.env` в `.gitignore`, есть `.env.example`.
