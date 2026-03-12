# Deployment Guide

This backend is ready to serve frontend snapshot data, but deployment is not just about starting `uvicorn`. To make it useful to the consuming frontend, you need a stable URL, a deployed database, and correct CORS settings.

## Minimum Deploy Checklist

1. Deploy the FastAPI app so it has a stable public base URL.
2. Ensure `movies.db` exists on the deployed host and contains your current dataset.
3. Ensure `levels.json` is present alongside the app.
4. Set `ALLOWED_ORIGINS` to the frontend origins that should be allowed to fetch snapshot data.
5. Confirm these endpoints work after deploy:
   - `GET /api/health`
   - `GET /api/export/frontend-manifest`
   - `GET /api/export/frontend-snapshot`

## Environment

Start from `.env.example` and copy the values you need into your deployed environment.

Set `ALLOWED_ORIGINS` as a comma-separated list. Example:

```text
ALLOWED_ORIGINS=https://your-frontend.example.com,http://localhost:3000
```

This is required if the frontend will fetch the snapshot directly from a browser.

## Frontend-Facing Endpoints

These are the endpoints the frontend actually needs for snapshot-style integration:

- `GET /api/health`
  - Purpose: deployment/liveness check
- `GET /api/export/frontend-manifest`
  - Purpose: cheap freshness check before downloading the full snapshot
- `GET /api/export/frontend-snapshot`
  - Purpose: full graph export for local gameplay logic

Everything else can remain available for compatibility and debugging, but these three are the core deployment endpoints for the React consumer.

## Recommended Frontend Fetch Pattern

1. Call `GET /api/health` during environment verification or status monitoring.
2. Call `GET /api/export/frontend-manifest` at app startup.
3. Compare `version` or `source_updated_at` with the cached copy.
4. Only call `GET /api/export/frontend-snapshot` if the cache is missing or stale.
5. Cache the snapshot in the frontend and run graph logic locally.

## Files To Share With The Frontend Team

Share these files or their contents with the consuming frontend project or agent:

- `FRONTEND_DATA_SYNC.md`
- `API_ENDPOINTS.md`
- `VERSION`
- `fastapi_app/main.py`
  - mainly for endpoint shapes and models
- `frontend_snapshot.py`
  - mainly for snapshot structure

If you want the frontend team to reimplement lookup and pathfinding faithfully, also share:

- `path_utils.py`

If you want them to understand the raw data model, also share:

- `db_helper.py`

## Local Pre-Deploy Verification

Before you deploy, run:

```bash
python3 test_api_endpoints.py
python3 test_path_utils.py
uvicorn fastapi_app.main:app --reload
```

Then verify in a browser or with curl:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/export/frontend-manifest
curl http://localhost:8000/api/export/frontend-snapshot
```

## Future Refactor Direction

The current backend still exposes gameplay-oriented endpoints, but the long-term clean shape is:

- TMDB ingestion and database maintenance
- graph export endpoints
- compatibility endpoints only where still needed

That keeps the frontend in control of gameplay while the backend remains the canonical data source.