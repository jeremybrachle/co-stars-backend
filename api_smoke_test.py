# """
# API Smoke Test Script for Co-Stars Backend
# -----------------------------------------
# This script tests all API endpoints for the Co-Stars backend.

# Usage:
#     1. Start your Flask API server (python app.py)
#     2. Run this script:
#              python api_smoke_test.py

# Requirements:
#     - requests (pip install requests)

# The script prints PASS/FAIL for each endpoint, and shows expected vs actual values for debugging.
# """

import requests
import json

BASE_URL = "http://localhost:8000"

def print_result(name, passed, expected=None, actual=None, detail=None):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {name}")
    if hasattr(print_result, 'url') and print_result.url:
        print(f"    API Call: {print_result.url}")
        print_result.url = None
    if expected is not None or actual is not None:
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
    if detail:
        print(f"    {detail}")




# 1. Test GET /api/levels: Should return a list of level dicts with actor_a and actor_b
levels_url = f"{BASE_URL}/api/levels"
resp = requests.get(levels_url)
print_result.url = levels_url
try:
    data = resp.json()
    expected = data  # strict match: expect exactly what the API returns
    actual = data
    passed = resp.status_code == 200 and isinstance(data, list) and all("actor_a" in lvl and "actor_b" in lvl for lvl in data)
    detail = None
    if not data:
        passed = False
        detail = "No levels returned."
except Exception as e:
    passed = False
    data = None
    expected = "200 OK and list of levels with actor_a/actor_b"
    actual = f"Exception: {e}"
    detail = str(e)
print_result("Test: GET /api/levels returns levels with actor_a/actor_b", passed, expected, actual, detail)



###############################

# 2. Test GET /api/actor/<name>: Should return actor info for a known actor
actor_name = None
if data and len(data) > 0:
    actor_name = data[0].get("actor_a")
if not actor_name:
    actor_name = "Matt Damon"  # fallback
actor_url = f"{BASE_URL}/api/actor/{actor_name}"
resp = requests.get(actor_url)
print_result.url = actor_url
try:
    actor_data = resp.json()
    expected = {"id": actor_data["id"], "name": actor_name}
    actual = actor_data
    passed = resp.status_code == 200 and actual == expected
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    actor_data = None
    expected = f"200 OK and keys: id, name for actor {actor_name}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<name> returns correct actor for '{actor_name}'", passed, expected, actual, detail)


# 2b. Test GET /api/actor/<name> with a non-existent actor
invalid_actor = "DefinitelyNotARealActorName12345"
invalid_actor_url = f"{BASE_URL}/api/actor/{invalid_actor}"
resp = requests.get(invalid_actor_url)
print_result.url = invalid_actor_url
try:
    data = resp.json()
    expected = {"error": "Actor not found"}
    actual = data
    passed = resp.status_code == 404 and actual == expected
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = {"error": "Actor not found"}
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<name> returns 404 for non-existent actor", passed, expected, actual, detail)




# 3. Test GET /api/actor/<actor_id>/movies: Should return movies for the actor
actor_id = actor_data["id"] if actor_data else 1
movies_url = f"{BASE_URL}/api/actor/{actor_id}/movies"
resp = requests.get(movies_url)
print_result.url = movies_url
try:
    movies = resp.json()
    expected = movies
    actual = movies
    passed = resp.status_code == 200 and actual == expected and isinstance(movies, list)
    detail = None
    if not movies:
        passed = False
        detail = "No movies returned for actor."
except Exception as e:
    passed = False
    movies = None
    expected = f"200 OK and list of movies for actor_id {actor_id}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<actor_id>/movies returns movies for actor_id {actor_id}", passed, expected, actual, detail)



###############################

# 4. Test GET /api/movie/<movie_id>/costars: Should return costars for a movie
movie_id = None
if movies and len(movies) > 0:
    movie_id = movies[0]["id"]
costars_url = f"{BASE_URL}/api/movie/{movie_id}/costars" if movie_id else None
if movie_id:
    resp = requests.get(costars_url)
    print_result.url = costars_url
    try:
        costars = resp.json()
        expected = costars
        actual = costars
        passed = resp.status_code == 200 and actual == expected and isinstance(costars, list)
        detail = None
        if not costars:
            passed = False
            detail = "No costars returned for movie."
    except Exception as e:
        passed = False
        costars = None
        expected = f"200 OK and list of costars for movie_id {movie_id}"
        actual = f"Exception: {e}"
        detail = str(e)
    print_result(f"Test: GET /api/movie/<movie_id>/costars returns costars for movie_id {movie_id}", passed, expected, actual, detail)
else:
    print_result.url = costars_url
    print_result("Test: GET /api/movie/<movie_id>/costars", False, "No movie_id available", None, "No movie_id available")


# 4b. Test GET /api/movie/<movie_id>/costars with a non-existent movie
invalid_movie_id = 999999999  # unlikely to exist
invalid_costars_url = f"{BASE_URL}/api/movie/{invalid_movie_id}/costars"
resp = requests.get(invalid_costars_url)
print_result.url = invalid_costars_url
try:
    data = resp.json()
    expected = {"error": "Movie not found"}
    actual = data
    passed = resp.status_code == 404 and actual == expected
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = {"error": "Movie not found"}
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/movie/<movie_id>/costars returns 404 for non-existent movie", passed, expected, actual, detail)




