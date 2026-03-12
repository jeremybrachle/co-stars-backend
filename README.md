
# Co-Stars Backend (FastAPI)

Co-Stars Backend is a FastAPI-only backend for exploring connections between actors and movies. All endpoints are documented and testable via the interactive Swagger UI at `/docs` or `/redoc`.

Release versioning now starts from `2.0.0`, with the current application version sourced from the root `VERSION` file.

## Overview

- Query actor/movie data and relationships from a local SQLite database
- Find the shortest path between any two actors, movies, or actor/movie pairs (type-agnostic pathfinding)
- Validate connection paths
- Populate your database using The Movie Database (TMDB) API
- Strict API and pathfinding testing included

## How to Run

1. Install dependencies:
   ```bash
   source venv/bin/activate
   pip install fastapi uvicorn requests python-dotenv
   ```
2. Ensure your SQLite database (`movies.db`) and `levels.json` are present in the project root.
3. Start the server from the project root:
   ```bash
   uvicorn fastapi_app.main:app --reload
   ```
4. Open your browser and go to:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Copy/Paste Base URLs

```text
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/api/levels
http://localhost:8000/api/actors
http://localhost:8000/api/movies
```

## API Endpoints

- `GET /api/levels` — List all challenge levels (actor pairs)
- `GET /api/health` — Basic deployment/liveness check
- `GET /api/export/frontend-manifest` — Lightweight refresh metadata for frontend sync
- `GET /api/actors` — List the full actor catalog with all actor attributes
- `GET /api/movies` — List the full movie catalog with all movie attributes
- `GET /api/export/frontend-snapshot` — Export the full graph for frontend-local gameplay
- `GET /api/actor/{name}` — Get actor details by name, including popularity
- `GET /api/actor/{actor_id}/movies` — List all movies for an actor, with optional target-aware path hints
- `GET /api/movie/{movie_id}/costars` — List all actors in a movie, with optional target-aware path hints
- `POST /api/path/validate` — Validate a path (sequence of actor/movie names)
- `POST /api/path/generate` — Generate the shortest path between any two nodes (actor or movie, by name/title)

See `/docs` for full interactive documentation and sample payloads.

For frontend integration details, including exact localhost URLs and how to build open-ended game flows in a React client, see `FRONTEND_VERSUS_INTEGRATION.md`.

For frontend-local data sync and snapshot-based integration that avoids gameplay API calls, see `FRONTEND_DATA_SYNC.md`.

For a single shareable handoff file intended for the consuming frontend project's agent, see `FRONTEND_AGENT_HANDOFF.md`.

For deployment steps and the minimal frontend-facing production endpoints, see `DEPLOYMENT.md`.

For static JSON export and GitHub Actions publishing to S3/CloudFront, see `S3_SNAPSHOT_DEPLOYMENT.md`.

### Open-Ended Suggestion API

The API is now intentionally open-ended:

- Popularity is returned as raw data only.
- Suggestion endpoints return full raw lists instead of forcing one ranking policy.
- If the frontend provides `target_type` and `target_id`, suggestion endpoints attach `path_hint` metadata with shortest-path information.
- If a returned suggestion is already the target, its `path_hint.steps_to_target` will be `0`, which lets either the backend or the frontend identify an immediate winning move.
- The frontend can decide whether to sort by popularity, sort by shortest path, shuffle, filter, or blend multiple strategies.

This makes it possible to support classic play, hint-assisted play, quick play, and memory modes from the same backend contract.


## Project Structure

```
├── fastapi_app/          # FastAPI app and endpoints
├── db.py                 # Database initialization and connection management
├── db_helper.py          # Database insertion and query helper functions
├── ingest.py             # Movie ingestion logic (by title or ID)
├── tmdb_api.py           # TMDB API wrapper functions
├── populate_db.py        # Script to populate the database with movies/actors
├── path_utils.py         # Pathfinding and pretty-printing logic
├── api_smoke_test.py     # Strict API smoke test script
├── test_path_utils.py    # Unit tests for pathfinding logic
└── movies.db             # SQLite database (generated after initialization)
```

## Database Schema

### Movies Table
- `id` (INTEGER PRIMARY KEY): TMDB movie ID
- `title` (TEXT): Movie title
- `release_date` (TEXT): Release date

### Actors Table
- `id` (INTEGER PRIMARY KEY): TMDB actor ID
- `name` (TEXT): Actor name
- `popularity` (REAL): Popularity score from TMDB

### Movie_Actors Table (Junction)
- `movie_id` (INTEGER): Foreign key to movies
- `actor_id` (INTEGER): Foreign key to actors

## Setup

