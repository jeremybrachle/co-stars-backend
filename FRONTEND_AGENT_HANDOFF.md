# Frontend Agent Handoff

This file is the single handoff document for the consuming frontend project. It contains the minimum backend contract, data shapes, refresh strategy, and integration guidance needed to start implementing frontend-side data management and gameplay logic.

## Goal

Treat this backend as a periodic graph data source, not as the primary gameplay engine.

The intended frontend architecture is:

- fetch graph metadata from the backend
- fetch the full graph snapshot only when needed
- cache the snapshot locally in the frontend
- run lookup, selection, validation, and pathfinding logic in the frontend for normal play

This minimizes network calls and keeps gameplay responsive.

## Backend Role

The backend currently still exposes gameplay-oriented endpoints, but the preferred integration path is:

- backend owns TMDB ingestion and database maintenance
- backend exports the graph and refresh metadata
- frontend owns normal runtime gameplay logic

## Required Endpoints

These are the only endpoints the frontend needs for the snapshot-first integration model.

### 1. Health Check

```http
GET /api/health
```

Purpose:

- verify the backend is reachable
- verify the deployed version

Example response:

```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

### 2. Frontend Manifest

```http
GET /api/export/frontend-manifest
```

Purpose:

- cheap refresh check before downloading the full snapshot
- compare backend freshness to cached frontend data

Expected shape:

```json
{
  "version": "2.0.0",
  "source_updated_at": "2026-03-11T00:00:00+00:00",
  "actor_count": 2,
  "movie_count": 1,
  "relationship_count": 2,
  "level_count": 1,
  "recommended_refresh_interval_hours": 168,
  "snapshot_endpoint": "/api/export/frontend-snapshot"
}
```

Use this to decide whether a cached snapshot is stale.

## Static Preload Export

If the frontend wants to ship with a preloaded static snapshot instead of fetching from the running API first, generate the current grouped v2 artifacts with:

```bash
./venv/bin/python export_frontend_snapshot.py \
  --api-version v2 \
  --output dist/frontend-snapshot.json \
  --manifest-output dist/frontend-manifest.json \
  --snapshot-endpoint frontend-snapshot.json
```

That command writes the snapshot and manifest files in the same shape served by the v2 export endpoints.

### 3. Frontend Snapshot

```http
GET /api/export/frontend-snapshot
```

Purpose:

- download the full actor/movie graph used by the frontend
- avoid incremental gameplay calls after local caching

Expected shape:

```json
{
  "meta": {
    "version": "2.0.0",
    "exported_at": "2026-03-11T00:00:00+00:00",
    "actor_count": 2,
    "movie_count": 1,
    "relationship_count": 2,
    "level_count": 1
  },
  "actors": [
    { "id": 1461, "name": "George Clooney", "popularity": 33.1 },
    { "id": 1892, "name": "Matt Damon", "popularity": 51.25 }
  ],
  "movies": [
    { "id": 161, "title": "Ocean's Eleven", "release_date": "2001-12-07" }
  ],
  "movie_actors": [
    { "movie_id": 161, "actor_id": 1461 },
    { "movie_id": 161, "actor_id": 1892 }
  ],
  "adjacency": {
    "actor_to_movies": {
      "1461": [161],
      "1892": [161]
    },
    "movie_to_actors": {
      "161": [1461, 1892]
    }
  },
  "levels": [
    { "actor_a": "Matt Damon", "actor_b": "George Clooney", "stars": 3 }
  ]
}
```

## Frontend Data Model

Use these TypeScript shapes as the baseline contract.

```ts
export type ActorRecord = {
  id: number;
  name: string;
  popularity: number | null;
};

export type MovieRecord = {
  id: number;
  title: string;
  release_date: string | null;
};

export type MovieActorLink = {
  movie_id: number;
  actor_id: number;
};

export type LevelRecord = {
  actor_a: string;
  actor_b: string;
  stars: number;
};

export type FrontendManifest = {
  version: string;
  source_updated_at: string;
  actor_count: number;
  movie_count: number;
  relationship_count: number;
  level_count: number;
  recommended_refresh_interval_hours: number;
  snapshot_endpoint: string;
};

export type FrontendSnapshot = {
  meta: {
    version: string;
    exported_at: string;
    actor_count: number;
    movie_count: number;
    relationship_count: number;
    level_count: number;
  };
  actors: ActorRecord[];
  movies: MovieRecord[];
  movie_actors: MovieActorLink[];
  adjacency: {
    actor_to_movies: Record<string, number[]>;
    movie_to_actors: Record<string, number[]>;
  };
  levels: LevelRecord[];
};
```

## Recommended Frontend Storage

Small-to-medium dataset:

- cache the snapshot in `localStorage`

Larger dataset or richer offline behavior:

- cache the snapshot in IndexedDB

Recommended in-memory derived structures after load:

- `actorsById: Map<number, ActorRecord>`
- `moviesById: Map<number, MovieRecord>`
- `actorNameToId: Map<string, number>` with normalized lowercase keys
- `movieTitleToId: Map<string, number>` with normalized lowercase keys
- `actorToMovies: Record<string, number[]>`
- `movieToActors: Record<string, number[]>`

## Required Frontend Flow

### First Load

1. Call `GET /api/health`.
2. Call `GET /api/export/frontend-manifest`.
3. Call `GET /api/export/frontend-snapshot`.
4. Cache the snapshot.
5. Build local indexes/maps.

### Later Loads

1. Load cached snapshot and cached manifest metadata.
2. Call `GET /api/export/frontend-manifest`.
3. Compare `version` and `source_updated_at`.
4. If unchanged, keep cached snapshot.
5. If changed or missing, download a fresh snapshot.

### Refresh Policy

- weekly refresh is acceptable as a default
- the backend manifest currently recommends `168` hours
- a manual refresh button is reasonable for admin/debug flows

## Minimal Fetch Example

```ts
const SNAPSHOT_KEY = "co-stars-snapshot";
const MANIFEST_KEY = "co-stars-manifest";

