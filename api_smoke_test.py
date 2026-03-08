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

BASE_URL = "http://localhost:5000"

def print_result(name, passed, expected=None, actual=None, detail=None):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if expected is not None or actual is not None:
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
    if detail:
        print(f"    {detail}")



# 1. Test GET /api/levels: Should return a list of level dicts with actor_a and actor_b
resp = requests.get(f"{BASE_URL}/api/levels")
try:
    data = resp.json()
    passed = resp.status_code == 200 and isinstance(data, list)
    expected = "200 OK and list of levels with actor_a/actor_b"
    actual = f"{resp.status_code} and {type(data).__name__}"
    # Explicit value check: first level has actor_a and actor_b
    detail = None
    if passed and data:
        first = data[0]
        if not ("actor_a" in first and "actor_b" in first):
            passed = False
            detail = f"First level missing actor_a or actor_b: {first}"
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
resp = requests.get(f"{BASE_URL}/api/actor/{actor_name}")
try:
    actor_data = resp.json()
    passed = resp.status_code == 200 and "id" in actor_data and "name" in actor_data
    expected = f"200 OK and keys: id, name for actor {actor_name}"
    actual = f"{resp.status_code} and keys: {list(actor_data.keys()) if isinstance(actor_data, dict) else type(actor_data).__name__}"
    detail = None
    # Explicit value check: returned name matches searched name (case-insensitive)
    if passed and actor_data["name"].lower() != actor_name.lower():
        passed = False
        detail = f"Returned name '{actor_data['name']}' does not match searched '{actor_name}'"
except Exception as e:
    passed = False
    actor_data = None
    expected = f"200 OK and keys: id, name for actor {actor_name}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<name> returns correct actor for '{actor_name}'", passed, expected, actual, detail)

# 2b. Test GET /api/actor/<name> with a non-existent actor
invalid_actor = "DefinitelyNotARealActorName12345"
resp = requests.get(f"{BASE_URL}/api/actor/{invalid_actor}")
try:
    data = resp.json()
    passed = resp.status_code == 404 and "error" in data
    expected = "404 and error message for non-existent actor"
    actual = f"{resp.status_code} and keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}"
    detail = None
    if passed and "not found" not in data["error"].lower():
        passed = False
        detail = f"Error message does not mention 'not found': {data['error']}"
except Exception as e:
    passed = False
    expected = "404 and error message for non-existent actor"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<name> returns 404 for non-existent actor", passed, expected, actual, detail)



# 3. Test GET /api/actor/<actor_id>/movies: Should return movies for the actor, and one should match the first level's movie if possible
actor_id = actor_data["id"] if actor_data else 1
resp = requests.get(f"{BASE_URL}/api/actor/{actor_id}/movies")
try:
    movies = resp.json()
    passed = resp.status_code == 200 and isinstance(movies, list)
    expected = f"200 OK and list of movies for actor_id {actor_id}"
    actual = f"{resp.status_code} and {type(movies).__name__}"
    detail = None
    # Explicit value check: at least one movie title is present
    if passed and not movies:
        passed = False
        detail = "No movies returned for actor."
    # If the first level has a movie title, check if it appears
    if passed and data and "movie" in data[0]:
        level_movie = data[0]["movie"]
        if not any(m["title"] == level_movie for m in movies):
            detail = f"Level movie '{level_movie}' not found in actor's movies."
except Exception as e:
    passed = False
    movies = None
    expected = f"200 OK and list of movies for actor_id {actor_id}"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/actor/<actor_id>/movies returns movies for actor_id {actor_id}", passed, expected, actual, detail)



###############################
# 4. Test GET /api/movie/<movie_id>/costars: Should return costars for a movie, and the original actor should not be in the list
movie_id = None
if movies and len(movies) > 0:
    movie_id = movies[0]["id"]
if movie_id:
    resp = requests.get(f"{BASE_URL}/api/movie/{movie_id}/costars")
    try:
        costars = resp.json()
        passed = resp.status_code == 200 and isinstance(costars, list)
        expected = f"200 OK and list of costars for movie_id {movie_id}"
        actual = f"{resp.status_code} and {type(costars).__name__}"
        detail = None
        # Explicit value check: actor_name should not be in costars
        if passed and any(c["name"].lower() == actor_name.lower() for c in costars):
            passed = False
            detail = f"Actor '{actor_name}' found in costars list."
        # Also check that at least one costar is present
        if passed and not costars:
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
    print_result("Test: GET /api/movie/<movie_id>/costars", False, "No movie_id available", None, "No movie_id available")

# 4b. Test GET /api/movie/<movie_id>/costars with a non-existent movie
invalid_movie_id = 999999999  # unlikely to exist
resp = requests.get(f"{BASE_URL}/api/movie/{invalid_movie_id}/costars")
try:
    data = resp.json()
    # Accept either 200 with empty list, or 404 with error (depending on API design)
    if resp.status_code == 200:
        passed = isinstance(data, list) and len(data) == 0
        expected = "200 and empty list for non-existent movie"
        actual = f"{resp.status_code} and {data}"
        detail = None
    else:
        passed = resp.status_code == 404 and "error" in data
        expected = "404 and error message for non-existent movie"
        actual = f"{resp.status_code} and keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}"
        detail = None
        if passed and "not found" not in data["error"].lower():
            passed = False
            detail = f"Error message does not mention 'not found': {data['error']}"
except Exception as e:
    passed = False
    expected = "200 and empty list or 404 and error message for non-existent movie"
    actual = f"Exception: {e}"
    detail = str(e)
print_result(f"Test: GET /api/movie/<movie_id>/costars returns empty or 404 for non-existent movie", passed, expected, actual, detail)



# 5. Test POST /api/path/validate: Should validate a path (actor -> movie -> costar)
path = []
if actor_data and movies and len(movies) > 0:
    path = [actor_data["name"], movies[0]["title"]]
    # Try to add a costar if available
    if 'costars' in locals() and costars and len(costars) > 0:
        path.append(costars[0]["name"])

if path:
    resp = requests.post(f"{BASE_URL}/api/path/validate", json={"path": path})
    try:
        result = resp.json()
        passed = resp.status_code == 200 and "valid" in result
        expected = f"200 OK and key: valid for path {path}"
        actual = f"{resp.status_code} and keys: {list(result.keys()) if isinstance(result, dict) else type(result).__name__}"
        detail = None
        # Explicit value check: valid should be True or False
        if passed and not isinstance(result["valid"], bool):
            passed = False
            detail = f"'valid' key is not boolean: {result['valid']}"
    except Exception as e:
        passed = False
        expected = f"200 OK and key: valid for path {path}"
        actual = f"Exception: {e}"
        detail = str(e)
    print_result(f"Test: POST /api/path/validate validates path {path}", passed, expected, actual, detail)
else:
    print_result("Test: POST /api/path/validate", False, "200 OK and key: valid", None, "No valid path to test")
