import json
from flask import Flask, render_template, request, redirect, url_for, session
from versus_game import (
    get_actor_by_name, get_movies_for_actor, get_costars_for_movie,
    get_all_movies_for_actor, get_all_costars_for_movie,
    find_closest_match, rewind_if_loop, validate_path
)

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for sessions

# -----------------------------
# Start Page
# -----------------------------
with open("levels.json", "r") as f:
    LEVELS = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        actor1 = request.form["actor1"].strip()
        actor2 = request.form["actor2"].strip()

        a1 = get_actor_by_name(actor1)
        a2 = get_actor_by_name(actor2)

        if not a1 or not a2:
            return render_template("index.html", error="Actor(s) not found", levels=LEVELS)

        session["current_actor_id"], session["current_actor_name"] = a1
        session["target_actor_name"] = a2[1]
        session["path_from_a"] = [a1[1]]
        session["path_from_b"] = [a2[1]]
        session["active_actor"] = "a"  # Start with actor A
        session["turn_count"] = 0
        session["back_count"] = 0
        session["shuffle_count"] = 0

        return redirect(url_for("choose_movie"))

    return render_template("index.html", levels=LEVELS)


# -----------------------------
# Movie Selection
# -----------------------------
@app.route("/movie", methods=["GET", "POST"])
def choose_movie():
    current_actor_id = session["current_actor_id"]
    current_actor_name = session["current_actor_name"]
    active_actor = session.get("active_actor", "a")
    path_a = session.get("path_from_a", [])
    path_b = session.get("path_from_b", [])
    target_name = session["target_actor_name"]

    # GET or first time: fetch and store the movie list in session
    if "current_movies" not in session:
        session["current_movies"] = get_movies_for_actor(current_actor_id)

    movies = session["current_movies"]

    if request.method == "POST":
        choice = request.form["choice"]
        
        # Switch active actor
        if choice in ["switch_a", "switch_b"]:
            new_active = "a" if choice == "switch_a" else "b"
            session["active_actor"] = new_active
            # Update current actor to the last in the chosen path
            current_path = path_a if new_active == "a" else path_b
            session["current_actor_name"] = current_path[-1]
            session["current_actor_id"] = get_actor_by_name(current_path[-1])[0]
            session.pop("current_movies", None)
            return redirect(url_for("choose_movie"))
            
        if choice == "shuffle":
            session["shuffle_count"] += 1
            session["current_movies"] = get_movies_for_actor(current_actor_id)
            return redirect(url_for("choose_movie"))
        elif choice == "back":
            current_path = path_a if active_actor == "a" else path_b
            if len(current_path) > 1:
                current_path.pop()  # remove actor
                current_path.pop()  # remove movie
                session["back_count"] += 1
                session["current_actor_name"] = current_path[-1]
                session["current_actor_id"] = get_actor_by_name(current_path[-1])[0]
                session.pop("current_movies", None)
            if active_actor == "a":
                session["path_from_a"] = current_path
            else:
                session["path_from_b"] = current_path
            return redirect(url_for("choose_movie"))
        elif choice == "writein":
            user_input = request.form["writein"].strip()
            full_movies = get_all_movies_for_actor(current_actor_id)
            valid_titles = [title for _, title in full_movies]
            closest = find_closest_match(user_input, valid_titles)
            if closest:
                movie_id, movie_title = full_movies[valid_titles.index(closest)]
                current_path = path_a if active_actor == "a" else path_b
                current_path = rewind_if_loop(current_path, movie_title)
                current_path.append(movie_title)
                if active_actor == "a":
                    session["path_from_a"] = current_path
                else:
                    session["path_from_b"] = current_path
                session["turn_count"] += 1
                session["movie_id"] = movie_id
                return redirect(url_for("choose_actor"))
        else:
            # Numeric selection
            try:
                movie_id, movie_title = movies[int(choice)-1]
                current_path = path_a if active_actor == "a" else path_b
                current_path = rewind_if_loop(current_path, movie_title)
                current_path.append(movie_title)
                if active_actor == "a":
                    session["path_from_a"] = current_path
                else:
                    session["path_from_b"] = current_path
                session["turn_count"] += 1
                session["movie_id"] = movie_id
                session.pop("current_movies", None)
                return redirect(url_for("choose_actor"))
            except:
                pass

    return render_template("movie_vertical.html", movies=movies, actor_name=current_actor_name, path_a=path_a, path_b=path_b, turn_count=session["turn_count"], back_count=session["back_count"], shuffle_count=session["shuffle_count"], target_actor=target_name, active_actor=active_actor)