export async function loadBackendSnapshot(baseUrl: string) {
  const manifestResponse = await fetch(`${baseUrl}/api/export/frontend-manifest`);
  if (!manifestResponse.ok) {
    throw new Error(`Manifest fetch failed: ${manifestResponse.status}`);
  }

  const manifest = (await manifestResponse.json()) as FrontendManifest;
  const cachedManifestRaw = localStorage.getItem(MANIFEST_KEY);
  const cachedSnapshotRaw = localStorage.getItem(SNAPSHOT_KEY);

  if (cachedManifestRaw && cachedSnapshotRaw) {
    const cachedManifest = JSON.parse(cachedManifestRaw) as FrontendManifest;
    const unchanged =
      cachedManifest.version === manifest.version &&
      cachedManifest.source_updated_at === manifest.source_updated_at;

    if (unchanged) {
      return JSON.parse(cachedSnapshotRaw) as FrontendSnapshot;
    }
  }

  const snapshotResponse = await fetch(`${baseUrl}${manifest.snapshot_endpoint}`);
  if (!snapshotResponse.ok) {
    throw new Error(`Snapshot fetch failed: ${snapshotResponse.status}`);
  }

  const snapshot = (await snapshotResponse.json()) as FrontendSnapshot;
  localStorage.setItem(MANIFEST_KEY, JSON.stringify(manifest));
  localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot));
  return snapshot;
}
```

## How To Use The Snapshot For Gameplay

The snapshot is enough to replace normal gameplay API calls.

### Get Movies For An Actor

- use `adjacency.actor_to_movies[String(actorId)]`
- map those IDs through `moviesById`

### Get Actors For A Movie

- use `adjacency.movie_to_actors[String(movieId)]`
- map those IDs through `actorsById`

### Validate A Move

- actor to movie is valid if `movieId` is in `actor_to_movies[String(actorId)]`
- movie to actor is valid if `actorId` is in `movie_to_actors[String(movieId)]`

### Find Shortest Paths

- run BFS locally over the bipartite graph
- alternate node types `actor -> movie -> actor -> movie`
- use the adjacency maps instead of hitting the backend

### Use Popularity

- popularity is raw display/sorting data only
- the frontend can sort by popularity, randomize, filter, or blend with path length heuristics

## Endpoints That Are Optional For Frontend Use

These still exist, but are not required if the snapshot is loaded:

- `GET /api/actors`
- `GET /api/movies`
- `GET /api/actor/{name}`
- `GET /api/actor/{actor_id}/movies`
- `GET /api/movie/{movie_id}/costars`
- `POST /api/path/validate`
- `POST /api/path/generate`

Use them only for compatibility, debugging, or incremental migration.

## Runtime Assumptions

- the backend is expected to allow your frontend origin through CORS
- backend CORS is controlled by `ALLOWED_ORIGINS`
- the frontend should keep `baseUrl` configurable through environment variables

Suggested frontend env var examples:

```text
VITE_API_BASE_URL=https://your-backend.example.com
NEXT_PUBLIC_API_BASE_URL=https://your-backend.example.com
REACT_APP_API_BASE_URL=https://your-backend.example.com
```

## If You Want Zero Runtime Fetches

The backend can generate a static JSON file instead of being called directly by the frontend:

```bash
./venv/bin/python export_frontend_snapshot.py \
  --api-version v2 \
  --output dist/frontend-snapshot.json \
  --manifest-output dist/frontend-manifest.json \
  --snapshot-endpoint frontend-snapshot.json
```

Those files can be bundled or hosted with the frontend app. In that mode, the backend is only needed for snapshot regeneration and database updates.

## Backend Files That Define The Contract

If the frontend project needs exact source references, these backend files are the contract-defining files:

- `fastapi_app/main.py`
- `frontend_snapshot.py`
- `path_utils.py`
- `db_helper.py`
- `VERSION`

## Integration Priority

Implement in this order:

1. health check wiring
2. manifest fetch and cache comparison
3. snapshot download and local persistence
4. local indexing utilities
5. local movie/actor lookup selectors
6. local pathfinding and move validation
7. gameplay UI wiring on top of local graph state

## Important Constraint

Do not build the frontend around per-move API calls if you can avoid it. The intended direction is to move normal game logic into the frontend and keep the backend focused on data refresh and graph export.