
# Co-Stars Backend (FastAPI)

This project is now a FastAPI-only backend for exploring connections between actors and movies. All endpoints are documented and testable via the interactive Swagger UI at `/docs` or `/redoc`.

The application version is now sourced from the root `VERSION` file so releases can be managed consistently across docs, the API, and CI.

GitHub Releases can also be generated from matching git tags and changelog entries, so a release tag like `v1.0.1` can publish the `1.0.1` notes automatically.

## How to Run

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn requests python-dotenv
   ```
2. Ensure your SQLite database (movies.db) and levels.json are present in the project root.
3. Start the server from the project root:
   ```bash
   uvicorn fastapi_app.main:app --reload
   ```
4. Open your browser and go to:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

Copy/paste URLs:

```text
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/api/health
http://localhost:8000/api/export/frontend-manifest
http://localhost:8000/api/export/frontend-snapshot
http://localhost:8000/api/levels
http://localhost:8000/api/actors
http://localhost:8000/api/movies
```

## Endpoints

- `/api/levels` — Get all levels (from levels.json)
- `/api/health` — Basic deployment/liveness check
- `/api/export/frontend-manifest` — Lightweight refresh metadata for frontend sync
- `/api/actors` — Get the full actor catalog
- `/api/movies` — Get the full movie catalog
- `/api/export/frontend-snapshot` — Export the full graph for frontend-local gameplay
- `/api/actor/{name}` — Get actor by name, including `popularity` (from DB)
- `/api/actor/{actor_id}/movies` — Get all movies for an actor, optionally with shortest-path hint metadata
- `/api/movie/{movie_id}/costars` — Get all actors in a movie, optionally with shortest-path hint metadata
- `/api/path/validate` — Validate a path (from DB)
- `/api/path/generate` — Generate a structured shortest path response between any two named nodes

### Open Suggestion Contract

The suggestion endpoints are designed to return raw data and optional path guidance, not to force one display policy.

- Popularity is exposed so the frontend can decide how to use it.
- `GET /api/actor/{actor_id}/movies` can accept `target_type` and `target_id` to attach a `path_hint` object to each movie.
- `GET /api/movie/{movie_id}/costars` can accept `exclude`, `target_type`, and `target_id` to attach a `path_hint` object to each actor.
- If a returned suggestion already is the target, its `path_hint.steps_to_target` will be `0`.
- The frontend can sort, shuffle, trim, or highlight the returned data however it wants.

This makes it possible to build classic play, hint-assisted play, quick play, and speed-round UIs on top of the same API.

All endpoints are powered by your SQLite database and helper functions. Sample payloads and schemas are visible in the Swagger UI.

If you want the consuming frontend to own the graph and avoid normal gameplay API calls, use the snapshot export flow documented in `FRONTEND_DATA_SYNC.md`.

## Notes
- The Flask implementation and all template files have been removed. This project is now FastAPI-only.
- You can visually explore and test all endpoints at `/docs`.
- For database setup and ingestion, see the main project README.
- For release versioning and changelog workflow, see `RELEASING.md` in the project root.
- Long term, the backend can be simplified toward TMDB sync plus graph export while path and move logic shifts into the consuming frontend.
