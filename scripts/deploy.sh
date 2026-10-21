#!/usr/bin/env bash
# Выкат или откат на конкретную версию: ./scripts/deploy.sh v1.1.0
set -euo pipefail

TAG="${1:?Укажите тег: ./scripts/deploy.sh v1.0.0}"
cd "$(dirname "$0")/.."

PREV="$(cat .deployed-version 2>/dev/null || echo 'нет')"
echo ">> Сейчас: $PREV  →  выкатываем: $TAG"

export APP_TAG="$TAG"
docker compose -f compose.prod.yaml pull app
docker compose -f compose.prod.yaml up -d

echo ">> Ждём /health ..."
for i in $(seq 1 30); do
  if body="$(curl -fsS http://localhost:8080/health 2>/dev/null)"; then
    echo ">> OK: $body"
    echo "$TAG" > .deployed-version
    echo ">> Откат при проблемах: ./scripts/deploy.sh $PREV"
    exit 0
  fi
  sleep 2
done

echo "!! Сервис не поднялся за 60 секунд. Логи: docker compose -f compose.prod.yaml logs app"
echo "!! Откат: ./scripts/deploy.sh $PREV"
exit 1