### Requirements
- Python 3.7+
- requests
- python-dotenv

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install requests python-dotenv
   ```

3. Set up environment variables:
   Create a `.env` file in the project root:
   ```
   TMDB_API_KEY=your_tmdb_api_key_here
   ```
   
   Get your API key from [The Movie Database (TMDB)](https://www.themoviedb.org/settings/api)


## Usage

### Populate the Database

Run the main population script to initialize and fill the database with sample movies:

```bash
python populate_db.py
```

This will:
1. Initialize a fresh SQLite database
2. Ingest a predefined list of movies
3. Fetch actors for each movie from TMDB
4. Store all data in the local database

### Run the FastAPI Backend

Start the API server (from the project root):

```bash
uvicorn fastapi_app.main:app --reload
```

Then open your browser to http://localhost:8000/docs to explore and test all endpoints visually.

### Ingest Individual Movies

```python
from ingest import ingest_movie_by_title, ingest_movie_by_id

# By movie title
ingest_movie_by_title("Ocean's Eleven")

# By TMDB ID
ingest_movie_by_id(1422)
```


### Find Connections Programmatically

```python
from path_utils import generate_path, pretty_print_path

# Find shortest path between two actors (by ID)
path = generate_path(actor_id_1, "actor", actor_id_2, "actor")
print(pretty_print_path(path, start_type="actor"))

# Find path between actor and movie, or movie and movie
path = generate_path(actor_id, "actor", movie_id, "movie")
print(pretty_print_path(path, start_type="actor"))
```


## Configuration

All database operations use `movies.db` as the default SQLite database file. This can be modified by changing the `DB_FILE` variable in `db.py` or `path_utils.py`.


## Testing

For a single command that runs the full suite and prints one aggregate summary table, see `TESTING.md`.

### Run Everything Together

If the FastAPI server is already running at `http://localhost:8000`, run:

```bash
python3 run_all_tests.py
```

If you only want the local unit-style checks and want to skip the live smoke test:

```bash
python3 run_all_tests.py --skip-smoke
```

### API Smoke Tests

Run the strict API smoke test to validate all endpoints and pathfinding logic:

```bash
python3 api_smoke_test.py
```

This script:
- Starts with a running FastAPI server (see above)
- Sends requests to all endpoints, including `/api/path/generate` and `/api/path/validate`
- Verifies full actor and movie catalogs, raw suggestion payloads, optional path hints, and structured path responses
- Prints clear PASS/FAIL output, expected vs actual values, and diagnostics for debugging

### Pathfinding Unit Tests

Run the pathfinding unit tests to verify the core logic:

```bash
python3 test_path_utils.py
```

This script:
- Tests all combinations (actor-actor, actor-movie, movie-movie, no-path)
- Prints readable test headers, input names/IDs, raw path (IDs), and pretty path (names)
- Ensures the backend pathfinding logic is robust and type-agnostic

### API Unit Tests

Run the isolated API endpoint tests:

```bash
python3 test_api_endpoints.py
```

This script:
- Verifies catalog endpoints and raw suggestion endpoints
- Checks optional `path_hint` metadata on actor and movie suggestion responses
- Verifies structured `POST /api/path/generate` output
- Uses mocked dependencies so endpoint behavior can be validated without relying on live DB state

## Release Management

This repository now tracks releases with a root-level `VERSION` file and `CHANGELOG.md`.

- The initial stable baseline is `2.0.0`.
- Update release notes in `CHANGELOG.md` under `Unreleased`.
- Bump versions with `python3 bump_version.py patch`, `python3 bump_version.py minor`, `python3 bump_version.py major`, or an explicit version like `python3 bump_version.py 1.2.3`.
- See `RELEASING.md` for the full release flow.

## GitHub Actions CI

The repository now includes a GitHub Actions workflow in `.github/workflows/ci.yml`.

The repository also includes `.github/workflows/snapshot-deploy.yml` for exporting frontend snapshot assets and publishing them to S3 from pull requests and from `main`.

- It runs on pushes to `main`.
- It runs on pushes to branches.
- It runs on pull requests, which are the GitHub equivalent of GitLab merge requests.
- It currently includes separate jobs for build validation, API unit tests, and path utility tests.
- CI seeds a deterministic SQLite fixture before DB-backed jobs so the pipeline does not depend on a checked-in `movies.db` file.
- Live smoke tests are intentionally left out of GitHub CI for now and can continue to run locally until the deployed backend flow is ready.

## GitHub Releases

You can map GitHub Releases directly to your changelog versions.

- Create or bump the target version with `bump_version.py`.
- Commit the updated `VERSION` and `CHANGELOG.md`.
- Push a matching tag like `v1.0.1`.
- The `Release` GitHub Actions workflow will validate the tag against `VERSION` and publish a GitHub Release using the matching section from `CHANGELOG.md`.

See `RELEASING.md` for the full release workflow.

## Notes
- The backend is now FastAPI-only. All Flask and template files have been removed.
- All endpoints are documented and testable at `/docs` (Swagger UI).
- For database setup and ingestion, see the usage section above.
- Long term, the backend can be reduced to TMDB ingestion, root data maintenance, and snapshot export while gameplay logic moves client-side.

