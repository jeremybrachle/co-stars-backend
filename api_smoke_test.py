import requests

BASE_URL = "http://localhost:8000"
SUMMARY = {"passed": 0, "failed": 0}


def print_result(name, passed, expected=None, actual=None, detail=None):
    if passed:
        SUMMARY["passed"] += 1
    else:
        SUMMARY["failed"] += 1

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if hasattr(print_result, "url") and print_result.url:
        print(f"    API Call: {print_result.url}")
        print_result.url = None
    if expected is not None or actual is not None:
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
    if detail:
        print(f"    {detail}")


def summarize_results():
    total = SUMMARY["passed"] + SUMMARY["failed"]
    print(f"\nSummary: {SUMMARY['passed']} passed, {SUMMARY['failed']} failed, {total} total")


health_url = f"{BASE_URL}/api/health"
resp = requests.get(health_url)
print_result.url = health_url
try:
    health = resp.json()
    api_version = health.get("version")
    passed = resp.status_code == 200 and health.get("status") == "ok" and isinstance(api_version, str)
    detail = None
except Exception as exc:
    health = None
    api_version = None
    passed = False
    detail = str(exc)
print_result("GET /api/health returns API status and version", passed, "200 OK with version", health, detail)


levels_url = f"{BASE_URL}/api/levels"
resp = requests.get(levels_url)
print_result.url = levels_url
try:
    levels = resp.json()
    passed = resp.status_code == 200 and isinstance(levels, list) and all(
        "actor_a" in level and "actor_b" in level for level in levels
    )
    detail = None if levels else "No levels returned."
except Exception as exc:
    levels = None
    passed = False
    detail = str(exc)
print_result("GET /api/levels returns actor-pair levels", passed, "200 OK and level list", levels, detail)


levels_v2_url = f"{BASE_URL}/api/v2/levels"
resp = requests.get(levels_v2_url)
print_result.url = levels_v2_url
try:
    levels_v2 = resp.json()
    passed = (
        resp.status_code == 200
        and isinstance(levels_v2, dict)
        and levels_v2.get("schema-version") == 2
        and isinstance(levels_v2.get("levels"), list)
    )
    detail = None if levels_v2 else "No v2 levels returned."
except Exception as exc:
    levels_v2 = None
    passed = False
    detail = str(exc)
print_result("GET /api/v2/levels returns grouped v2 levels", passed, "200 OK and grouped level document", levels_v2, detail)


manifest_v2_url = f"{BASE_URL}/api/v2/export/frontend-manifest"
resp = requests.get(manifest_v2_url)
print_result.url = manifest_v2_url
try:
    manifest_v2 = resp.json()
    passed = (
        resp.status_code == 200
        and manifest_v2.get("level_schema_version") == 2
        and "level_group_count" in manifest_v2
        and manifest_v2.get("snapshot_endpoint") == "/api/v2/export/frontend-snapshot"
    )
    detail = None if manifest_v2 else "No v2 manifest returned."
except Exception as exc:
    manifest_v2 = None
    passed = False
    detail = str(exc)
print_result("GET /api/v2/export/frontend-manifest returns grouped metadata", passed, "200 OK and grouped manifest metadata", manifest_v2, detail)


snapshot_v2_url = f"{BASE_URL}/api/v2/export/frontend-snapshot"
resp = requests.get(snapshot_v2_url)
print_result.url = snapshot_v2_url
try:
    snapshot_v2 = resp.json()
    passed = (
        resp.status_code == 200
        and snapshot_v2.get("meta", {}).get("level_schema_version") == 2
        and "level_group_count" in snapshot_v2.get("meta", {})
        and isinstance(snapshot_v2.get("levels"), list)
    )
    detail = None if snapshot_v2 else "No v2 snapshot returned."
except Exception as exc:
    snapshot_v2 = None
    passed = False
    detail = str(exc)
print_result("GET /api/v2/export/frontend-snapshot returns grouped snapshot", passed, "200 OK and grouped snapshot payload", snapshot_v2, detail)


actors_url = f"{BASE_URL}/api/actors"
resp = requests.get(actors_url)
print_result.url = actors_url
try:
    all_actors = resp.json()
    passed = resp.status_code == 200 and isinstance(all_actors, list) and all(
        "id" in actor
        and "name" in actor
        and "popularity" in actor
        and "birthday" in actor
        and "profile_path" in actor
        and "profile_url" in actor
        and "known_for_department" in actor
        for actor in all_actors
    )
    detail = None if all_actors else "No actors returned."
