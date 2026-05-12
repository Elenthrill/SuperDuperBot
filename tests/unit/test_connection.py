from app.infastructure.database.connection import build_pg_conninfo


def test_build_pg_conninfo_simple_values():
    conninfo = build_pg_conninfo(
        db_name="postgres",
        host="localhost",
        port=5432,
        user="postgres",
        password="secret",
    )

    assert conninfo == "postgresql://postgres:secret@localhost:5432/postgres"


def test_build_pg_conninfo_escapes_user_and_password():
    conninfo = build_pg_conninfo(
        db_name="test_db",
        host="localhost",
        port=5432,
        user="user name",
        password="p@ss word",
    )

    assert conninfo == "postgresql://user%20name:p%40ss%20word@localhost:5432/test_db"

def test_build_pg_conninfo_escapes_special_characters():
    conninfo = build_pg_conninfo(
        db_name="test_db",
        host="localhost",
        port=5432,
        user="user@example.com",
        password="p@ss:word/123",
    )

    assert conninfo == (
        "postgresql://user%40example.com:"
        "p%40ss%3Aword%2F123@localhost:5432/test_db"
    )