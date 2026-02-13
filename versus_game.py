import sqlite3

DB_FILE = "movies.db"


# -----------------------------
# DB Helper
# -----------------------------
def run_query(sql, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# -----------------------------
# Lookups
# -----------------------------
def get_actor_by_name(name):
    row = run_query(
        "SELECT id, name FROM actors WHERE name = ? COLLATE NOCASE",
        (name,)
    )
    return row[0] if row else None


def get_movies_for_actor(actor_id):
    return run_query("""
        SELECT m.id, m.title
        FROM movies m
        JOIN movie_actors ma ON m.id = ma.movie_id
        WHERE ma.actor_id = ?
        ORDER BY RANDOM()
        LIMIT 7
    """, (actor_id,))


def get_costars_for_movie(movie_id, exclude_names):

    base_sql = """
        SELECT a.id, a.name
        FROM actors a
        JOIN movie_actors ma ON a.id = ma.actor_id
        WHERE ma.movie_id = ?
    """

    params = [movie_id]

    if exclude_names:
        placeholders = ",".join("?" * len(exclude_names))
        base_sql += f" AND a.name NOT IN ({placeholders})"
        params.extend(exclude_names)

    base_sql += """
        ORDER BY a.popularity DESC
        LIMIT 7
    """

    return run_query(base_sql, tuple(params))


# -----------------------------
# Path Validation
# -----------------------------
def validate_path(path):
    for i in range(0, len(path) - 2, 2):
        actor_name = path[i]
        movie_title = path[i + 1]
        next_actor = path[i + 2]

        rows = run_query("""
            SELECT 1
            FROM actors a1
            JOIN movie_actors ma1 ON a1.id = ma1.actor_id
            JOIN movies m ON ma1.movie_id = m.id
            JOIN movie_actors ma2 ON m.id = ma2.movie_id
            JOIN actors a2 ON ma2.actor_id = a2.id
            WHERE a1.name = ?
            AND m.title = ?
            AND a2.name = ?
        """, (actor_name, movie_title, next_actor))

        if not rows:
            return False

    return True


# -----------------------------
# Visual Renderer
# -----------------------------
def render_board(path, target_actor):
    print("\n" + "=" * 80)

    # Header line
    print(f"{path[0]}   ↔   {target_actor}")
    print("     ↓")

    indent = 0

    # Start from the first movie, not the first actor
    for node in path[1:]:
        indent += 4
        if node != target_actor:
            print(" " * indent + node)
            print(" " * indent + "     ↓")
        else:
            print(" " * indent + node + "  ←  Match found!")

    print("=" * 80)

# -----------------------------
# Loop Rewind Logic
# -----------------------------
def rewind_if_loop(path, new_movie):
    if new_movie in path:
        first_index = path.index(new_movie)

        # Movie indices should always be odd
        if first_index % 2 != 1:
            return path  # safety guard

        rewind_index = first_index - 1  # go back to actor before movie

        print(f"\n🔁 Loop detected. Rewinding to '{path[rewind_index]}'.")
        return path[:rewind_index + 1]

    return path

def print_victory_path(path):
    """
    Prints the final validated path with alternating "was in" and "with" labels.
    Format: actor → was in → movie → with → actor → was in → movie, etc.
    """
    print("\n" + "=" * 80)
    print("🏆 VICTORY PATH 🏆")
    print("=" * 80 + "\n")
    
    indent = 0
    
    for i, node in enumerate(path):
        # Print the node
        print(" " * indent + node)
        
        # Don't print arrow/label after the last node
        if i < len(path) - 1:
            indent += 4
            
            # Determine label based on position
            # Even indices (0, 2, 4...) are actors, odd (1, 3, 5...) are movies
            if i % 2 == 0:
                # Current node is an actor, next is a movie
                label = "was in"
            else:
                # Current node is a movie, next is an actor
                label = "with"
            
            print(" " * (indent - 4) + "↓")
            print(" " * (indent - 4) + label)
    
    print("\n" + "=" * 80)

# -----------------------------
# Game Loop
# -----------------------------
def play_vs_game(actor1_name, actor2_name):

    actor1 = get_actor_by_name(actor1_name)
    actor2 = get_actor_by_name(actor2_name)

    if not actor1 or not actor2:
        print("One or both actors not found.")
        return

    print("\n🎭 Actor Versus Mode")
    print(f"1. {actor1_name}")
    print(f"2. {actor2_name}")

    choice = input("\nChoose your starting actor (1 or 2): ").strip()

    if choice == "1":
        start_actor = actor1
        target_actor = actor2
    elif choice == "2":
        start_actor = actor2
        target_actor = actor1
    else:
        print("Invalid choice.")
        return

    current_actor_id, current_actor_name = start_actor
    target_name = target_actor[1]

    path = [current_actor_name]

    while True:

        render_board(path, target_name)

        # --- Movie selection ---
        movies = get_movies_for_actor(current_actor_id)
        if not movies:
            print("No movies available.")
            return

        # print("\nMovies:")
        print(f"\nMovies starring {current_actor_name}:")
        for i, (_, title) in enumerate(movies, 1):
            print(f"{i}. {title}")

        # Allow back option if not first round
        back_option = None
        if len(path) > 1:
            back_option = len(movies) + 1
            print(f"{back_option}. ⬅ Back to previous actor")

        # Handle back option
        m_choice = input("Choose a movie: ").strip()
        if back_option and m_choice.isdigit() and int(m_choice) == back_option:
            removed_actor = path.pop()
            removed_movie = path.pop()
            print(f"\n↩ Returning from '{removed_actor}' via '{removed_movie}'.")
            current_actor_name = path[-1]
            current_actor_id = get_actor_by_name(current_actor_name)[0]
            continue

        if not m_choice.isdigit() or not (1 <= int(m_choice) <= len(movies)):
            print("Invalid choice.")
            continue

        movie_id, movie_title = movies[int(m_choice) - 1]

        # Loop prevention
        path = rewind_if_loop(path, movie_title)
        path.append(movie_title)

        render_board(path, target_name)

        # --- Costar selection ---
        costars = get_costars_for_movie(movie_id, path)
        if not costars:
            print("No costars found.")
            return

        # print("\nCostars:")
        print(f"\nCostars in {movie_title}:")
        for i, (_, name) in enumerate(costars, 1):
            print(f"{i}. {name}")

        # print(f"{i+1}. ⬅ Back to previous movie")
        back_option = len(costars) + 1
        print(f"{back_option}. ⬅ Back to previous movie")

        a_choice = input("Choose a costar: ").strip()

        if a_choice.isdigit() and int(a_choice) == back_option:
            removed_movie = path.pop()
            print(f"\n↩ Returning from '{removed_movie}'.")
            continue



        next_actor_id, next_actor_name = costars[int(a_choice) - 1]
        path.append(next_actor_name)

        # Win check
        if next_actor_name.lower() == target_name.lower():
            render_board(path, target_name)
            print("\n🎉 Target reached!")

            if validate_path(path):
                connections = (len(path) - 2) # // subtract 2 for the original actor and target actor
                print(f"Valid path confirmed.")
                print(f"Total connections: {connections}")
                # print_victory_path(path)
            else:
                print("Path validation failed.")

            return

        current_actor_id = next_actor_id
        current_actor_name = next_actor_name


# -----------------------------
# Entry
# -----------------------------
if __name__ == "__main__":
    play_vs_game("George Clooney", "Tobey Maguire")
