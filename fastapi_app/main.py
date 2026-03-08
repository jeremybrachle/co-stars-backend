


import sqlite3
from fastapi import FastAPI, Query, Request, Response, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from versus_game import (
    get_actor_by_name as vg_get_actor_by_name,
    get_movie_by_title as vg_get_movie_by_title,
    get_all_movies_for_actor,
    get_all_costars_for_movie,
    validate_path as vg_validate_path
)
from path_utils import generate_path
from db_helper import movie_exists
import json

app = FastAPI(
    title="Co-Stars API",
    description="A FastAPI backend for actor/movie game. All endpoints are documented and testable via the Swagger UI.",
    version="2.0.0",
)

# --- Path Generation Endpoint ---
from fastapi import Body
from pydantic import BaseModel

class PathNode(BaseModel):
    type: str  # "actor" or "movie"
    value: str

class PathGenRequest(BaseModel):
    a: PathNode
    b: PathNode

@app.post("/api/path/generate", summary="Generate a path between any two nodes", tags=["Pathfinding"])
def generate_path_endpoint(req: PathGenRequest = Body(...)):
    """
    Generate a path between any two nodes (actor or movie).
    Input: {"a": {"type": "actor"|"movie", "value": str}, "b": {"type": "actor"|"movie", "value": str}}
    Returns the path as a pretty-printed string, or -1 if no path exists.
    """
    try:
        def resolve(node):
            if node.type == "actor":
                actor = vg_get_actor_by_name(node.value)
                return ("actor", actor[0]) if actor else (None, None)
            elif node.type == "movie":
                movie = vg_get_movie_by_title(node.value)
                return ("movie", movie[0]) if movie else (None, None)
            else:
                return (None, None)

        type_a, id_a = resolve(req.a)
        type_b, id_b = resolve(req.b)
        if not type_a or not type_b:
            return {"path": "-1", "reason": "Invalid actor/movie name"}

        from collections import deque
        conn = None
        try:
            conn = sqlite3.connect("movies.db")
            cursor = conn.cursor()
            # BFS: node = (id, type, path_so_far)
            queue = deque()
            visited = set()
            queue.append((id_a, type_a, [(id_a, type_a)]))
            visited.add((id_a, type_a))
            while queue:
                curr_id, curr_type, path = queue.popleft()
                if (curr_id, curr_type) == (id_b, type_b):
                    # Convert path to pretty string
                    ids = [x[0] for x in path]
                    from path_utils import pretty_print_path
                    return {"path": pretty_print_path(ids, start_type=type_a)}
                if curr_type == "actor":
                    # Expand to movies
                    cursor.execute("SELECT movie_id FROM movie_actors WHERE actor_id = ?", (curr_id,))
                    for (movie_id,) in cursor.fetchall():
                        if (movie_id, "movie") not in visited:
                            visited.add((movie_id, "movie"))
                            queue.append((movie_id, "movie", path + [(movie_id, "movie")]))
                elif curr_type == "movie":
                    # Expand to actors
                    cursor.execute("SELECT actor_id FROM movie_actors WHERE movie_id = ?", (curr_id,))
                    for (actor_id,) in cursor.fetchall():
                        if (actor_id, "actor") not in visited:
                            visited.add((actor_id, "actor"))
                            queue.append((actor_id, "actor", path + [(actor_id, "actor")]))
            return {"path": "-1"}
        finally:
            if conn:
                conn.close()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- Load levels from file (as in Flask) ---
with open("levels.json", "r") as f:
    LEVELS = json.load(f)

# --- Pydantic Models ---
class Level(BaseModel):
    actor_a: str
    actor_b: str
    stars: int

class Actor(BaseModel):
    id: int
    name: str

class Movie(BaseModel):
    id: int
    title: str

class PathValidateRequest(BaseModel):
    path: List[str]

class PathValidateResponse(BaseModel):
    valid: bool
    message: Optional[str] = None


# --- Endpoints ---
@app.get("/api/levels", response_model=List[Level], summary="Get all levels", tags=["Levels"])
def get_levels():
    """Returns all available levels."""
    return LEVELS

@app.get("/api/actor/{name}", response_model=Actor, responses={404: {"model": dict}}, summary="Get actor by name", tags=["Actors"])
def get_actor_by_name(name: str):
    """Returns actor details by name."""
    actor = vg_get_actor_by_name(name)
    if not actor:
        return JSONResponse(status_code=404, content={"error": "Actor not found"})
    return {"id": actor[0], "name": actor[1]}

@app.get("/api/actor/{actor_id}/movies", response_model=List[Movie], summary="Get movies for actor", tags=["Actors"])
def get_movies_for_actor(actor_id: int):
    """Returns movies for a given actor ID."""
    movies = get_all_movies_for_actor(actor_id)
    return [{"id": m[0], "title": m[1]} for m in movies]

@app.get("/api/movie/{movie_id}/costars", response_model=List[Actor], responses={404: {"model": dict}}, summary="Get costars for a movie", tags=["Movies"])
def get_costars_for_movie(movie_id: int, exclude: Optional[List[str]] = Query(None)):
    """Returns costars for a given movie ID."""
    if not movie_exists(movie_id):
        return JSONResponse(status_code=404, content={"error": "Movie not found"})
    costars = get_all_costars_for_movie(movie_id, exclude or [])
    return [{"id": c[0], "name": c[1]} for c in costars]

@app.post("/api/path/validate", response_model=PathValidateResponse, summary="Validate a path", tags=["Gameplay"])
def validate_path(req: PathValidateRequest):
    """Validates a path (actor -> movie -> actor ...). Returns whether the path is valid."""
    if not req.path or not isinstance(req.path, list):
        return {"valid": False, "message": "Missing or invalid path"}
    valid = vg_validate_path(req.path)
    # Always omit 'message' if None or missing
    def strip_message_none(obj):
        if isinstance(obj, tuple):
            valid_val, message = obj
            if message is not None:
                return {"valid": valid_val, "message": message}
            else:
                return {"valid": valid_val}
        if isinstance(obj, dict):
            result = dict(obj)
            if 'message' in result and result['message'] is None:
                del result['message']
            return result
        if isinstance(obj, PathValidateResponse):
            result = obj.dict()
            if 'message' in result and result['message'] is None:
                del result['message']
            return result
        return {"valid": obj}
    return strip_message_none(valid)


# --- Notes ---
# - All endpoints are visible and testable at /docs
# - Sample payload for POST /api/path/validate:
#   {
#     "path": [123, 456, 789]
#   }
# - All data is now served from your SQLite database.
