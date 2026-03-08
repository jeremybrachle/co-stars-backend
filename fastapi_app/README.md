
# Co-Stars Backend (FastAPI)

This project is now a FastAPI-only backend for exploring connections between actors and movies. All endpoints are documented and testable via the interactive Swagger UI at `/docs` or `/redoc`.

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

## Endpoints

- `/api/levels` — Get all levels (from levels.json)
- `/api/actor/{name}` — Get actor by name (from DB)
- `/api/actor/{actor_id}/movies` — Get movies for actor (from DB)
- `/api/movie/{movie_id}/costars` — Get costars for a movie (from DB)
- `/api/path/validate` — Validate a path (from DB)

All endpoints are powered by your SQLite database and helper functions. Sample payloads and schemas are visible in the Swagger UI.

## Notes
- The Flask implementation and all template files have been removed. This project is now FastAPI-only.
- You can visually explore and test all endpoints at `/docs`.
- For database setup and ingestion, see the main project README.
