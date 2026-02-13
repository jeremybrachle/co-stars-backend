import sqlite3
import difflib
import unicodedata

DB_FILE = "movies.db"


# -----------------------------
# DB Helpers
# -----------------------------
def run_query(sql, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def normalize_text(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower()


def find_closest_match(user_input, valid_options, cutoff=0.6):
    normalized_map = {
        normalize_text(option): option for option in valid_options
    }

    normalized_input = normalize_text(user_input)

    matches = difflib.get_close_matches(
        normalized_input,
        normalized_map.keys(),
        n=1,
        cutoff=cutoff
    )

    if matches:
        return normalized_map[matches[0]]

    return None

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
    # Always return 6 random movies
    return run_query("""
        SELECT m.id, m.title
        FROM movies m
        JOIN movie_actors ma ON m.id = ma.movie_id
        WHERE ma.actor_id = ?
        ORDER BY RANDOM()
        LIMIT 6
    """, (actor_id,))

def get_all_movies_for_actor(actor_id):
    return run_query("""
        SELECT m.id, m.title
        FROM movies m
        JOIN movie_actors ma ON m.id = ma.movie_id
        WHERE ma.actor_id = ?
    """, (actor_id,))

def get_costars_for_movie(movie_id, exclude_names):
    base_sql = """
        SELECT a.id, a.name, a.popularity
        FROM actors a
        JOIN movie_actors ma ON a.id = ma.actor_id
        WHERE ma.movie_id = ?
    """

    params = [movie_id]

    if exclude_names:
        placeholders = ",".join("?" * len(exclude_names))
        base_sql += f" AND a.name NOT IN ({placeholders})"
        params.extend(exclude_names)

    # Step 1: get random pool
    base_sql += """
        ORDER BY RANDOM()
        LIMIT 20
    """

    random_pool = run_query(base_sql, tuple(params))

    # Step 2: sort pool by popularity descending
    sorted_pool = sorted(random_pool, key=lambda x: x[2], reverse=True)

    # Step 3: return top 6
    return [(row[0], row[1]) for row in sorted_pool[:6]]

def get_all_costars_for_movie(movie_id, exclude_names):
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
def render_board(path, target_actor, turn_count, back_count):
    if target_actor == path[-1]:
        depth = (len(path) - 2)
    else:
        depth = (len(path) - 1)
    
    print("\n" + "=" * 80)
    print(f"{path[0]}   ↔   {target_actor}  |  Turn: {turn_count}  |  Depth: {depth}  |  Rewinds: {back_count}  |")
    print("      ↓")

    indent = 0
    for node in path[1:]:
        indent += 4
        if node != target_actor:
            print(" " * indent + node)
            print(" " * indent + "      ↓")
        else:
            print(" " * indent + node + "  ←  Match found!")

    print("=" * 80)


# -----------------------------
# Loop Rewind Logic
# -----------------------------
def rewind_if_loop(path, new_movie):
    if new_movie in path:
        first_index = path.index(new_movie)

        if first_index % 2 != 1:
            return path

        rewind_index = first_index - 1
        print(f"\n🔁 Loop detected. Rewinding to '{path[rewind_index]}'.")
        return path[:rewind_index + 1]

    return path


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
    shuffle_count = 0
    turn_count = 0
    back_count = 0

    while True:

        render_board(path, target_name, turn_count, back_count)

        # -----------------------------
        # MOVIE SELECTION
        # -----------------------------
        while True:
            movies = get_movies_for_actor(current_actor_id)

            if not movies:
                print("No movies available.")
                return

            print(f"\nMovies starring {current_actor_name}:")
            for i, (_, title) in enumerate(movies, 1):
                print(f"{i}. {title}")

            print("7. 🔀 Shuffle")
            print("8. ⬅ Back")
            print("9. ✏ Write-in")

            m_choice = input("Choose a movie: ").strip()

            if m_choice == "" or m_choice == "7":
                shuffle_count += 1
                # print(f"\n🔀 Shuffled! Total reshuffles: {shuffle_count}")
                continue

            if m_choice == "8":
                turn_count += 1
                back_count += 1

                if len(path) > 1:
                    removed_actor = path.pop()
                    removed_movie = path.pop()
                    print(f"\n↩ Returning from '{removed_actor}' via '{removed_movie}'.")
                    current_actor_name = path[-1]
                    current_actor_id = get_actor_by_name(current_actor_name)[0]
                else:
                    print("Cannot go back further.")
                continue

            if m_choice == "9":
                user_text = input("Enter movie name: ").strip()

                full_filmography = get_all_movies_for_actor(current_actor_id)

                if not full_filmography:
                    print("No movies found.")
                    continue
                
                valid_titles = [title for _, title in full_filmography]

                closest = find_closest_match(user_text, valid_titles)

                if closest:
                    print(f"\n🎯 Interpreting as: {closest}")
                    movie_index = valid_titles.index(closest)
                    movie_id, movie_title = full_filmography[movie_index]

                    path.append(movie_title)
                    turn_count += 1
                    break
                else:
                    print("No close match found among current options.")
                    continue

            if not m_choice.isdigit() or not (1 <= int(m_choice) <= 6):
                print("Invalid choice.")
                continue

            movie_id, movie_title = movies[int(m_choice) - 1]
            turn_count += 1
            break

        path = rewind_if_loop(path, movie_title)
        path.append(movie_title)

        render_board(path, target_name, turn_count, back_count)

        # -----------------------------
        # COSTAR SELECTION
        # -----------------------------
        while True:
            costars = get_costars_for_movie(movie_id, path)

            if not costars:
                print("No costars found.")
                return

            print(f"\nCostars in {movie_title}:")
            for i, (_, name) in enumerate(costars, 1):
                print(f"{i}. {name}")

            print("7. 🔀 Shuffle")
            print("8. ⬅ Back")
            print("9. ✏ Write-in")

            a_choice = input("Choose a costar: ").strip()

            if a_choice == "" or a_choice == "7":
                shuffle_count += 1
                # print(f"\n🔀 Shuffled! Total reshuffles: {shuffle_count}")
                continue

            if a_choice == "8":
                turn_count += 1
                back_count += 1
                removed_movie = path.pop()
                print(f"\n↩ Returning from '{removed_movie}'.")
                break

            if a_choice == "9":
                user_text = input("Enter actor name: ").strip()
                
                # Query full cast:
                full_cast = get_all_costars_for_movie(movie_id, path)

                if not full_cast:
                    print("No additional actors found.")
                    continue

                valid_names = [name for _, name in full_cast]
                closest = find_closest_match(user_text, valid_names)

                if closest:
                    print(f"\n🎯 Interpreting as: {closest}")
                    actor_index = valid_names.index(closest)
                    next_actor_id, next_actor_name = full_cast[actor_index]
                    
                    path.append(next_actor_name)
                    turn_count += 1

                    # ✅ ADD THIS WIN CHECK
                    if next_actor_name.lower() == target_name.lower():
                        render_board(path, target_name, turn_count, back_count)
                        print("\n🎉 Target reached!")

                        if validate_path(path):
                            connections = len(path) - 2
                            print("Valid path confirmed.")
                            print(f"Total connections: {connections}")
                            print(f"Total reshuffles used: {shuffle_count}")
                        else:
                            print("Path validation failed.")

                        return

                    # Otherwise continue to next round
                    current_actor_id = next_actor_id
                    current_actor_name = next_actor_name
                    
                    break
                else:
                    print("No close match found in this movie.")
                    continue

            if not a_choice.isdigit() or not (1 <= int(a_choice) <= 6):
                print("Invalid choice.")
                continue

            next_actor_id, next_actor_name = costars[int(a_choice) - 1]
            turn_count += 1
            path.append(next_actor_name)

            if next_actor_name.lower() == target_name.lower():
                render_board(path, target_name, turn_count, back_count)
                print("\n🎉 Target reached!")

                if validate_path(path):
                    connections = len(path) - 2
                    print("Valid path confirmed.")
                    print(f"Total connections: {connections}")
                    print(f"Total reshuffles used: {shuffle_count}")
                else:
                    print("Path validation failed.")

                return

            current_actor_id = next_actor_id
            current_actor_name = next_actor_name
            break


# -----------------------------
# Entry
# -----------------------------
if __name__ == "__main__":
    # play_vs_game("George Clooney", "Tobey Maguire")
    play_vs_game("Matt Damon", "Daniel Craig")