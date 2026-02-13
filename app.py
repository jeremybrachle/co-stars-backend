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
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        actor1 = request.form["actor1"].strip()
        actor2 = request.form["actor2"].strip()

        a1 = get_actor_by_name(actor1)
        a2 = get_actor_by_name(actor2)

        if not a1 or not a2:
            return render_template("index.html", error="Actor(s) not found")

        session["current_actor_id"], session["current_actor_name"] = a1
        session["target_actor_name"] = a2[1]
        session["path"] = [a1[1]]
        session["turn_count"] = 0
        session["back_count"] = 0
        session["shuffle_count"] = 0

        return redirect(url_for("choose_movie"))

    return render_template("index.html")


# -----------------------------
# Movie Selection
# -----------------------------
@app.route("/movie", methods=["GET", "POST"])
def choose_movie():
    current_actor_id = session["current_actor_id"]
    current_actor_name = session["current_actor_name"]
    path = session["path"]
    target_name = session["target_actor_name"]

    if request.method == "POST":
        choice = request.form["choice"]
        if choice == "shuffle":
            session["shuffle_count"] += 1
        elif choice == "back":
            if len(path) > 1:
                path.pop()  # remove actor
                path.pop()  # remove movie
                session["back_count"] += 1
                session["current_actor_name"] = path[-1]
                session["current_actor_id"] = get_actor_by_name(path[-1])[0]
            return redirect(url_for("choose_movie"))
        elif choice == "writein":
            user_input = request.form["writein"].strip()
            full_movies = get_all_movies_for_actor(current_actor_id)
            valid_titles = [title for _, title in full_movies]
            closest = find_closest_match(user_input, valid_titles)
            if closest:
                movie_id, movie_title = full_movies[valid_titles.index(closest)]
                path = rewind_if_loop(path, movie_title)
                path.append(movie_title)
                session["path"] = path
                session["turn_count"] += 1
                session["movie_id"] = movie_id
                return redirect(url_for("choose_actor"))
        else:
            # Numeric selection
            movies = get_movies_for_actor(current_actor_id)
            try:
                movie_id, movie_title = movies[int(choice)-1]
                path = rewind_if_loop(path, movie_title)
                path.append(movie_title)
                session["path"] = path
                session["turn_count"] += 1
                session["movie_id"] = movie_id
                return redirect(url_for("choose_actor"))
            except:
                pass  # ignore invalid selection

    movies = get_movies_for_actor(current_actor_id)
    return render_template("movie.html", movies=movies, actor_name=current_actor_name, path=path, turn_count=session["turn_count"], back_count=session["back_count"], shuffle_count=session["shuffle_count"])


# -----------------------------
# Actor Selection
# -----------------------------
@app.route("/actor", methods=["GET", "POST"])
def choose_actor():
    movie_id = session["movie_id"]
    path = session["path"]
    target_name = session["target_actor_name"]

    if request.method == "POST":
        choice = request.form["choice"]
        if choice == "shuffle":
            session["shuffle_count"] += 1
        elif choice == "back":
            path.pop()  # remove movie
            session["path"] = path
            session["back_count"] += 1
            return redirect(url_for("choose_movie"))
        elif choice == "writein":
            user_input = request.form["writein"].strip()
            full_cast = get_all_costars_for_movie(movie_id, path)
            valid_names = [name for _, name in full_cast]
            closest = find_closest_match(user_input, valid_names)
            if closest:
                next_actor_id, next_actor_name = full_cast[valid_names.index(closest)]
                path.append(next_actor_name)
                session["path"] = path
                session["turn_count"] += 1
                if next_actor_name.lower() == target_name.lower():
                    valid = validate_path(path)
                    return render_template("win.html", path=path, valid=valid)
                session["current_actor_id"] = next_actor_id
                session["current_actor_name"] = next_actor_name
                return redirect(url_for("choose_movie"))
        else:
            # Numeric selection
            costars = get_costars_for_movie(movie_id, path)
            try:
                next_actor_id, next_actor_name = costars[int(choice)-1]
                path.append(next_actor_name)
                session["path"] = path
                session["turn_count"] += 1
                if next_actor_name.lower() == target_name.lower():
                    valid = validate_path(path)
                    return render_template("win.html", path=path, valid=valid)
                session["current_actor_id"] = next_actor_id
                session["current_actor_name"] = next_actor_name
                return redirect(url_for("choose_movie"))
            except:
                pass

    costars = get_costars_for_movie(movie_id, path)
    return render_template("actor.html", costars=costars, movie_title=path[-1], path=path, turn_count=session["turn_count"], back_count=session["back_count"], shuffle_count=session["shuffle_count"])


if __name__ == "__main__":
    app.run(debug=True)
