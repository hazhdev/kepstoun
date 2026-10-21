# RUNBOOK: что делать, если сломалось

Все команды выполняются на сервере из папки проекта. Здесь `P="docker compose -f compose.prod.yaml"`.

## 0. Быстрая диагностика (первые 2 минуты)

```bash
cat .deployed-version                 # какая версия должна работать
$P ps                                 # статус контейнеров (healthy / unhealthy / restarting)
curl -s localhost:8080/health         # {"status":"ok","version":"vX.Y.Z"}
$P logs --tail=100 app                # ошибки приложения
$P logs --tail=50 db                  # ошибки базы
```

## 1. Плохой релиз → откат (основной сценарий)

Признаки: после `deploy.sh` выросло число ошибок, `/health` не отвечает или отвечает 503, контейнер `app` перезапускается.

```bash
./scripts/deploy.sh vX.Y.Z            # подставьте ПРЕДЫДУЩИЙ рабочий тег
                                      # (его печатает deploy.sh, список — в CHANGELOG.md / GitHub Packages)
curl -s localhost:8080/health         # проверить, что version = прошлый тег
```

Базу откатывать **не нужно**: миграции обратно совместимы (см. README → «Инженерные решения»).
После отката заведите issue, чините в main и выпускайте новый патч-релиз (`vX.Y.Z+1`). Тег не перевыпускайте.

## 2. `/health` отвечает 503 `database unavailable`

```bash
$P ps db                              # жив ли контейнер базы
$P logs --tail=50 db
$P restart db                         # затем: $P restart app
```

* `password authentication failed`: проверьте, что `POSTGRES_PASSWORD` в `.env` совпадает с тем, с которым
  создавался volume. Пароль меняется только в самой базе (`ALTER USER`), правка `.env` его не меняет.
* `No space left on device`: выполните `docker system prune` (удаляет неиспользуемые образы) и проверьте `df -h`.

## 3. Контейнер `app` не стартует

```bash
$P logs app
```

* `задайте POSTGRES_PASSWORD / IMAGE / APP_TAG`: не хватает переменной в `.env` (образец — `.env.example`).
* `manifest unknown` / `denied` при `pull`: такого тега нет в ghcr.io, или пакет приватный. Нужно выполнить
  `docker login ghcr.io -u <login>` с токеном, у которого есть `read:packages`, либо сделать пакет публичным.
* Ошибка миграции (`psycopg.errors...` при старте): выполните откат по п. 1. Миграция идёт в транзакции,
  поэтому при ошибке база остаётся в прежнем состоянии.

## 4. Бэкап и восстановление базы

```bash
$P exec -T db pg_dump -U guestbook guestbook > backup_$(date +%F).sql     # бэкап
$P exec -T db psql -U guestbook guestbook < backup_YYYY-MM-DD.sql         # восстановление
```

Перед релизом с новой миграцией обязательно сделайте бэкап.

## 5. CI красный / образ не опубликовался

* Красный `check`: запустите локально `uv run ruff check . && uv run pytest`. Если упал `uv sync --locked`,
  значит uv.lock устарел: выполните `uv lock` и закоммитьте.
* `publish` не запустился: он работает только для push в `main` и тегов `v*.*.*`, и только после зелёного `check`.
* `denied: installation not allowed to Create organization package`: Settings → Actions → General →
  Workflow permissions → **Read and write**.
