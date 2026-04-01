# Levels V1/V2 Migration

This document explains the current backend migration for level data and why both level contracts now exist at the same time.

## Why This Changed

The old backend level contract was a flat array of actor-pair records:

```json
[
  {
    "actor_a": "Matt Damon",
    "actor_b": "Daniel Craig",
    "stars": 3
  }
]
```

That contract no longer matches the intended frontend gameplay model.

The new gameplay authoring requirements are:

- levels must be grouped by a named level container
- each level contains multiple games
- games can be actor-to-actor, actor-to-movie, or movie-to-movie
- stars are no longer authored in backend level data
- games need room for future boss-mode settings and notes

## Current Source Of Truth

- `levels.json` is now the authored v2 grouped level document
- `levels_v1.json` is the frozen legacy compatibility file for old consumers

This split avoids inventing fake `stars` values for the new contract and keeps the old frontend working while the new frontend is implemented.

## Endpoint Strategy

The backend now exposes both contracts in parallel.

### V1 compatibility endpoints

- `GET /api/levels`
- `GET /api/v1/levels`
- `GET /api/export/frontend-manifest`
- `GET /api/v1/export/frontend-manifest`
- `GET /api/export/frontend-snapshot`
- `GET /api/v1/export/frontend-snapshot`

These endpoints keep the old flat actor-pair payload shape.

### V2 grouped endpoints

- `GET /api/v2/levels`
- `GET /api/v2/export/frontend-manifest`
- `GET /api/v2/export/frontend-snapshot`

These endpoints expose grouped levels with nested games and typed nodes.

## V2 Level Shape

The new authored shape is:

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

## Validation Rules

The shared loader in `levels_contracts.py` performs these checks for v2 exports:

- every level and game ID must be a non-empty string
- every node must include `id`, `type`, and `label`
- node `type` must be `actor` or `movie`
- actor node IDs must exist in the actors table
- movie node IDs must exist in the movies table
- notes default to `{ "text": "" }`
- settings default to `{}`

For exported v2 payloads, node labels are normalized from the database so the frontend gets canonical names and titles.

## Metadata Differences

V1 metadata keeps the old meaning:

- `level_count` = count of flat playable records

V2 metadata adds grouped-level counters:

- `level_count` = total playable games across all grouped levels
- `level_group_count` = total named levels
- `normal_game_count` = games not marked as boss mode
- `boss_game_count` = games marked with `game-type = boss-mode`
- `level_schema_version` = current level contract schema version

## Current Data State

The backend now scaffolds five grouped v2 levels in `levels.json`.

- Level 1 contains the three migrated legacy sample games
- Levels 2 through 5 are empty placeholders until more game definitions are authored

This keeps the contract in place without inventing the remaining gameplay content.

## Versioning Decision

The project version is now `2.2.0`.

Reason:

- v2 was added without removing v1
- the existing unversioned frontend compatibility endpoints still work
- the change is additive, so it is a minor-version bump rather than a major one

The next major version should happen when v1 compatibility is removed or when the unversioned endpoints are repointed to the v2 contract.