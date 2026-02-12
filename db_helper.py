import sqlite3
from db import DB_FILE

def get_connection():
    return sqlite3.connect(DB_FILE)

def insert_movie(movie_id, title, release_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO movies (id, title, release_date)
        VALUES (?, ?, ?)
    """, (movie_id, title, release_date))
    conn.commit()
    conn.close()

def insert_actor(actor_id, name, popularity=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actors (id, name, popularity)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            popularity=COALESCE(excluded.popularity, actors.popularity)
    """, (actor_id, name, popularity))
    conn.commit()
    conn.close()

def insert_relationship(movie_id, actor_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO movie_actors (movie_id, actor_id)
        VALUES (?, ?)
    """, (movie_id, actor_id))
    conn.commit()
    conn.close()

def get_actors_in_movie(movie_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.name, a.popularity
        FROM actors a
        JOIN movie_actors ma ON a.id = ma.actor_id
        WHERE ma.movie_id = ?
    """, (movie_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_movies_for_actor(actor_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.title, m.release_date
        FROM movies m
        JOIN movie_actors ma ON m.id = ma.movie_id
        WHERE ma.actor_id = ?
    """, (actor_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def movie_exists(movie_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM movies WHERE id = ?", (movie_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def movie_exists_by_title(title):
    conn = get_connection()
    cursor = conn.cursor()
    # Case-insensitive comparison
    cursor.execute("SELECT 1 FROM movies WHERE title = ? COLLATE NOCASE", (title,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
