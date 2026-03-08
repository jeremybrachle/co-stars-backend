
# Co-Stars Backend (FastAPI)

Co-Stars Backend is a FastAPI-only backend for exploring connections between actors and movies. All endpoints are documented and testable via the interactive Swagger UI at `/docs` or `/redoc`.

## Overview

- Query actor/movie data and relationships from a local SQLite database
- Find the shortest path between any two actors, movies, or actor/movie pairs (type-agnostic pathfinding)
- Validate connection paths
- Populate your database using The Movie Database (TMDB) API
- Strict API and pathfinding testing included

## How to Run

1. Install dependencies:
   ```bash
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

## API Endpoints

- `GET /api/levels` — List all challenge levels (actor pairs)
- `GET /api/actor/{name}` — Get actor details by name
- `GET /api/actor/{actor_id}/movies` — List all movies for an actor
- `GET /api/movie/{movie_id}/costars` — List all costars for a movie
- `POST /api/path/validate` — Validate a path (sequence of actor/movie names)
- `POST /api/path/generate` — Generate the shortest path between any two nodes (actor or movie, by name/title)

See `/docs` for full interactive documentation and sample payloads.


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

### API Smoke Tests

Run the strict API smoke test to validate all endpoints and pathfinding logic:

```bash
python3 api_smoke_test.py
```

This script:
- Starts with a running FastAPI server (see above)
- Sends requests to all endpoints, including `/api/path/generate` and `/api/path/validate`
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

## Notes
- The backend is now FastAPI-only. All Flask and template files have been removed.
- All endpoints are documented and testable at `/docs` (Swagger UI).
- For database setup and ingestion, see the usage section above.

