import json
from flask import Flask, request, jsonify
from versus_game import (
    get_actor_by_name, get_movies_for_actor, get_costars_for_movie,
    get_all_movies_for_actor, get_all_costars_for_movie,
    find_closest_match, rewind_if_loop, validate_path
)
from db_helper import movie_exists

app = Flask(__name__)

# -----------------------------
# Start Page
# -----------------------------
with open("levels.json", "r") as f:
    LEVELS = json.load(f)


# API: Get all levels
@app.route("/api/levels", methods=["GET"])
def api_levels():
    return jsonify(LEVELS)


# -----------------------------
# Movie Selection
# -----------------------------

# API: Get actor info by name
@app.route("/api/actor/<name>", methods=["GET"])
def api_actor_by_name(name):
    actor = get_actor_by_name(name)
    if not actor:
        return jsonify({"error": "Actor not found"}), 404
    return jsonify({"id": actor[0], "name": actor[1]})


# Helper: Get actor by id
def get_actor_by_id(actor_id):
    from versus_game import run_query
    row = run_query("SELECT id, name FROM actors WHERE id = ?", (actor_id,))
    return row[0] if row else None

# API: Get movies for actor by actor_id
@app.route("/api/actor/<int:actor_id>/movies", methods=["GET"])
def api_movies_for_actor(actor_id):
    actor = get_actor_by_id(actor_id)
    if not actor:
        return jsonify({"error": "Actor not found"}), 404
    movies = get_all_movies_for_actor(actor_id)
    return jsonify([{"id": m[0], "title": m[1]} for m in movies])


# API: Get costars for movie by movie_id
@app.route("/api/movie/<int:movie_id>/costars", methods=["GET"])
def api_costars_for_movie(movie_id):
    exclude_names = request.args.getlist("exclude")
    if not movie_exists(movie_id):
        return jsonify({"error": "Movie not found"}), 404
    costars = get_all_costars_for_movie(movie_id, exclude_names)
    return jsonify([{"id": c[0], "name": c[1]} for c in costars])

# API: Validate a path (POST)
@app.route("/api/path/validate", methods=["POST"])
def api_validate_path():
    data = request.get_json()
    path = data.get("path")
    if not path or not isinstance(path, list):
        return jsonify({"error": "Missing or invalid path"}), 400
    valid = validate_path(path)
    return jsonify({"valid": valid})








if __name__ == "__main__":
    app.run(debug=True)
