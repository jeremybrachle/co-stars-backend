# Frontend Levels V2 Handoff

This document is intended for the frontend agent or frontend developer that will migrate the app from the legacy flat level contract to the new grouped v2 level contract.

## Goal

Move frontend level ingestion to the new grouped v2 endpoints without breaking the currently deployed v1-based experience during rollout.

## Backend Endpoints To Use

### Current legacy compatibility endpoints

- `GET /api/levels`
- `GET /api/export/frontend-manifest`
- `GET /api/export/frontend-snapshot`

These are still live and should be treated as v1 compatibility only.

### New grouped v2 endpoints

- `GET /api/v2/levels`
- `GET /api/v2/export/frontend-manifest`
- `GET /api/v2/export/frontend-snapshot`

The frontend migration should target the v2 endpoints.

## Contract Summary

### V2 levels document

```json
{
  "schema-version": 2,
  "levels": [
    {
      "level-id": "1",
      "level-name": "Level 1 - Starter Pack",
      "game-data": [
        {
          "game-id": "1",
          "game-type": "normal-non-boss",
          "startNode": { "id": 1892, "type": "actor", "label": "Matt Damon" },
          "targetNode": { "id": 8784, "type": "actor", "label": "Daniel Craig" },
          "notes": { "text": "Migrated from the legacy flat levels list." },
          "settings": {}
        }
      ]
    }
  ]
}
```

### V2 snapshot metadata additions

`GET /api/v2/export/frontend-snapshot` and `GET /api/v2/export/frontend-manifest` now include:

- `level_count`: total playable games
- `level_group_count`: total named levels
- `normal_game_count`: total non-boss games
- `boss_game_count`: total boss games
- `level_schema_version`: expected to be `2`

## Important Behavioral Changes

### 1. Stars are gone from level data

The backend no longer authors `stars` for v2 levels.

Frontend requirement:

- remove any assumption that `stars` exist on v2 level/game records
- calculate stars client-side at runtime from the optimal path logic

### 2. Level selection is now two-tiered

The frontend should no longer treat `levels` as a flat list of playable items.

New UI/data flow:

1. choose a named level group
2. choose or sequence through the games inside that level
3. launch gameplay from the selected game's `startNode` and `targetNode`

### 3. Nodes are already typed

Each game now declares fully typed endpoints:

- `startNode.type` is `actor` or `movie`
- `targetNode.type` is `actor` or `movie`

Frontend requirement:

- stop inferring actor-vs-actor from the level shape
- branch gameplay setup from the node `type` fields instead

### 4. Boss support is not fully implemented yet

`game-type` already exists so the frontend can prepare for boss-mode UX.

Current expectation:

- support at least `normal-non-boss`
- treat `boss-mode` as reserved for future behavior
- do not hard-fail if `settings` contains additional keys later

## Recommended TypeScript Shapes

```ts
export type LevelNode = {
  id: number;
  type: "actor" | "movie";
  label: string;
};

export type LevelNotes = {
  text: string;
};

export type LevelGameV2 = {
  "game-id": string;
  "game-type": string;
  startNode: LevelNode;
  targetNode: LevelNode;
  notes: LevelNotes;
  settings: Record<string, unknown>;
};

export type LevelGroupV2 = {
  "level-id": string;
  "level-name": string;
  "game-data": LevelGameV2[];
};

export type LevelsDocumentV2 = {
  "schema-version": 2;
  levels: LevelGroupV2[];
};

export type FrontendManifestV2 = {
  version: string;
  source_updated_at: string;
  actor_count: number;
  movie_count: number;
  relationship_count: number;
  level_count: number;
  level_group_count: number;
  normal_game_count: number;
  boss_game_count: number;
  level_schema_version: number;
  recommended_refresh_interval_hours: number;
  snapshot_endpoint: string;
};
```

## Frontend Migration Plan

### Phase 1

- keep the old frontend using the unversioned v1 endpoints
- add parallel v2 fetch utilities and v2 TypeScript types
- gate v2 UI behind a feature flag if needed

### Phase 2

- switch snapshot refresh checks to `/api/v2/export/frontend-manifest`
- switch snapshot ingestion to `/api/v2/export/frontend-snapshot`
- update cached storage keys so v1 and v2 snapshots do not collide

Suggested keys:

- `co-stars-snapshot-v1`
- `co-stars-manifest-v1`
- `co-stars-snapshot-v2`
- `co-stars-manifest-v2`

### Phase 3

- update selectors and state so UI is driven by level groups and nested games
- remove any dependency on `stars` being present in level payloads
- compute stars from runtime path results instead

### Phase 4

- once the frontend is stable on v2, stop depending on v1 routes
- backend can later remove v1 in a future major version

## Minimal Fetch Example

```ts
export async function loadLevelsV2(baseUrl: string) {
  const response = await fetch(`${baseUrl}/api/v2/levels`);
  if (!response.ok) {
    throw new Error(`V2 levels fetch failed: ${response.status}`);
  }

  return (await response.json()) as LevelsDocumentV2;
}

export async function loadSnapshotV2(baseUrl: string) {
  const manifestResponse = await fetch(`${baseUrl}/api/v2/export/frontend-manifest`);
  if (!manifestResponse.ok) {
    throw new Error(`V2 manifest fetch failed: ${manifestResponse.status}`);
  }

  const manifest = (await manifestResponse.json()) as FrontendManifestV2;
  const snapshotResponse = await fetch(`${baseUrl}${manifest.snapshot_endpoint}`);
  if (!snapshotResponse.ok) {
    throw new Error(`V2 snapshot fetch failed: ${snapshotResponse.status}`);
  }

  return snapshotResponse.json();
}
```

## Current Data Caveat

The backend contract is ready for five grouped levels, but only the first level currently has migrated sample games.

Frontend requirement:

- handle empty `game-data` arrays safely
- do not assume every level group already contains 10 games

## What Not To Do

- do not read `stars` from v2 levels
- do not flatten grouped v2 levels back into a single list unless the UI truly needs a derived view
- do not assume all games are actor-to-actor
- do not hardcode gameplay setup around one node type combination