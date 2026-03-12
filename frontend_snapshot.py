from datetime import datetime, timezone
from pathlib import Path

from db_helper import get_all_actors, get_all_movie_actor_links, get_all_movies
from db import DB_FILE
from project_version import get_project_version


ROOT = Path(__file__).resolve().parent
LEVELS_FILE = ROOT / "levels.json"


def _isoformat_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _get_source_updated_at():
    timestamps = []

    db_path = ROOT / DB_FILE
    if db_path.exists():
        timestamps.append(db_path.stat().st_mtime)

    if LEVELS_FILE.exists():
        timestamps.append(LEVELS_FILE.stat().st_mtime)

    if not timestamps:
        return datetime.now(timezone.utc).isoformat()

    return _isoformat_from_timestamp(max(timestamps))


def _serialize_actors(actor_rows):
    return [
        {
            "id": actor_id,
            "name": name,
            "popularity": popularity,
        }
        for actor_id, name, popularity in actor_rows
    ]


def _serialize_movies(movie_rows):
    return [
        {
            "id": movie_id,
            "title": title,
            "release_date": release_date,
        }
        for movie_id, title, release_date in movie_rows
    ]


def _serialize_links(link_rows):
    return [
        {
            "movie_id": movie_id,
            "actor_id": actor_id,
        }
        for movie_id, actor_id in link_rows
    ]


def _build_adjacency(link_rows):
    actor_to_movies = {}
    movie_to_actors = {}

    for movie_id, actor_id in link_rows:
        actor_key = str(actor_id)
        movie_key = str(movie_id)
        actor_to_movies.setdefault(actor_key, []).append(movie_id)
        movie_to_actors.setdefault(movie_key, []).append(actor_id)

    return actor_to_movies, movie_to_actors


def build_frontend_snapshot(levels):
    actor_rows = get_all_actors()
    movie_rows = get_all_movies()
    link_rows = get_all_movie_actor_links()
    actor_to_movies, movie_to_actors = _build_adjacency(link_rows)

    return {
        "meta": {
            "version": get_project_version(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "actor_count": len(actor_rows),
            "movie_count": len(movie_rows),
            "relationship_count": len(link_rows),
            "level_count": len(levels),
        },
        "actors": _serialize_actors(actor_rows),
        "movies": _serialize_movies(movie_rows),
        "movie_actors": _serialize_links(link_rows),
        "adjacency": {
            "actor_to_movies": actor_to_movies,
            "movie_to_actors": movie_to_actors,
        },
        "levels": list(levels),
    }


def build_frontend_manifest(levels):
    actor_rows = get_all_actors()
    movie_rows = get_all_movies()
    link_rows = get_all_movie_actor_links()

    return {
        "version": get_project_version(),
        "source_updated_at": _get_source_updated_at(),
        "actor_count": len(actor_rows),
        "movie_count": len(movie_rows),
        "relationship_count": len(link_rows),
        "level_count": len(levels),
        "recommended_refresh_interval_hours": 168,
        "snapshot_endpoint": "/api/export/frontend-snapshot",
    }