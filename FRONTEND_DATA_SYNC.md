# Frontend Data Sync

This project can support a React frontend with almost no runtime API traffic if the frontend treats the backend as a periodic data source instead of a gameplay engine.

## Recommended Direction

Use the backend as a graph export service and TMDB ingestion service.

- Keep the backend responsible for updating `movies.db` from TMDB.
- Export the actor/movie graph in one frontend-friendly payload.
- Cache that payload in the consuming React app.
- Run lookup, suggestion, and path logic inside the frontend for normal gameplay.

That removes most or all gameplay-time API calls.

## Least Number Of API Calls

For normal play, the smallest practical integration is one full data call plus a lightweight freshness check:

```text
GET /api/export/frontend-manifest
```

and only when needed:

```text
GET /api/export/frontend-snapshot
```

Recommended policy:

- First app load: fetch the manifest, then fetch the snapshot.
- After that: reuse cached data locally.
- Refresh cadence: weekly is reasonable if your movie graph changes infrequently.
- On later app loads: fetch the manifest first and only download the snapshot if `version` or `source_updated_at` changed.

If you want zero runtime API calls after build time, use the export script instead. For the new grouped v2 levels contract, run:

```bash
./venv/bin/python export_frontend_snapshot.py \
  --api-version v2 \
  --output dist/frontend-snapshot.json \
  --manifest-output dist/frontend-manifest.json \
  --snapshot-endpoint frontend-snapshot.json
```

That writes the preloaded frontend artifacts using the v2 grouped levels shape.

## Snapshot Contents

The snapshot includes:

- `actors`: actor records with `id`, `name`, and `popularity`
- `movies`: movie records with `id`, `title`, and `release_date`
- `movie_actors`: the raw graph edges
- `adjacency.actor_to_movies`: precomputed actor-to-movie lookup map
- `adjacency.movie_to_actors`: precomputed movie-to-actor lookup map
- `levels`: existing challenge pairs
- `meta.version`: version from the backend `VERSION` file
- `meta.exported_at`: UTC export timestamp

The manifest endpoint includes:

- `version`
- `source_updated_at`
- counts for actors, movies, links, and levels
- `recommended_refresh_interval_hours`
- `snapshot_endpoint`

This is enough for a frontend to:

- render actor and movie catalogs
- pick random or filtered start nodes
- validate moves locally
- find costars and movie lists locally
- run BFS pathfinding locally
- use popularity without requesting ranked results from the backend

## Generic React Loading Pattern

This is the most project-agnostic pattern I can give you before I need specifics from the other app:

```ts
const SNAPSHOT_KEY = "co-stars-snapshot";
const SNAPSHOT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

type SnapshotMeta = {
  version: string;
  exported_at: string;
};

type Snapshot = {
  meta: SnapshotMeta;
  actors: Array<{ id: number; name: string; popularity: number | null }>;
  movies: Array<{ id: number; title: string; release_date: string | null }>;
  movie_actors: Array<{ movie_id: number; actor_id: number }>;
  adjacency: {
    actor_to_movies: Record<string, number[]>;
    movie_to_actors: Record<string, number[]>;
  };
  levels: Array<{ actor_a: string; actor_b: string; stars: number }>;
};

export async function loadSnapshot(): Promise<Snapshot> {
  const cachedRaw = localStorage.getItem(SNAPSHOT_KEY);

  if (cachedRaw) {
    const cached = JSON.parse(cachedRaw) as Snapshot;
    const ageMs = Date.now() - new Date(cached.meta.exported_at).getTime();
    if (ageMs < SNAPSHOT_MAX_AGE_MS) {
      return cached;
    }
  }

  const response = await fetch("http://localhost:8000/api/export/frontend-snapshot");
  if (!response.ok) {
    throw new Error(`Snapshot fetch failed: ${response.status}`);
  }

  const snapshot = (await response.json()) as Snapshot;
  localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot));
  return snapshot;
}
```

For large datasets, prefer IndexedDB over `localStorage`, but the sync pattern is the same.

## What To Hand Off To The React Project Agent

You can hand the other agent these concrete integration facts right now:

- Use `GET /api/export/frontend-snapshot` as the primary data-ingest endpoint.
- Use `GET /api/export/frontend-manifest` as the cheap freshness check endpoint.
- Cache the full payload client-side.
- Treat `adjacency.actor_to_movies` and `adjacency.movie_to_actors` as the core lookup structure.
- Use `version` and `source_updated_at` from the manifest to decide when to refresh.
- Do not depend on gameplay endpoints for normal play once the snapshot is loaded.
- Keep backend calls only for snapshot refreshes and future TMDB-driven updates.

That is enough for the consuming app to build a local store, selectors, and client-side graph traversal.

## Future Refactor TODOs

- TODO: make snapshot export the primary frontend contract.
- TODO: move gameplay-specific endpoints into a legacy or compatibility namespace.
- TODO: keep the long-term backend focused on TMDB ingestion, database refresh, and graph export.
- TODO: move move-validation and pathfinding fully into the frontend after the consuming app has the graph cached.
- TODO: add delta or manifest sync only if the snapshot becomes too large for a full weekly refresh.