# Frontend Enrichment Handoff

This document is the dedicated frontend upgrade contract for the TMDB enrichment work introduced in backend version `2.1.0`.

## What Changed

These backend changes are additive.

- Existing endpoints still exist at the same URLs.
- Existing keys such as `id`, `name`, `title`, `release_date`, and `popularity` still exist.
- New metadata fields were added to catalog and snapshot payloads.
- The frontend can ignore the new fields and continue working as before, as long as it does not strictly reject unknown JSON properties.

That means this is a passive, backward-compatible expansion of the data contract.

## Version Recommendation

The snapshot and backend version are now `2.1.0`.

Reasoning:

- `2.0.2` would imply a small patch-level fix.
- This change adds new response fields and expands the snapshot contract in a meaningful way.
- Nothing was intentionally removed or renamed, so a new minor version is the right signal.

## Integration Options

### Option 1: Snapshot-first

Recommended for the frontend.

- fetch `GET /api/export/frontend-manifest`
- compare `version` and `source_updated_at` to cached data
- fetch `GET /api/export/frontend-snapshot` when stale
- render everything locally from the snapshot

### Option 2: Catalog-first

Useful for debugging or admin views.

- fetch `GET /api/actors`
- fetch `GET /api/movies`
- use the richer metadata directly without building local graph logic first

## New Response Fields

### `GET /api/actors`

Each actor now includes:

- `birthday`
- `deathday`
- `place_of_birth`
- `biography`
- `profile_path`
- `profile_url`
- `known_for_department`

Example:

```json
{
  "id": 1892,
  "name": "Matt Damon",
  "popularity": 51.25,
  "birthday": "1970-10-08",
  "deathday": null,
  "place_of_birth": "Cambridge, Massachusetts, USA",
  "biography": "Actor and screenwriter.",
  "profile_path": "/matt.jpg",
  "profile_url": "https://image.tmdb.org/t/p/w500/matt.jpg",
  "known_for_department": "Acting"
}
```

### `GET /api/movies`

Each movie now includes:

- `genres`
- `overview`
- `poster_path`
- `poster_url`
- `original_language`
- `content_rating`

Example:

```json
{
  "id": 161,
  "title": "Ocean's Eleven",
  "release_date": "2001-12-07",
  "genres": ["Crime", "Thriller"],
  "overview": "Danny Ocean assembles a crew to rob three casinos.",
  "poster_path": "/hQQo.jpg",
  "poster_url": "https://image.tmdb.org/t/p/w500/hQQo.jpg",
  "original_language": "en",
  "content_rating": "PG-13"
}
```

### `GET /api/export/frontend-snapshot`

The snapshot now includes the same enriched actor and movie objects.

This is the easiest payload for the frontend to consume because it contains:

- enriched actors
- enriched movies
- `movie_actors` relationship edges
- adjacency maps
- levels

## Raw Paths vs Full URLs

Both are returned.

- `poster_path` and `profile_path` preserve the raw TMDB path stored in SQLite
- `poster_url` and `profile_url` are ready-to-render image URLs for frontend use

Frontend recommendation:

- use `poster_url` and `profile_url` for rendering
- keep the raw path only if you want future control over image size selection

## TypeScript Contract

```ts
export type ActorRecord = {
  id: number;
  name: string;
  popularity: number | null;
  birthday: string | null;
  deathday: string | null;
  place_of_birth: string | null;
  biography: string | null;
  profile_path: string | null;
  profile_url: string | null;
  known_for_department: string | null;
};

export type MovieRecord = {
  id: number;
  title: string;
  release_date: string | null;
  genres: string[];
  overview: string | null;
  poster_path: string | null;
  poster_url: string | null;
  original_language: string | null;
  content_rating: string | null;
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

## Frontend Upgrade Steps

1. Update your local frontend types to the `2.1.0` shapes above.
2. Keep all existing usage of `id`, `name`, `title`, `release_date`, and `popularity` unchanged.
3. Start rendering optional metadata only when present.
4. Prefer `poster_url` and `profile_url` for images.
5. If you use cached snapshots, invalidate them when `manifest.version !== cached.version` or `source_updated_at` changes.

## Minimal Rendering Guidance

Safe UI fallbacks:

- if `poster_url` is `null`, show a placeholder card image
- if `profile_url` is `null`, show a placeholder avatar
- if `overview` is empty, omit the synopsis block
- if `content_rating` is `null`, omit the badge
- if `biography` is empty, show a compact actor card instead of a long profile section

## Suggested Frontend Usage Pattern

For an actor card:

- primary text: `name`
- secondary text: `known_for_department`
- tertiary text: `place_of_birth`
- media: `profile_url`

For a movie card:

- primary text: `title`
- secondary text: `release_date`
- badges: `content_rating`, `original_language`, `genres`
- media: `poster_url`
- body copy: `overview`

## Compatibility Notes

These endpoints intentionally remain compact and were not expanded with the full metadata payload:

- `GET /api/actor/{name}`
- `GET /api/actor/{actor_id}/movies`
- `GET /api/movie/{movie_id}/costars`

Those routes still work as before and are safe to leave unchanged in the frontend.

## Verification Checklist For The Frontend Project

1. Fetch `GET /api/export/frontend-manifest` and confirm `version === "2.1.0"`.
2. Fetch `GET /api/export/frontend-snapshot` and confirm actor rows include `profile_url`.
3. Confirm movie rows include `poster_url`.
4. Render one actor card and one movie card using the new URL fields.
5. Confirm the frontend still works even if it ignores all new fields.