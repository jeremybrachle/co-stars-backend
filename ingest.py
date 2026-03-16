import json

from tmdb_api import (
    get_actors_for_movie,
    get_movie_content_rating,
    get_movie_details,
    get_movie_id_by_title,
    get_person_details,
)
from db_helper import (
    insert_movie,
    insert_actor,
    insert_relationship,
    movie_exists,
    movie_exists_by_title,
)


def _serialize_genres(movie_payload):
    genres = [genre.get("name") for genre in movie_payload.get("genres", []) if genre.get("name")]
    return json.dumps(genres) if genres else None


def ingest_movie_by_id(movie_id, refresh_existing=False):
    if movie_exists(movie_id) and not refresh_existing:
        print(f"Movie ID {movie_id} already exists. Skipping API call.")
        return "skipped"

    movie = get_movie_details(movie_id)

    try:
        content_rating = get_movie_content_rating(movie_id)
    except Exception as exc:
        print(f"Warning: failed to fetch content rating for movie ID {movie_id}: {exc}")
        content_rating = None

    insert_movie(
        movie["id"],
        movie["title"],
        movie.get("release_date"),
        genres_json=_serialize_genres(movie),
        overview=movie.get("overview"),
        poster_path=movie.get("poster_path"),
        original_language=movie.get("original_language"),
        content_rating=content_rating,
    )

    actors = get_actors_for_movie(movie_id)
    for actor in actors:
        try:
            person_details = get_person_details(actor["id"])
        except Exception as exc:
            print(
                f"Warning: failed to enrich actor {actor['name']} ({actor['id']}): {exc}"
            )
            person_details = {}

        insert_actor(
            actor["id"],
            person_details.get("name") or actor["name"],
            actor.get("popularity"),
            birthday=person_details.get("birthday"),
            deathday=person_details.get("deathday"),
            place_of_birth=person_details.get("place_of_birth"),
            biography=person_details.get("biography"),
            profile_path=person_details.get("profile_path"),
            known_for_department=person_details.get("known_for_department"),
        )
        insert_relationship(movie["id"], actor["id"])

    action = "Refreshed" if refresh_existing else "Inserted"
    print(f"{action} movie '{movie['title']}' and {len(actors)} actors.")
    return "refreshed" if refresh_existing else "inserted"


def ingest_movie_by_title(title, refresh_existing=False):
    if movie_exists_by_title(title) and not refresh_existing:
        print(f"Movie '{title}' already exists. Skipping API call.")
        return "skipped"

    movie_id = get_movie_id_by_title(title)
    if not movie_id:
        print(f"Movie '{title}' not found on TMDB.")
        return "not_found"

    return ingest_movie_by_id(movie_id, refresh_existing=refresh_existing)
