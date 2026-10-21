import logging
from pathlib import Path

import psycopg

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def connect(url: str) -> psycopg.Connection:
    return psycopg.connect(url, autocommit=True)


def migrate(url: str, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Применяет SQL-миграции из migrations/ по порядку имён файлов.

    Правило проекта: миграции только расширяют схему (expand-only),
    поэтому предыдущая версия приложения работает с новой схемой.
    Если в базе есть миграции, которых этот код не знает (база уже
    обновлена более новой версией), — это откат: просто логируем и работаем.
    """
    files = sorted(migrations_dir.glob("*.sql"))
    known = {f.stem for f in files}
    applied_now: list[str] = []
    with connect(url) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version TEXT PRIMARY KEY,"
            " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        unknown = sorted(done - known)
        if unknown:
            log.warning("В базе есть миграции новее этого кода (откат?): %s", unknown)
        for f in files:
            if f.stem in done:
                continue
            with conn.transaction():
                conn.execute(f.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (f.stem,))
            log.info("Применена миграция %s", f.stem)
            applied_now.append(f.stem)
    return applied_now
