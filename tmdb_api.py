import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def tmdb_get(endpoint, params=None):
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Accept": "application/json"
    }
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

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
