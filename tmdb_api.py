import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p")
POSTER_IMAGE_SIZE = os.getenv("TMDB_POSTER_SIZE", "w500")
PROFILE_IMAGE_SIZE = os.getenv("TMDB_PROFILE_SIZE", "w500")

def tmdb_get(endpoint, params=None):
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Accept": "application/json"
    }
    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_movie_details(movie_id):
    return tmdb_get(f"/movie/{movie_id}")


def build_tmdb_image_url(image_path, size):
    if not image_path:
        return None

    normalized_path = image_path if image_path.startswith("/") else f"/{image_path}"
    return f"{IMAGE_BASE_URL}/{size}{normalized_path}"


def build_poster_url(poster_path):
    return build_tmdb_image_url(poster_path, POSTER_IMAGE_SIZE)


def build_profile_url(profile_path):
    return build_tmdb_image_url(profile_path, PROFILE_IMAGE_SIZE)


def get_movie_release_dates(movie_id):
    return tmdb_get(f"/movie/{movie_id}/release_dates")


def extract_us_content_rating(release_dates_payload):
    for country_block in release_dates_payload.get("results", []):
        if country_block.get("iso_3166_1") != "US":
            continue

        for release in country_block.get("release_dates", []):
            certification = (release.get("certification") or "").strip()
            if certification:
                return certification

    return None


def get_movie_content_rating(movie_id):
    return extract_us_content_rating(get_movie_release_dates(movie_id))


def get_person_details(person_id):
    return tmdb_get(f"/person/{person_id}")

def get_actors_for_movie(movie_id):
    data = tmdb_get(f"/movie/{movie_id}/credits")
    actors = []
    for person in data.get("cast", []):
        actors.append({
            "id": person["id"],
            "name": person["name"],
            "popularity": person.get("popularity")
        })
    return actors

def get_movie_id_by_title(title):
    data = tmdb_get("/search/movie", params={"query": title})
    results = data.get("results", [])
    if results:
        return results[0]["id"]
    return None

def get_movies_for_actor_tmdb(actor_id):
    data = tmdb_get(f"/person/{actor_id}/movie_credits")
    movies = []
    for movie in data.get("cast", []):
        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "release_date": movie.get("release_date")
        })
    return movies