except Exception as exc:
    all_actors = None
    passed = False
    detail = str(exc)
print_result("GET /api/actors returns enriched actor catalog", passed, "200 OK and enriched actor list", all_actors, detail)


movies_catalog_url = f"{BASE_URL}/api/movies"
resp = requests.get(movies_catalog_url)
print_result.url = movies_catalog_url
try:
    all_movies = resp.json()
    passed = resp.status_code == 200 and isinstance(all_movies, list) and all(
        "id" in movie
        and "title" in movie
        and "release_date" in movie
        and "genres" in movie
        and "overview" in movie
        and "poster_path" in movie
        and "poster_url" in movie
        and "original_language" in movie
        and "content_rating" in movie
        for movie in all_movies
    )
    detail = None if all_movies else "No movies returned."
except Exception as exc:
    all_movies = None
    passed = False
    detail = str(exc)
print_result("GET /api/movies returns enriched movie catalog", passed, "200 OK and enriched movie list", all_movies, detail)


snapshot_url = f"{BASE_URL}/api/export/frontend-snapshot"
resp = requests.get(snapshot_url)
print_result.url = snapshot_url
try:
    snapshot = resp.json()
    snapshot_actors = snapshot.get("actors", [])
    snapshot_movies = snapshot.get("movies", [])
    passed = (
        resp.status_code == 200
        and isinstance(snapshot.get("meta"), dict)
        and snapshot.get("meta", {}).get("version") == api_version
        and isinstance(snapshot_actors, list)
        and isinstance(snapshot_movies, list)
        and all("profile_url" in actor for actor in snapshot_actors)
        and all("poster_url" in movie for movie in snapshot_movies)
    )
    detail = None
except Exception as exc:
    snapshot = None
    passed = False
    detail = str(exc)
print_result("GET /api/export/frontend-snapshot returns enriched graph payload", passed, "200 OK and enriched snapshot", snapshot, detail)


start_actor_name = "George Clooney"
target_actor_name = "Matt Damon"
if levels:
    start_actor_name = levels[0].get("actor_a") or start_actor_name
    target_actor_name = levels[0].get("actor_b") or target_actor_name

start_actor_url = f"{BASE_URL}/api/actor/{start_actor_name}"
resp = requests.get(start_actor_url)
print_result.url = start_actor_url
try:
    start_actor = resp.json()
    passed = resp.status_code == 200 and all(key in start_actor for key in ["id", "name", "popularity"])
    detail = None
except Exception as exc:
    start_actor = None
    passed = False
    detail = str(exc)
print_result(f"GET /api/actor/{{name}} resolves {start_actor_name}", passed, "200 OK and actor record", start_actor, detail)


target_actor_url = f"{BASE_URL}/api/actor/{target_actor_name}"
resp = requests.get(target_actor_url)
print_result.url = target_actor_url
try:
    target_actor = resp.json()
    passed = resp.status_code == 200 and all(key in target_actor for key in ["id", "name", "popularity"])
    detail = None
except Exception as exc:
    target_actor = None
    passed = False
    detail = str(exc)
print_result(f"GET /api/actor/{{name}} resolves {target_actor_name}", passed, "200 OK and actor record", target_actor, detail)


invalid_actor_url = f"{BASE_URL}/api/actor/DefinitelyNotARealActorName12345"
resp = requests.get(invalid_actor_url)
print_result.url = invalid_actor_url
try:
    missing_actor = resp.json()
    passed = resp.status_code == 404 and missing_actor == {"error": "Actor not found"}
    detail = None
except Exception as exc:
    missing_actor = None
    passed = False
    detail = str(exc)
print_result("GET /api/actor/{name} returns 404 for missing actor", passed, {"error": "Actor not found"}, missing_actor, detail)


actor_id = start_actor["id"] if start_actor else 1
target_actor_id = target_actor["id"] if target_actor else None
movies_for_actor_url = f"{BASE_URL}/api/actor/{actor_id}/movies"
if target_actor_id is not None:
    movies_for_actor_url += f"?target_type=actor&target_id={target_actor_id}"
