from guestbook.config import Settings


def test_database_url_is_built_from_parts():
    s = Settings(
        postgres_host="db",
        postgres_port=5432,
        postgres_db="g",
        postgres_user="u",
        postgres_password="p",
    )
    assert s.database_url == "postgresql://u:p@db:5432/g"
