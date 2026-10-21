# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

## [1.0.0] - 2026-10-17

### Added
- Гостевая книга: `GET/POST /messages`, `GET /health` (показывает версию).
- Миграции схемы при старте, только расширяющие (таблица `schema_migrations`).
- Docker-образ на uv, `compose.yaml` (app + PostgreSQL), конфиг через pydantic-settings.
- CI: Ruff + pytest на push и PR; CD: образ в ghcr.io из `main` и по тегам `vX.Y.Z`.
- `compose.prod.yaml` и `scripts/deploy.sh` для выката/отката по тегу; README, RUNBOOK.