resp = requests.get(movies_for_actor_url)
print_result.url = movies_for_actor_url
try:
    actor_movies = resp.json()
    passed = resp.status_code == 200 and isinstance(actor_movies, list) and all(
        "id" in movie and "title" in movie and "release_date" in movie for movie in actor_movies
    )
    if passed and target_actor_id is not None:
        passed = all("path_hint" in movie for movie in actor_movies)
    detail = None if actor_movies else "No movies returned for actor."
except Exception as exc:
    actor_movies = None
    passed = False
    detail = str(exc)
print_result(
    f"GET /api/actor/{{actor_id}}/movies returns raw movie suggestions for actor_id {actor_id}",
    passed,
    "200 OK and movie list with optional path_hint",
    actor_movies,
    detail,
)


movie_id = actor_movies[0]["id"] if actor_movies else None
if movie_id is not None:
    costars_url = f"{BASE_URL}/api/movie/{movie_id}/costars?exclude={requests.utils.quote(start_actor_name)}"
    if target_actor_id is not None:
        costars_url += f"&target_type=actor&target_id={target_actor_id}"
    resp = requests.get(costars_url)
    print_result.url = costars_url
    try:
        costars = resp.json()
        passed = resp.status_code == 200 and isinstance(costars, list) and all(
            "id" in actor and "name" in actor and "popularity" in actor for actor in costars
        )
        if passed and target_actor_id is not None:
            passed = all("path_hint" in actor for actor in costars)
        detail = None if costars else "No costars returned for movie."
    except Exception as exc:
        costars = None
        passed = False
        detail = str(exc)
    print_result(
        f"GET /api/movie/{{movie_id}}/costars returns raw actor suggestions for movie_id {movie_id}",
        passed,
        "200 OK and actor list with optional path_hint",
        costars,
        detail,
    )
else:
    costars = None
    print_result("GET /api/movie/{movie_id}/costars", False, "Movie id available", movie_id, "No movie_id available")


invalid_movie_url = f"{BASE_URL}/api/movie/999999999/costars"
resp = requests.get(invalid_movie_url)
print_result.url = invalid_movie_url
try:
    missing_movie = resp.json()
    passed = resp.status_code == 404 and missing_movie == {"error": "Movie not found"}
    detail = None
except Exception as exc:
    missing_movie = None
    passed = False
    detail = str(exc)
print_result("GET /api/movie/{movie_id}/costars returns 404 for missing movie", passed, {"error": "Movie not found"}, missing_movie, detail)


validate_url = f"{BASE_URL}/api/path/validate"
valid_path = ["George Clooney", "Ocean's Eleven", "Matt Damon"]
resp = requests.post(validate_url, json={"path": valid_path})
print_result.url = validate_url
try:
    validation = resp.json()
    passed = resp.status_code == 200 and validation.get("valid") is True
    detail = None
except Exception as exc:
    validation = None
    passed = False
    detail = str(exc)
print_result("POST /api/path/validate accepts a valid path", passed, {"valid": True}, validation, detail)


invalid_path = ["George Clooney", "Ocean's Eleven", "Definitely Not In This Movie"]
resp = requests.post(validate_url, json={"path": invalid_path})
print_result.url = validate_url
try:
    invalid_validation = resp.json()
    passed = resp.status_code == 200 and invalid_validation.get("valid") is False
    detail = None
except Exception as exc:
    invalid_validation = None
    passed = False
    detail = str(exc)
print_result("POST /api/path/validate rejects an invalid path", passed, {"valid": False}, invalid_validation, detail)


generate_url = f"{BASE_URL}/api/path/generate"
resp = requests.post(
    generate_url,
    json={
        "a": {"type": "actor", "value": start_actor_name},
        "b": {"type": "actor", "value": target_actor_name},
    },
)
print_result.url = generate_url
try:
    generated = resp.json()
    passed = (
        resp.status_code == 200
        and isinstance(generated.get("path"), str)
        and generated.get("path") != "-1"
        and isinstance(generated.get("nodes"), list)
        and len(generated.get("nodes")) >= 2
        and "steps" in generated
    )
    detail = None
except Exception as exc:
    generated = None
    passed = False
    detail = str(exc)
print_result("POST /api/path/generate returns a structured path", passed, "200 OK and structured path response", generated, detail)


summarize_results()
