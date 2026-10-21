# Guestbook: от коммита до прода

Гостевая книга (FastAPI + PostgreSQL). Это капстоун-проект: сама бизнес-логика минимальная, главное в нём — эксплуатация.
Каждый коммит проходит линтер и тесты, образ публикуется в GitHub Container Registry, релизы версионируются git-тегами,
а откат на предыдущую версию делается одной командой.

```
push ──► CI: Ruff + pytest ──► (main) образ :latest в ghcr.io
tag vX.Y.Z ──► CI ──► образ :vX.Y.Z в ghcr.io ──► deploy.sh vX.Y.Z  (откат: deploy.sh <прошлый тег>)
```

## Быстрый старт (локально)

Нужны Docker и (для разработки) [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env          # задайте свой POSTGRES_PASSWORD
docker compose up -d --build  # сервис + PostgreSQL одной командой
curl localhost:8000/health    # {"status":"ok","version":"local"}
```

Документация API (Swagger): http://localhost:8000/docs

| Метод | Путь        | Что делает                                  |
|-------|-------------|---------------------------------------------|
| GET   | `/health`   | Жив ли сервис и база, какая версия запущена |
| GET   | `/messages` | Последние сообщения (`?limit=50`)           |
| POST  | `/messages` | Добавить: `{"author": "...", "text": "..."}` |

## Разработка

```bash
uv sync                       # зависимости из uv.lock (Python закреплён в .python-version)
docker compose up -d db       # база для тестов
uv run pytest                 # тесты
uv run ruff check . && uv run ruff format --check .
```

## Как устроено

| Что | Где |
|-----|-----|
| Зависимости | `pyproject.toml` + `uv.lock`, Python 3.12 (`.python-version`) |
| Конфиг | `src/guestbook/config.py` (pydantic-settings, всё из env / `.env`) |
| Образ | `Dockerfile`: зависимости ставятся до копирования кода (кэш слоёв), не root, `HEALTHCHECK` |
| Локальный запуск | `compose.yaml`: app + postgres, healthcheck, `depends_on: service_healthy`, volume `pgdata` |
| Прод | `compose.prod.yaml`: тот же стек, но образ из ghcr.io по тегу; `scripts/deploy.sh` |
| Миграции | `migrations/*.sql`, применяются при старте (`src/guestbook/db.py`), только расширяющие |
| CI/CD | `.github/workflows/ci.yml`: `check` (Ruff + pytest на push/PR) → `publish` (needs: check, только main и теги) |

**Секреты.** `.env` лежит в `.gitignore` и `.dockerignore`. В репозитории есть только `.env.example`, а в compose пароль
подставляется через `${POSTGRES_PASSWORD}`. В CI используется одноразовая тестовая база, образ пушится через встроенный `GITHUB_TOKEN`.

## Релизы

Версии по [SemVer](https://semver.org/lang/ru/), история изменений в [CHANGELOG.md](CHANGELOG.md).

```bash
# 1. описать изменения в CHANGELOG.md, закоммитить в main, дождаться зелёного CI
git tag v1.1.0
git push origin v1.1.0        # CI соберёт ghcr.io/<owner>/<repo>:v1.1.0
```

Теги образов: `latest` (последний main), `vX.Y.Z` (релиз), `vX.Y` и `sha-<коммит>`.

## Выкат и откат

```bash
# в .env задайте IMAGE=ghcr.io/<ваш-логин>/<репозиторий> (маленькими буквами)
./scripts/deploy.sh v1.1.0    # выкат
./scripts/deploy.sh v1.0.0    # откат — та же команда с прошлым тегом
```

Скрипт скачивает образ, перезапускает контейнер, ждёт `/health` и подсказывает команду отката.
Что делать, если что-то сломалось, описано в [RUNBOOK.md](RUNBOOK.md).

## Инженерные решения

**Стратегия выката: recreate по неизменяемому тегу.** Прод всегда запускается с конкретным `vX.Y.Z`, а не с `latest`.
Поэтому всегда известно, что именно сейчас работает (это видно и в `/health`), а откат — это выкат прошлого тега:
образ уже лежит в реестре, пересобирать ничего не нужно. У сервиса один инстанс, поэтому используется recreate:
во время перезапуска сервис недоступен несколько секунд. Для учебного сервиса это приемлемо, а blue-green
потребовал бы балансировщик и второй инстанс.

**Миграции только расширяющие (expand-only), поэтому откат безопасен.** Миграции могут добавлять таблицы и
nullable-колонки (или колонки с DEFAULT), но не удаляют и не переименовывают существующие. Значит, *старый* код
работает с *новой* схемой: про новую колонку он просто не знает. Откат делается без отката базы, и данные не теряются.
Если старый код видит в `schema_migrations` миграцию, которой у него нет, он пишет предупреждение и продолжает
работать (это проверяет `tests/test_migrations.py`). Удаление колонки выполняется в два релиза: сначала код
перестаёт её использовать, и только в следующем релизе колонка удаляется.
