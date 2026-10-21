# Сценарий защиты

Замените `<login>` на свой логин GitHub (в имени образа только маленькие буквы).

## Подготовка (один раз)

```bash
git init -b main && git add -A && git commit -m "feat: guestbook v1.0.0"
# создайте на GitHub пустой репозиторий kapstoun (Public), затем:
git remote add origin https://github.com/<login>/kapstoun.git
git push -u origin main
```

GitHub → репозиторий → **Settings → Actions → General → Workflow permissions → Read and write**.

## 1. Push → зелёный CI → образ :latest

Вкладка **Actions**: job `Lint & test` зелёный, потом `Build & push image`.
Справа на главной странице репозитория откройте **Packages** → `kapstoun`, там есть тег `latest`.
(Package settings → Change visibility → Public, чтобы `docker pull` работал без логина.)

## 2. Релиз v1.0.0

```bash
git tag v1.0.0 && git push origin v1.0.0
```

В Packages появился образ `v1.0.0`.

## 3. Новая версия v1.1.0 (с миграцией)

```bash
git apply demo/v1.1.0.patch       # колонка rating + миграция 0002 + CHANGELOG
git add -A && git commit -m "feat: rating for messages (v1.1.0)"
git push
# дождаться зелёного CI
git tag v1.1.0 && git push origin v1.1.0
```

## 4. Выкат и откат

```bash
cp .env.example .env              # задать POSTGRES_PASSWORD и IMAGE=ghcr.io/<login>/kapstoun

./scripts/deploy.sh v1.0.0
curl -X POST localhost:8080/messages -H 'Content-Type: application/json' -d '{"author":"Аня","text":"до релиза"}'

./scripts/deploy.sh v1.1.0        # выкат: применилась миграция 0002
curl -s localhost:8080/health     # "version":"v1.1.0"
curl -X POST localhost:8080/messages -H 'Content-Type: application/json' -d '{"author":"Оля","text":"с оценкой","rating":5}'

./scripts/deploy.sh v1.0.0        # ОТКАТ
curl -s localhost:8080/health     # "version":"v1.0.0", сервис жив
curl -s localhost:8080/messages   # оба сообщения на месте, данные не потеряны
```

## 5. Документация

Показать `README.md` (раздел «Инженерные решения») и `RUNBOOK.md`.

## 6. Что объяснить

> Миграция `0002_add_rating` только **добавляет nullable-колонку**. Код v1.0.0 о ней не знает: он не читает
> её в SELECT, а в INSERT она получает NULL. Поэтому после отката на v1.0.0 сервис работает с новой схемой,
> базу откатывать не нужно и данные не теряются. Удалять или переименовывать колонку в одном релизе нельзя:
> старый код упадёт. Такое изменение делается в два релиза (expand → contract).
> Выкат идёт по неизменяемому тегу (`v1.1.0`, а не `latest`): всегда видно, что запущено, а откат —
> это просто выкат прошлого тега, который уже лежит в ghcr.io.
