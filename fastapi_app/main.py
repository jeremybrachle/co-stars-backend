from enum import Enum
import os
from fastapi import FastAPI, HTTPException, Query, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List, Optional
from versus_game import (
    get_actor_by_name as vg_get_actor_by_name,
    get_actor_details_by_name as vg_get_actor_details_by_name,
    get_movie_by_title as vg_get_movie_by_title,
)
from path_utils import (
    build_path_hint,
    generate_typed_path,
    normalize_path,
    pretty_print_path,
    serialize_typed_path,
    validate_named_path,
)
from db_helper import (
    actor_exists,
    get_actors_in_movie,
    get_all_actors,
    get_all_movies,
    get_movies_for_actor as db_get_movies_for_actor,
    movie_exists,
)
from frontend_snapshot import build_frontend_manifest, build_frontend_snapshot
from project_version import get_project_version
import json

load_dotenv()


def get_allowed_origins():
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app = FastAPI(
    title="Co-Stars API",
    description="A FastAPI backend for actor/movie game. All endpoints are documented and testable via the Swagger UI.",
    version=get_project_version(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LEVELS_EXAMPLE = [
    {
        "actor_a": "Matt Damon",
        "actor_b": "George Clooney",
        "stars": 3,
    }
]

ACTORS_EXAMPLE = [
    {
        "id": 1461,
        "name": "George Clooney",
        "popularity": 33.1,
    },
    {
        "id": 1892,
        "name": "Matt Damon",
        "popularity": 51.25,
    },
]

MOVIES_EXAMPLE = [
    {
        "id": 161,
        "title": "Ocean's Eleven",
        "release_date": "2001-12-07",
    },
    {
        "id": 1422,
        "title": "The Departed",
        "release_date": "2006-10-04",
    },
]

FRONTEND_SNAPSHOT_EXAMPLE = {
    "meta": {
        "version": "2.0.0",
        "exported_at": "2026-03-11T00:00:00+00:00",
        "actor_count": 2,
        "movie_count": 1,
        "relationship_count": 2,
        "level_count": 1,
    },
    "actors": ACTORS_EXAMPLE,
    "movies": [MOVIES_EXAMPLE[0]],
    "movie_actors": [
        {"movie_id": 161, "actor_id": 1461},
        {"movie_id": 161, "actor_id": 1892},
    ],
    "adjacency": {
        "actor_to_movies": {
            "1461": [161],
            "1892": [161],
        },
        "movie_to_actors": {
            "161": [1461, 1892],
        },
    },
    "levels": LEVELS_EXAMPLE,
}

FRONTEND_MANIFEST_EXAMPLE = {
    "version": "2.0.0",
    "source_updated_at": "2026-03-11T00:00:00+00:00",
    "actor_count": 2,
    "movie_count": 1,
    "relationship_count": 2,
    "level_count": 1,
    "recommended_refresh_interval_hours": 168,
    "snapshot_endpoint": "/api/export/frontend-snapshot",
}

HEALTH_EXAMPLE = {
    "status": "ok",
    "version": "2.0.0",
}

MOVIE_SUGGESTIONS_EXAMPLE = [
    {
        "id": 161,
        "title": "Ocean's Eleven",
        "release_date": "2001-12-07",
        "path_hint": {
            "reachable": True,
            "steps_to_target": 1,
            "path": [
                {"id": 161, "type": "movie", "label": "Ocean's Eleven"},
                {"id": 1892, "type": "actor", "label": "Matt Damon"},
            ],
        },
    },
    {
        "id": 10589,
        "title": "The Perfect Storm",
        "release_date": "2000-06-30",
        "path_hint": {
            "reachable": True,
            "steps_to_target": 3,
            "path": [
                {"id": 10589, "type": "movie", "label": "The Perfect Storm"},
                {"id": 13240, "type": "actor", "label": "Mark Wahlberg"},
                {"id": 1422, "type": "movie", "label": "The Departed"},
                {"id": 1892, "type": "actor", "label": "Matt Damon"},
            ],
        },
    },
]

ACTOR_SUGGESTIONS_EXAMPLE = [
    {
        "id": 1892,
        "name": "Matt Damon",
        "popularity": 51.25,
        "path_hint": {
            "reachable": True,
            "steps_to_target": 0,
            "path": [
                {"id": 1892, "type": "actor", "label": "Matt Damon"},
            ],
        },
    },
    {
        "id": 13240,
        "name": "Mark Wahlberg",
        "popularity": 28.0,
        "path_hint": {
            "reachable": True,
            "steps_to_target": 2,
            "path": [
                {"id": 13240, "type": "actor", "label": "Mark Wahlberg"},
                {"id": 1422, "type": "movie", "label": "The Departed"},
                {"id": 1892, "type": "actor", "label": "Matt Damon"},
            ],
        },
    },
]

PATH_GENERATE_REQUEST_EXAMPLE = {
    "a": {"type": "actor", "value": "George Clooney"},
    "b": {"type": "actor", "value": "Matt Damon"},
}

PATH_GENERATE_RESPONSE_EXAMPLE = {
    "path": "George Clooney -> Ocean's Eleven -> Matt Damon",
    "nodes": [
        {"id": 1461, "type": "actor", "label": "George Clooney"},
        {"id": 161, "type": "movie", "label": "Ocean's Eleven"},
        {"id": 1892, "type": "actor", "label": "Matt Damon"},
    ],
    "steps": 2,
    "reason": None,
}

PATH_VALIDATE_REQUEST_EXAMPLE = {
    "start_type": "actor",
    "path": ["George Clooney", "Ocean's Eleven", "Matt Damon"],
}

PATH_VALIDATE_RESPONSE_EXAMPLE = {
    "valid": True,
}

PATH_NORMALIZE_REQUEST_EXAMPLE = {
    "start_type": "actor",
    "path": ["George Clooney", "Ocean's Eleven", "Brad Pitt", "The Mexican", "George Clooney"],
}

PATH_NORMALIZE_RESPONSE_EXAMPLE = {
    "original_path": ["George Clooney", "Ocean's Eleven", "Brad Pitt", "The Mexican", "George Clooney"],
    "normalized_path": ["George Clooney"],
    "loop_detected": True,
    "rewind_to_index": 0,
    "repeated_node": {"type": "actor", "label": "George Clooney"},
    "removed_segment": [
        {"type": "movie", "label": "Ocean's Eleven"},
        {"type": "actor", "label": "Brad Pitt"},
        {"type": "movie", "label": "The Mexican"},
    ],
}

NOT_FOUND_EXAMPLE = {"error": "Actor not found"}
MOVIE_NOT_FOUND_EXAMPLE = {"error": "Movie not found"}

class PathNode(BaseModel):
    type: str = Field(..., examples=["actor"], description="Node type: actor or movie.")
    value: str = Field(..., examples=["George Clooney"], description="Actor name or movie title.")

class PathGenRequest(BaseModel):
    a: PathNode
    b: PathNode


class NodeType(str, Enum):
    actor = "actor"
    movie = "movie"


class NodeSummary(BaseModel):
    id: int
    type: NodeType
    label: str


class PathLabelNode(BaseModel):
    type: NodeType
    label: str


class PathHint(BaseModel):
    reachable: bool
    steps_to_target: Optional[int] = None
    path: List[NodeSummary] = Field(default_factory=list)


class PathGenerateResponse(BaseModel):
    path: str
    nodes: List[NodeSummary]
    steps: Optional[int] = None
    reason: Optional[str] = None

@app.post(
    "/api/path/generate",
    response_model=PathGenerateResponse,
    summary="Generate a path between any two nodes",
    tags=["Pathfinding"],
    responses={
        200: {
            "description": "Structured shortest path response.",
            "content": {"application/json": {"example": PATH_GENERATE_RESPONSE_EXAMPLE}},
        }
    },
)
def generate_path_endpoint(
    req: PathGenRequest = Body(
        ...,
        openapi_examples={
            "actorToActor": {
                "summary": "Actor to actor path",
                "value": PATH_GENERATE_REQUEST_EXAMPLE,
            },
            "actorToMovie": {
                "summary": "Actor to movie path",
                "value": {
                    "a": {"type": "actor", "value": "George Clooney"},
                    "b": {"type": "movie", "value": "Ocean's Eleven"},
                },
            },
        },
    )
):
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
            return {"path": "-1", "nodes": [], "steps": None, "reason": "Invalid actor/movie name"}

        typed_path = generate_typed_path(id_a, type_a, id_b, type_b)
        if typed_path == -1:
            return {"path": "-1", "nodes": [], "steps": None, "reason": "No path found"}

        node_ids = [node_id for node_id, _node_type in typed_path]
        return {
            "path": pretty_print_path(node_ids, start_type=type_a),
            "nodes": serialize_typed_path(typed_path),
            "steps": len(typed_path) - 1,
            "reason": None,
        }
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
    popularity: Optional[float] = None


class ActorSuggestion(Actor):
    path_hint: Optional[PathHint] = None

class Movie(BaseModel):
    id: int
    title: str
    release_date: Optional[str] = None


class MovieSuggestion(Movie):
    path_hint: Optional[PathHint] = None


class MovieActorLink(BaseModel):
    movie_id: int
    actor_id: int


class FrontendSnapshotMeta(BaseModel):
    version: str
    exported_at: str
    actor_count: int
    movie_count: int
    relationship_count: int
    level_count: int


class FrontendAdjacency(BaseModel):
    actor_to_movies: dict[str, List[int]] = Field(default_factory=dict)
    movie_to_actors: dict[str, List[int]] = Field(default_factory=dict)


class FrontendSnapshot(BaseModel):
    meta: FrontendSnapshotMeta
    actors: List[Actor]
    movies: List[Movie]
    movie_actors: List[MovieActorLink]
    adjacency: FrontendAdjacency
    levels: List[Level]


class FrontendManifest(BaseModel):
    version: str
    source_updated_at: str
    actor_count: int
    movie_count: int
    relationship_count: int
    level_count: int
    recommended_refresh_interval_hours: int
    snapshot_endpoint: str


class HealthResponse(BaseModel):
    status: str
    version: str

class PathValidateRequest(BaseModel):
    start_type: NodeType = NodeType.actor
    path: List[str]

class PathValidateResponse(BaseModel):
    valid: bool
    message: Optional[str] = None


class PathNormalizeRequest(BaseModel):
    start_type: NodeType = NodeType.actor
    path: List[str]


class PathNormalizeResponse(BaseModel):
    original_path: List[str]
    normalized_path: List[str]
    loop_detected: bool
    rewind_to_index: Optional[int] = None
    repeated_node: Optional[PathLabelNode] = None
    removed_segment: List[PathLabelNode] = Field(default_factory=list)


def resolve_target_node(target_type: Optional[NodeType], target_id: Optional[int]):
    if target_type is None and target_id is None:
        return None
    if target_type is None or target_id is None:
        raise HTTPException(status_code=400, detail="target_type and target_id must be provided together")

    exists = actor_exists(target_id) if target_type == NodeType.actor else movie_exists(target_id)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Target {target_type.value} not found")

    return (target_type.value, target_id)


def serialize_actor_rows(actor_rows, target_node=None):
    serialized = []
    for actor_id, name, popularity in actor_rows:
        actor = {
            "id": actor_id,
            "name": name,
            "popularity": popularity,
        }
        if target_node is not None:
            target_type, target_id = target_node
            actor["path_hint"] = build_path_hint(actor_id, "actor", target_id, target_type)
        serialized.append(actor)
    return serialized


def serialize_movie_rows(movie_rows, target_node=None):
    serialized = []
    for movie_id, title, release_date in movie_rows:
        movie = {
            "id": movie_id,
            "title": title,
            "release_date": release_date,
        }
        if target_node is not None:
            target_type, target_id = target_node
            movie["path_hint"] = build_path_hint(movie_id, "movie", target_id, target_type)
        serialized.append(movie)
    return serialized


# --- Endpoints ---
@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
    responses={
        200: {
            "description": "Basic API liveness response.",
            "content": {"application/json": {"example": HEALTH_EXAMPLE}},
        }
    },
)
def health_check():
    return {"status": "ok", "version": get_project_version()}


@app.get(
    "/api/levels",
    response_model=List[Level],
    summary="Get all levels",
    tags=["Levels"],
    responses={
        200: {
            "description": "Predefined challenge levels.",
            "content": {"application/json": {"example": LEVELS_EXAMPLE}},
        }
    },
)
def get_levels():
    """Returns all available levels."""
    return LEVELS


@app.get(
    "/api/actors",
    response_model=List[Actor],
    summary="Get all actors",
    tags=["Catalog"],
    responses={
        200: {
            "description": "Full actor catalog.",
            "content": {"application/json": {"example": ACTORS_EXAMPLE}},
        }
    },
)
def get_actors():
    """Returns every actor in the database with all actor attributes."""
    return serialize_actor_rows(get_all_actors())


@app.get(
    "/api/movies",
    response_model=List[Movie],
    summary="Get all movies",
    tags=["Catalog"],
    responses={
        200: {
            "description": "Full movie catalog.",
            "content": {"application/json": {"example": MOVIES_EXAMPLE}},
        }
    },
)
def get_movies():
    """Returns every movie in the database with all movie attributes."""
    return serialize_movie_rows(get_all_movies())


@app.get(
    "/api/export/frontend-manifest",
    response_model=FrontendManifest,
    summary="Get lightweight frontend refresh metadata",
    tags=["Export"],
    responses={
        200: {
            "description": "Snapshot freshness metadata for frontend refresh checks.",
            "content": {"application/json": {"example": FRONTEND_MANIFEST_EXAMPLE}},
        }
    },
)
def export_frontend_manifest():
    """Returns cheap metadata the frontend can check before pulling the full snapshot.

    TODO(frontend-refactor): Use this endpoint as the default freshness check before downloading a new snapshot.
    """
    return build_frontend_manifest(LEVELS)


@app.get(
    "/api/export/frontend-snapshot",
    response_model=FrontendSnapshot,
    summary="Export the full graph for frontend-local gameplay",
    tags=["Export"],
    responses={
        200: {
            "description": "Full actor/movie graph plus adjacency lists for frontend-local state.",
            "content": {"application/json": {"example": FRONTEND_SNAPSHOT_EXAMPLE}},
        }
    },
)
def export_frontend_snapshot():
    """Returns a complete snapshot the frontend can cache and query locally.

    TODO(frontend-refactor): Make this export contract the long-term frontend sync surface.
    TODO(frontend-refactor): Move legacy gameplay-specific lookup endpoints behind a compatibility namespace once the frontend owns graph traversal.
    """
    return build_frontend_snapshot(LEVELS)

@app.get(
    "/api/actor/{name}",
    response_model=Actor,
    responses={
        200: {"content": {"application/json": {"example": ACTORS_EXAMPLE[1]}}},
        404: {"model": dict, "content": {"application/json": {"example": NOT_FOUND_EXAMPLE}}},
    },
    summary="Get actor by name",
    tags=["Actors"],
)
def get_actor_by_name(
    name: str = Path(..., description="Actor name to resolve.", examples=["Matt Damon"])
):
    """Returns actor details by name."""
    actor = vg_get_actor_details_by_name(name)
    if not actor:
        return JSONResponse(status_code=404, content={"error": "Actor not found"})
    return {"id": actor[0], "name": actor[1], "popularity": actor[2]}

@app.get(
    "/api/actor/{actor_id}/movies",
    response_model=List[MovieSuggestion],
    summary="Get movies for actor",
    tags=["Actors"],
    responses={
        200: {"content": {"application/json": {"example": MOVIE_SUGGESTIONS_EXAMPLE}}},
        404: {"model": dict, "content": {"application/json": {"example": NOT_FOUND_EXAMPLE}}},
    },
)
def get_movies_for_actor(
    actor_id: int = Path(..., description="Actor id whose movies should be returned.", examples=[1461]),
    target_type: Optional[NodeType] = Query(
        None,
        description="Optional target node type used to attach shortest-path hint metadata.",
        examples=["actor"],
    ),
    target_id: Optional[int] = Query(
        None,
        description="Optional target node id used to attach shortest-path hint metadata.",
        examples=[1892],
    ),
):
    """Returns all movies for a given actor ID with optional target-aware path hints."""
    if not actor_exists(actor_id):
        return JSONResponse(status_code=404, content={"error": "Actor not found"})

    target_node = resolve_target_node(target_type, target_id)
    movies = db_get_movies_for_actor(actor_id)
    return serialize_movie_rows(movies, target_node=target_node)


@app.get(
    "/api/movie/{movie_id}/costars",
    response_model=List[ActorSuggestion],
    responses={
        200: {"content": {"application/json": {"example": ACTOR_SUGGESTIONS_EXAMPLE}}},
        404: {"model": dict, "content": {"application/json": {"example": MOVIE_NOT_FOUND_EXAMPLE}}},
    },
    summary="Get costars for a movie",
    tags=["Movies"],
)
def get_costars_for_movie(
    movie_id: int = Path(..., description="Movie id whose actors should be returned.", examples=[161]),
    exclude: Optional[List[str]] = Query(
        None,
        description="Optional repeated actor names to exclude from the returned list.",
        examples=[["George Clooney"]],
    ),
    target_type: Optional[NodeType] = Query(
        None,
        description="Optional target node type used to attach shortest-path hint metadata.",
        examples=["actor"],
    ),
    target_id: Optional[int] = Query(
        None,
        description="Optional target node id used to attach shortest-path hint metadata.",
        examples=[1892],
    ),
):
    """Returns all costars for a given movie ID with optional target-aware path hints."""
    if not movie_exists(movie_id):
        return JSONResponse(status_code=404, content={"error": "Movie not found"})

    target_node = resolve_target_node(target_type, target_id)
    excluded_names = exclude or []
    costars = get_actors_in_movie(movie_id, excluded_names)
    return serialize_actor_rows(costars, target_node=target_node)

@app.post(
    "/api/path/validate",
    response_model=PathValidateResponse,
    response_model_exclude_none=True,
    summary="Validate a path",
    tags=["Gameplay"],
    responses={
        200: {"content": {"application/json": {"example": PATH_VALIDATE_RESPONSE_EXAMPLE}}},
    },
)
def validate_path(
    req: PathValidateRequest = Body(
        ...,
        openapi_examples={
            "validPath": {
                "summary": "Valid alternating path",
                "value": PATH_VALIDATE_REQUEST_EXAMPLE,
            },
            "invalidPath": {
                "summary": "Invalid alternating path",
                "value": {
                    "start_type": "actor",
                    "path": ["George Clooney", "Ocean's Eleven", "Definitely Not In This Movie"],
                },
            },
            "movieStartPath": {
                "summary": "Movie-first alternating path",
                "value": {
                    "start_type": "movie",
                    "path": ["Ocean's Eleven", "Matt Damon", "The Departed"],
                },
            },
        },
    )
):
    """Validates an alternating path for either actor-first or movie-first gameplay."""
    if not req.path or not isinstance(req.path, list):
        return {"valid": False, "message": "Missing or invalid path"}
    valid = validate_named_path(req.path, start_type=req.start_type.value)
    # TODO(frontend-refactor): Move normal gameplay path validation to the frontend once the graph is cached client-side.
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


@app.post(
    "/api/path/normalize",
    response_model=PathNormalizeResponse,
    summary="Normalize repeated nodes in a path",
    tags=["Gameplay"],
    responses={
        200: {"content": {"application/json": {"example": PATH_NORMALIZE_RESPONSE_EXAMPLE}}},
    },
)
def normalize_path_endpoint(
    req: PathNormalizeRequest = Body(
        ...,
        openapi_examples={
            "actorStartLoop": {
                "summary": "Actor-first loop rewind",
                "value": PATH_NORMALIZE_REQUEST_EXAMPLE,
            },
            "movieStartLoop": {
                "summary": "Movie-first loop rewind",
                "value": {
                    "start_type": "movie",
                    "path": ["Ocean's Eleven", "Matt Damon", "The Departed", "Mark Wahlberg", "Ocean's Eleven"],
                },
            },
        },
    )
):
    """Collapses repeated actors or movies by rewinding the path to the earlier occurrence."""
    if not req.path or not isinstance(req.path, list):
        raise HTTPException(status_code=400, detail="Missing or invalid path")

    normalized = normalize_path(req.path, start_type=req.start_type.value)
    return normalized


# --- Notes ---
# - All endpoints are visible and testable at /docs
# - Sample payload for POST /api/path/validate:
#   {
#     "path": [123, 456, 789]
#   }
# - All data is now served from your SQLite database.
