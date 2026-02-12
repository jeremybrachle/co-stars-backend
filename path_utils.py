import sqlite3

DB_FILE = "movies.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

# -----------------------------
# Function 1: BFS to generate a path
# -----------------------------
def generate_path(start_actor_id, end_actor_id):
    """
    Returns a list like [actor, movie, actor, movie, ..., actor]
    that connects start_actor_id to end_actor_id.
    Uses BFS for shortest path in terms of actor-movie links.
    """
    from collections import deque

    conn = get_connection()
    cursor = conn.cursor()

    visited_actors = set()
    queue = deque()
    queue.append((start_actor_id, [start_actor_id]))  # (current_actor, path_so_far)

    while queue:
        current_actor, path = queue.popleft()
        visited_actors.add(current_actor)

        # Find all movies for this actor
        cursor.execute("SELECT movie_id FROM movie_actors WHERE actor_id = ?", (current_actor,))
        movies = [row[0] for row in cursor.fetchall()]

        for movie_id in movies:
            # Find all co-actors in that movie
            cursor.execute("""
                SELECT actor_id FROM movie_actors
                WHERE movie_id = ? AND actor_id != ?
            """, (movie_id, current_actor))
            co_actors = [row[0] for row in cursor.fetchall()]

            for co_actor in co_actors:
                if co_actor in visited_actors:
                    continue
                new_path = path + [movie_id, co_actor]
                if co_actor == end_actor_id:
                    conn.close()
                    return new_path  # Found a path!
                queue.append((co_actor, new_path))
                visited_actors.add(co_actor)  # mark visited

    conn.close()
    return None  # No path found

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
def pretty_print_path(path):
    """
    Converts a path of IDs into readable names from DB
    """
    conn = get_connection()
    cursor = conn.cursor()

    names = []
    for idx, val in enumerate(path):
        if idx % 2 == 0:  # actor
            cursor.execute("SELECT name FROM actors WHERE id = ?", (val,))
            row = cursor.fetchone()
            names.append(row[0] if row else f"Actor {val}")
        else:  # movie
            cursor.execute("SELECT title FROM movies WHERE id = ?", (val,))
            row = cursor.fetchone()
            names.append(row[0] if row else f"Movie {val}")

    conn.close()
    # Format: Actor -> Movie -> Actor -> ...
    return " -> ".join(names)
