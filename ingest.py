from tmdb_api import tmdb_get, get_actors_for_movie, get_movie_id_by_title
from db_helper import insert_movie, insert_actor, insert_relationship, movie_exists, movie_exists_by_title

def ingest_movie_by_id(movie_id):
    # Skip if movie already exists
    if movie_exists(movie_id):
        print(f"Movie ID {movie_id} already exists. Skipping API call.")
        return

    movie = tmdb_get(f"/movie/{movie_id}")
    insert_movie(movie["id"], movie["title"], movie.get("release_date"))

    actors = get_actors_for_movie(movie_id)
    for actor in actors:
        insert_actor(actor["id"], actor["name"], actor.get("popularity"))
        insert_relationship(movie["id"], actor["id"])

    print(f"Inserted movie '{movie['title']}' and {len(actors)} actors.")


def ingest_movie_by_title(title):
    # First, check if the title already exists (case-insensitive)
    if movie_exists_by_title(title):
        print(f"Movie '{title}' already exists. Skipping API call.")
        return

    # Search TMDB for the movie
    movie_id = get_movie_id_by_title(title)
    if not movie_id:
        print(f"Movie '{title}' not found on TMDB.")
        return

    # Ingest by ID
    ingest_movie_by_id(movie_id)
