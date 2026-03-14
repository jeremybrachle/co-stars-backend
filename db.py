import sqlite3

DB_FILE = "movies.db"

MOVIE_EXTRA_COLUMNS = {
    "genres_json": "TEXT",
    "overview": "TEXT",
    "poster_path": "TEXT",
    "original_language": "TEXT",
    "content_rating": "TEXT",
}

ACTOR_EXTRA_COLUMNS = {
    "birthday": "TEXT",
    "deathday": "TEXT",
    "place_of_birth": "TEXT",
    "biography": "TEXT",
    "profile_path": "TEXT",
    "known_for_department": "TEXT",
}


def get_connection():
    return sqlite3.connect(DB_FILE)


def _create_tables(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date TEXT,
            genres_json TEXT,
            overview TEXT,
            poster_path TEXT,
            original_language TEXT,
            content_rating TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY,
            name TEXT,
            popularity REAL,
            birthday TEXT,
            deathday TEXT,
            place_of_birth TEXT,
            biography TEXT,
            profile_path TEXT,
            known_for_department TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS movie_actors (
            movie_id INTEGER,
            actor_id INTEGER,
            PRIMARY KEY (movie_id, actor_id)
        )
        """
    )


def _get_existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _add_missing_columns(cursor, table_name, columns):
    existing_columns = _get_existing_columns(cursor, table_name)
    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )


def ensure_schema():
    conn = get_connection()
    cursor = conn.cursor()

    _create_tables(cursor)
    _add_missing_columns(cursor, "movies", MOVIE_EXTRA_COLUMNS)
    _add_missing_columns(cursor, "actors", ACTOR_EXTRA_COLUMNS)

    conn.commit()
    conn.close()
    print("Database schema ensured.")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS movie_actors")
    cursor.execute("DROP TABLE IF EXISTS actors")
    cursor.execute("DROP TABLE IF EXISTS movies")

    _create_tables(cursor)

    conn.commit()
    conn.close()
    print("Database initialized.")