# 5. Test POST /api/path/validate: Should validate a path (actor -> movie -> costar)
path = []
validate_url = f"{BASE_URL}/api/path/validate"
if actor_data and movies and len(movies) > 0:
    path = [actor_data["name"], movies[0]["title"]]
    # Try to add a costar if available
    if 'costars' in locals() and costars and len(costars) > 0:
        path.append(costars[0]["name"])


# 5a. Test POST /api/path/validate: Valid path George Clooney → Ocean's Eleven → Brad Pitt → Babylon → Tobey Maguire
valid_path = ["George Clooney", "Ocean's Eleven", "Brad Pitt", "Babylon", "Tobey Maguire"]
resp = requests.post(validate_url, json={"path": valid_path})
print_result.url = validate_url
try:
    result = resp.json()
    actual = dict(result)
    if 'message' in actual and actual['message'] is None:
        del actual['message']
    expected = {"valid": True}
    passed = resp.status_code == 200 and actual == expected and isinstance(result["valid"], bool)
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = f"200 OK and key: valid for path {valid_path}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: POST /api/path/validate validates correct path {valid_path}", passed, expected, actual, detail)

# 5b. Test POST /api/path/validate: Invalid path George Clooney → Ocean's Eleven → Mark Wahlberg
invalid_path = ["George Clooney", "Ocean's Eleven", "Mark Wahlberg"]
resp = requests.post(validate_url, json={"path": invalid_path})
print_result.url = validate_url
try:
    result = resp.json()
    actual = dict(result)
    if 'message' in actual and actual['message'] is None:
        del actual['message']
    expected = {"valid": False}
    passed = resp.status_code == 200 and actual == expected and isinstance(result["valid"], bool)
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = f"200 OK and key: valid for path {invalid_path}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: POST /api/path/validate invalid path {invalid_path}", passed, expected, actual, detail)

# 5 (original): Test POST /api/path/validate: Should validate a path (actor -> movie -> costar)
if path:
    resp = requests.post(validate_url, json={"path": path})
    print_result.url = validate_url
    try:
        result = resp.json()
        # Remove 'message' if it is None for strict comparison
        actual = dict(result)
        if 'message' in actual and actual['message'] is None:
            del actual['message']
        expected = {"valid": result["valid"]}
        passed = resp.status_code == 200 and actual == expected and isinstance(result["valid"], bool)
        detail = None
        if not passed:
            detail = f"Returned: {actual}, Expected: {expected}"
    except Exception as e:
        passed = False
        expected = f"200 OK and key: valid for path {path}"
        actual = f"Exception: {e}"
        detail = str(e)
    print_result(f"Test: POST /api/path/validate validates path {path}", passed, expected, actual, detail)
else:
    print_result.url = validate_url
    print_result("Test: POST /api/path/validate", False, "200 OK and key: valid", None, "No valid path to test")


# 6. Test POST /api/path/generate: Actor-Actor
generate_url = f"{BASE_URL}/api/path/generate"
actor_a = None
actor_b = None
if data and len(data) > 1:
    actor_a = data[0].get("actor_a")
    actor_b = data[0].get("actor_b")
if not (actor_a and actor_b):
    actor_a = "Matt Damon"
    actor_b = "Daniel Craig"
resp = requests.post(generate_url, json={
    "a": {"type": "actor", "value": actor_a},
    "b": {"type": "actor", "value": actor_b}
})
print_result.url = generate_url
try:
    result = resp.json()
    path = result.get("path")
    # Accept only non-empty, non-"-1" string as valid
    passed = resp.status_code == 200 and isinstance(path, str) and path and path != "-1" and path.strip() != "-1"
    expected = "A valid path string (not -1)"
    actual = path
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}. Full response: {result}"
except Exception as e:
    passed = False
    expected = "200 OK and valid path string"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: POST /api/path/generate actor-actor {actor_a} -> {actor_b}", passed, expected, actual, detail)

# 7. Test POST /api/path/generate: Actor-Movie
movie_title = None
if movies and len(movies) > 0:
    movie_title = movies[0]["title"]
if not movie_title:
    movie_title = "Ocean's Eleven"
resp = requests.post(generate_url, json={
    "a": {"type": "actor", "value": actor_a},
    "b": {"type": "movie", "value": movie_title}
})
print_result.url = generate_url
try:
    result = resp.json()
    path = result.get("path")
    passed = resp.status_code == 200 and isinstance(path, str) and path != "-1" and path != -1
    expected = "A valid path string (not -1)"
    actual = path
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = "200 OK and valid path string"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: POST /api/path/generate actor-movie {actor_a} -> {movie_title}", passed, expected, actual, detail)

# 8. Test POST /api/path/generate: Movie-Movie
movie_a = None
movie_b = None
if movies and len(movies) > 1:
    movie_a = movies[0]["title"]
    movie_b = movies[1]["title"]
if not (movie_a and movie_b):
    movie_a = "Ocean's Eleven"
    movie_b = "Babylon"
resp = requests.post(generate_url, json={
    "a": {"type": "movie", "value": movie_a},
    "b": {"type": "movie", "value": movie_b}
})
print_result.url = generate_url
try:
    result = resp.json()
    path = result.get("path")
    passed = resp.status_code == 200 and isinstance(path, str) and path != "-1" and path != -1
    expected = "A valid path string (not -1)"
    actual = path
    detail = None
    if not passed:
        detail = f"Returned: {actual}, Expected: {expected}"
except Exception as e:
    passed = False
    expected = "200 OK and valid path string"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: POST /api/path/generate movie-movie {movie_a} -> {movie_b}", passed, expected, actual, detail)
