import sqlite3

DB_FILE = "movies.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Drop existing tables (start fresh)
    cursor.execute("DROP TABLE IF EXISTS movie_actors")
    cursor.execute("DROP TABLE IF EXISTS actors")
    cursor.execute("DROP TABLE IF EXISTS movies")

    # Movies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date TEXT
        )
    """)

    # Actors table with popularity
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY,
            name TEXT,
            popularity REAL
        )
    """)

    # Relationship table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_actors (
            movie_id INTEGER,
            actor_id INTEGER,
            PRIMARY KEY (movie_id, actor_id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized.")
