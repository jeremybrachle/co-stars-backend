import sqlite3
from db import DB_FILE

def get_connection():
    return sqlite3.connect(DB_FILE)

def insert_movie(
    movie_id,
    title,
    release_date,
    genres_json=None,
    overview=None,
    poster_path=None,
    original_language=None,
    content_rating=None,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movies (
            id,
            title,
            release_date,
            genres_json,
            overview,
            poster_path,
            original_language,
            content_rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            release_date=COALESCE(excluded.release_date, movies.release_date),
            genres_json=excluded.genres_json,
            overview=excluded.overview,
            poster_path=excluded.poster_path,
            original_language=excluded.original_language,
            content_rating=excluded.content_rating
    """, (
        movie_id,
        title,
        release_date,
        genres_json,
        overview,
        poster_path,
        original_language,
        content_rating,
    ))
    conn.commit()
    conn.close()

def insert_actor(
    actor_id,
    name,
    popularity=None,
    birthday=None,
    deathday=None,
    place_of_birth=None,
    biography=None,
    profile_path=None,
    known_for_department=None,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actors (
            id,
            name,
            popularity,
            birthday,
            deathday,
            place_of_birth,
            biography,
            profile_path,
            known_for_department
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            popularity=COALESCE(excluded.popularity, actors.popularity),
            birthday=excluded.birthday,
            deathday=excluded.deathday,
            place_of_birth=excluded.place_of_birth,
            biography=excluded.biography,
            profile_path=excluded.profile_path,
            known_for_department=excluded.known_for_department
    """, (
        actor_id,
        name,
        popularity,
        birthday,
        deathday,
        place_of_birth,
        biography,
        profile_path,
        known_for_department,
    ))
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

def get_actor_by_id(actor_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, popularity FROM actors WHERE id = ?",
        (actor_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result


def get_movie_by_id(movie_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, release_date FROM movies WHERE id = ?",
        (movie_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result


def get_all_actors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, popularity FROM actors ORDER BY name COLLATE NOCASE ASC"
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_movies():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, release_date FROM movies ORDER BY title COLLATE NOCASE ASC"
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_actors_with_metadata():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            name,
            popularity,
            birthday,
            deathday,
            place_of_birth,
            biography,
            profile_path,
            known_for_department
        FROM actors
        ORDER BY name COLLATE NOCASE ASC
        """
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_movies_with_metadata():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            title,
            release_date,
            genres_json,
            overview,
            poster_path,
            original_language,
            content_rating
        FROM movies
        ORDER BY title COLLATE NOCASE ASC
        """
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_movie_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM movies ORDER BY id ASC")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result


def get_all_movie_actor_links():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT movie_id, actor_id
        FROM movie_actors
        ORDER BY movie_id ASC, actor_id ASC
        """
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_actors_in_movie(movie_id, exclude_names=None):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        SELECT a.id, a.name, a.popularity
        FROM actors a
        JOIN movie_actors ma ON a.id = ma.actor_id
        WHERE ma.movie_id = ?
    """
    params = [movie_id]

    if exclude_names:
        placeholders = ",".join("?" * len(exclude_names))
        sql += f" AND a.name NOT IN ({placeholders})"
        params.extend(exclude_names)

    sql += " ORDER BY a.name COLLATE NOCASE ASC"
    cursor.execute(sql, tuple(params))
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
        ORDER BY m.title COLLATE NOCASE ASC
    """, (actor_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def actor_exists(actor_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM actors WHERE id = ?", (actor_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

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
