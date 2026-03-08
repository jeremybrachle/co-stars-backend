import sqlite3

DB_FILE = "movies.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

# -----------------------------
# Function 1: BFS to generate a path
# -----------------------------
def generate_path(start_id, start_type, end_id, end_type):
    """
    Returns a list of alternating actor/movie IDs connecting start to end, regardless of type.
    start_type/end_type: "actor" or "movie"
    """
    from collections import deque
    conn = get_connection()
    cursor = conn.cursor()
    queue = deque()
    visited = set()
    queue.append((start_id, start_type, [(start_id, start_type)]))
    visited.add((start_id, start_type))
    while queue:
        curr_id, curr_type, path = queue.popleft()
        if (curr_id, curr_type) == (end_id, end_type):
            # Return only the IDs for pretty_print_path
            return [x[0] for x in path]
        if curr_type == "actor":
            cursor.execute("SELECT movie_id FROM movie_actors WHERE actor_id = ?", (curr_id,))
            for (movie_id,) in cursor.fetchall():
                if (movie_id, "movie") not in visited:
                    visited.add((movie_id, "movie"))
                    queue.append((movie_id, "movie", path + [(movie_id, "movie")]))
        elif curr_type == "movie":
            cursor.execute("SELECT actor_id FROM movie_actors WHERE movie_id = ?", (curr_id,))
            for (actor_id,) in cursor.fetchall():
                if (actor_id, "actor") not in visited:
                    visited.add((actor_id, "actor"))
                    queue.append((actor_id, "actor", path + [(actor_id, "actor")]))
    conn.close()
    return -1  # No path found

# -----------------------------
# Function 2: Verify a given path
# -----------------------------
def verify_path(path):
    """
    Checks that the path is valid: actor -> movie -> next_actor exists in DB
    path = [actor_id, movie_id, actor_id, movie_id, actor_id...]
    """
    if len(path) < 3 or len(path) % 2 == 0:
        return False  # must be odd length: actor -> movie -> actor -> ... -> actor

    conn = get_connection()
    cursor = conn.cursor()

    for i in range(0, len(path) - 2, 2):
        actor1 = path[i]
        movie = path[i+1]
        actor2 = path[i+2]

        cursor.execute("""
            SELECT COUNT(*) FROM movie_actors
            WHERE movie_id = ? AND actor_id IN (?, ?)
        """, (movie, actor1, actor2))
        count = cursor.fetchone()[0]
        if count != 2:
            conn.close()
            return False  # link invalid

    conn.close()
    return True

# -----------------------------
# Optional: Pretty-print a path
# -----------------------------
def pretty_print_path(path, start_type="actor"):
    """
    Converts a path of IDs into readable names from DB.
    start_type: 'actor' or 'movie' (type of first node)
    """
    conn = get_connection()
    cursor = conn.cursor()

    names = []
    curr_type = start_type
    for val in path:
        if curr_type == "actor":
            cursor.execute("SELECT name FROM actors WHERE id = ?", (val,))
            row = cursor.fetchone()
            names.append(row[0] if row else f"Actor {val}")
            curr_type = "movie"
        else:
            cursor.execute("SELECT title FROM movies WHERE id = ?", (val,))
            row = cursor.fetchone()
            names.append(row[0] if row else f"Movie {val}")
            curr_type = "actor"

    conn.close()
    return " -> ".join(names)