# -----------------------------
# Actor Selection
# -----------------------------
@app.route("/actor", methods=["GET", "POST"])
def choose_actor():
    movie_id = session["movie_id"]
    active_actor = session.get("active_actor", "a")
    path_a = session.get("path_from_a", [])
    path_b = session.get("path_from_b", [])
    target_name = session["target_actor_name"]

    # Always regenerate costars if missing
    costars = session.get("current_costars")
    if not costars:
        current_path = path_a if active_actor == "a" else path_b
        costars = get_costars_for_movie(movie_id, current_path)
        session["current_costars"] = costars

    if request.method == "POST":
        choice = request.form["choice"]

        # Switch active actor
        if choice in ["switch_a", "switch_b"]:
            new_active = "a" if choice == "switch_a" else "b"
            session["active_actor"] = new_active
            current_path = path_a if new_active == "a" else path_b
            session["current_actor_name"] = current_path[-1]
            session["current_actor_id"] = get_actor_by_name(current_path[-1])[0]
            session.pop("current_costars", None)
            return redirect(url_for("choose_movie"))

        # 🔀 SHUFFLE
        if choice == "shuffle":
            session["shuffle_count"] += 1
            current_path = path_a if active_actor == "a" else path_b
            session["current_costars"] = get_costars_for_movie(movie_id, current_path)
            return redirect(url_for("choose_actor"))

        # ⬅ BACK
        elif choice == "back":
            current_path = path_a if active_actor == "a" else path_b
            current_path.pop()  # remove movie
            session["back_count"] += 1
            if active_actor == "a":
                session["path_from_a"] = current_path
            else:
                session["path_from_b"] = current_path
            session.pop("current_costars", None)
            return redirect(url_for("choose_movie"))

        # ✏ WRITE-IN
        elif choice == "writein":
            user_input = request.form["writein"].strip()
            current_path = path_a if active_actor == "a" else path_b
            full_cast = get_all_costars_for_movie(movie_id, current_path)
            valid_names = [name for _, name in full_cast]
            closest = find_closest_match(user_input, valid_names)

            if closest:
                next_actor_id, next_actor_name = full_cast[valid_names.index(closest)]
                current_path.append(next_actor_name)
                session["turn_count"] += 1
                
                if active_actor == "a":
                    session["path_from_a"] = current_path
                    if next_actor_name.lower() == target_name.lower():
                        valid = validate_path(current_path)
                        session.pop("current_costars", None)
                        return render_template("win_vertical.html", path=current_path, valid=valid, target_actor=target_name)
                else:
                    session["path_from_b"] = current_path
                    if next_actor_name.lower() == session["path_from_a"][0].lower():
                        valid = validate_path(current_path)
                        session.pop("current_costars", None)
                        return render_template("win_vertical.html", path=current_path, valid=valid, target_actor=target_name)

                session["current_actor_id"] = next_actor_id
                session["current_actor_name"] = next_actor_name
                session.pop("current_costars", None)
                session.pop("current_movies", None)
                return redirect(url_for("choose_movie"))

        # 🔢 NUMBERED SELECTION
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(costars):
                    next_actor_id, next_actor_name = costars[index]
                    current_path = path_a if active_actor == "a" else path_b
                    current_path.append(next_actor_name)
                    session["turn_count"] += 1

                    # WIN CHECK
                    if active_actor == "a":
                        session["path_from_a"] = current_path
                        if next_actor_name.lower() == target_name.lower():
                            valid = validate_path(current_path)
                            session.pop("current_costars", None)
                            return render_template("win_vertical.html", path=current_path, valid=valid, target_actor=target_name)
                    else:
                        session["path_from_b"] = current_path
                        if next_actor_name.lower() == session["path_from_a"][0].lower():
                            valid = validate_path(current_path)
                            session.pop("current_costars", None)
                            return render_template("win_vertical.html", path=current_path, valid=valid, target_actor=target_name)

                    session["current_actor_id"] = next_actor_id
                    session["current_actor_name"] = next_actor_name
                    session.pop("current_costars", None)
                    session.pop("current_movies", None)
                    return redirect(url_for("choose_movie"))

            except:
                pass

    current_path = path_a if active_actor == "a" else path_b
    return render_template(
        "actor_vertical.html",
        costars=session["current_costars"],
        movie_title=current_path[-1],
        path_a=path_a,
        path_b=path_b,
        turn_count=session["turn_count"],
        back_count=session["back_count"],
        shuffle_count=session["shuffle_count"],
        target_actor=target_name,
        active_actor=active_actor
    )


@app.route("/play", methods=["GET", "POST"])
def play_game():
    actor_a = request.args.get("actorA") or request.form.get("actorA")
    actor_b = request.args.get("actorB") or request.form.get("actorB")
    if not actor_a or not actor_b:
        return "Missing actor names", 400

    a1 = get_actor_by_name(actor_a)
    a2 = get_actor_by_name(actor_b)
    if not a1 or not a2:
        return f"Actor(s) not found: {actor_a}, {actor_b}", 404

    session["current_actor_id"], session["current_actor_name"] = a1
    session["target_actor_name"] = a2[1]
    session["path_from_a"] = [a1[1]]
    session["path_from_b"] = [a2[1]]
    session["active_actor"] = "a"
    session["turn_count"] = 0
    session["back_count"] = 0
    session["shuffle_count"] = 0
    session.pop("current_movies", None)
    session.pop("current_costars", None)

    # Test logic: redirect to movie selection
    return redirect(url_for("choose_movie"))


if __name__ == "__main__":
    app.run(debug=True)
