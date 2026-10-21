from guestbook import db


def test_migrate_is_idempotent(db_url):
    db.migrate(db_url)
    assert db.migrate(db_url) == []


def test_unknown_newer_migration_does_not_break_old_code(db_url, client):
    """Имитация отката: в базе есть миграция от более новой версии."""
    with db.connect(db_url) as conn:
        conn.execute(
            "INSERT INTO schema_migrations (version) VALUES ('9999_from_future') "
            "ON CONFLICT DO NOTHING"
        )
    try:
        assert db.migrate(db_url) == []
        assert client.get("/health").status_code == 200
    finally:
        with db.connect(db_url) as conn:
            conn.execute("DELETE FROM schema_migrations WHERE version = '9999_from_future'")
