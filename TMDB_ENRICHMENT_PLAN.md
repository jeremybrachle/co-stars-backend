# TMDB Enrichment And Seed CSV Plan

This document is the implementation checklist for expanding TMDB-backed metadata while keeping the current frontend connection stable.

Primary goals:

- Keep the existing frontend working without requiring immediate frontend changes.
- Add richer movie metadata.
- Add richer actor metadata.
- Replace the hardcoded ingest list in `populate_db.py` with a seed CSV file.
- Add unit tests and smoke-test coverage for the new backend behavior.
- Keep the full rebuild flow simple enough to run in one work session, including a long-running database rebuild in the background.

## Scope

### Movie fields to add

Add these fields if TMDB provides them:

- `genres`
- `overview` or synopsis
- `poster_path`
- `original_language`
- `content_rating`

Notes:

- `poster_path` should be stored as the raw TMDB image path such as `/abc123.jpg`, not a full CDN URL.
- `content_rating` is not returned directly on the base movie payload in the way the other fields are. It comes from the TMDB movie release dates endpoint and should be pulled from the US certification when available.

### Actor fields to add

Add these fields if TMDB provides them:

- `birthday`
- `deathday`
- `place_of_birth`
- `biography`
- `profile_path`
- `known_for_department`

## TMDB API Sources

Use the TMDB v3 endpoints below for the new data.

### Movie metadata source

- `GET /movie/{movie_id}`

Use this endpoint for:

- `genres`
- `overview`
- `poster_path`
- `original_language`
- any future movie fields such as `runtime`, `vote_average`, `vote_count`, or `backdrop_path`

Relevant TMDB note:

- the movie details response includes `genres`, `original_language`, `overview`, and `poster_path`
- it also supports `append_to_response`, which may be useful later if you want to reduce separate requests

### Movie rating source

- `GET /movie/{movie_id}/release_dates`

Use this endpoint for:

- US certification values such as `G`, `PG`, `PG-13`, `R`, and similar values when present

Recommended extraction rule:

- find the `US` release block
- choose the most useful non-empty `certification`
- if no US certification exists, store `null`

### Actor metadata source

- `GET /person/{person_id}`

Use this endpoint for:

- `birthday`
- `deathday`
- `place_of_birth`
- `biography`
- `profile_path`
- `known_for_department`

### Image URL construction source

- `GET /configuration`

Use this endpoint only if you want to build full image URLs in the backend.

Recommended storage rule:

- store raw TMDB paths such as `poster_path` and `profile_path` in SQLite
- do not store full image URLs in the database
- build full URLs later using TMDB image configuration, or build them directly in the frontend from the raw path

## Frontend Compatibility Strategy

The current frontend contract should remain stable during this work.

Do not break or rename the existing fields returned by:

- `GET /api/actors`
- `GET /api/movies`
- `GET /api/export/frontend-snapshot`

Recommended approach:

- Keep the current fields exactly as they are.
- Make all new database columns nullable.
- Add new backend fields to the database and ingestion logic first.
- Expose richer metadata only through one of these safe approaches:
  - add optional fields to existing endpoints if the frontend is tolerant of extra fields
  - add new detail endpoints for actor and movie metadata
  - add a new export variant later if the frontend wants the richer snapshot

Safest first pass:

- Keep the current snapshot shape unchanged.
- Keep `/api/actors` and `/api/movies` unchanged initially.
- Add optional detail endpoints later if needed.

## Recommended Order Of Work

Follow this order to minimize risk and keep the frontend stable.

### Phase 1: Prepare seed input

1. Create a CSV file in the project root, for example `movie_seed.csv`.
2. Move the current `movies_to_ingest` values from `populate_db.py` into the CSV.
3. Store one row per movie with both ID and title.
4. The ingest logic should use only the TMDB ID from the CSV.
5. The title column is there for manual maintenance and readability only.

Recommended CSV shape:

```csv
tmdb_movie_id,title
1422,The Departed
2133,The Perfect Storm
270487,Hail Caesar!
348350,Solo: A Star Wars Story
334541,Manchester by the Sea
580489,Venom: Let There Be Carnage
652,Troy
550,Fight Club
2501,The Bourne Identity
615777,Babylon
508,Love Actually
27205,Inception
414906,The Batman
546554,Knives Out
16869,Inglourious Basterds
286217,The Martian
206647,Spectre
161,Ocean's Eleven
64682,The Great Gatsby
```

Important note:

- The current hardcoded list mixes titles and IDs.
- If the new rule is ID-driven ingestion, title-based entries must be converted to TMDB IDs before the CSV is finalized.
- The CSV should still keep the title column so you can edit the file easily later.
- The loading code should ignore the title column for ingestion decisions.

Do not rely on title lookup in the new populate flow.

### Phase 1A: Separate full rebuild from incremental sync

Do not make `populate_db.py` always destroy the database.

Target behavior:

- default mode should be additive and non-destructive
- the script should read the CSV and check whether each TMDB movie ID already exists
- if a movie already exists, skip inserting it unless an explicit refresh flag is provided
- if a movie is missing, ingest it and its related actors

Recommended CLI behavior:

- `python3 populate_db.py`
  - additive sync mode from CSV
- `python3 populate_db.py --reset`
  - full rebuild from scratch
- `python3 populate_db.py --refresh-existing`
  - revisit existing CSV-listed movies and refresh their metadata

This supports both use cases:

- initial full setup
- adding one or more new rows to the CSV later without wiping the existing database

### Phase 2: Expand the database schema

Update the schema in `db.py`.

Add nullable columns to `movies`:

- `genres_json TEXT`
- `overview TEXT`
- `poster_path TEXT`
- `original_language TEXT`
- `content_rating TEXT`

Add nullable columns to `actors`:

- `birthday TEXT`
- `deathday TEXT`
- `place_of_birth TEXT`
- `biography TEXT`
- `profile_path TEXT`
- `known_for_department TEXT`

Implementation decision:

- For this repo, a clean rebuild is still the simplest way to create a fresh enriched database.
- But the code should also support a one-time in-place schema migration so existing data can be enriched without forcing a wipe.
- `init_db()` can remain the destructive reset path.
- Add a separate migration or ensure-schema path for existing databases.

### Phase 2A: Initial migration of existing data

Add a one-time migration path for an existing `movies.db`.

Recommended approach:

1. add an `ensure_schema()` function that creates missing columns if they do not exist
2. run that schema upgrade once against the current database
3. run a metadata backfill script that visits existing movies and actors already in the database
4. populate new nullable columns without altering existing graph relationships

Recommended scripts:

- `populate_db.py --reset` for a full rebuild
- `backfill_metadata.py` for upgrading an existing populated database in place

The migration/backfill path should:

- keep existing actor, movie, and relationship rows
- add only the new columns and metadata values
- avoid deleting any existing graph data

### Phase 3: Expand TMDB fetch logic

Update `tmdb_api.py`.

Add or update helpers for:

- full movie details via `/movie/{id}`
- movie certification via `/movie/{id}/release_dates`
- full actor details via `/person/{id}`
- optional image configuration via `/configuration`

Implementation notes:

- `genres` should be stored as JSON text in SQLite unless you want a normalized `movie_genres` table.
- `content_rating` should prefer a non-empty US certification from the movie release dates payload, otherwise fall back to `null`.
- `biography` can be large, which is fine in SQLite but should not be forced into the current frontend snapshot unless needed.
- `poster_path` and `profile_path` should be stored as raw paths.
- If you want fully qualified image URLs later, use the TMDB configuration endpoint to combine `secure_base_url`, the desired image size, and the stored raw path.

### Phase 4: Update ingest flow

Update `ingest.py` and `db_helper.py`.

Movie ingest should:

- fetch the full movie payload
- fetch the release dates payload for certification
- write both current and new movie fields

Actor ingest should:

- continue inserting actor records from movie credits
- enrich each actor with `/person/{id}` data before saving, or run a second enrichment pass after movie ingest

Recommended first implementation:

- ingest the movie first
- ingest the cast list
- for each actor in the cast, fetch person details and upsert the richer actor record

Tradeoff:

- This is simple to reason about but slower because it adds many TMDB person-detail requests.
- If rebuild time becomes too slow, split actor enrichment into a separate backfill script.

### Phase 5: Keep API compatibility stable

Update `fastapi_app/main.py` carefully.

First pass recommendation:

- keep the current `Actor` and `Movie` response models unchanged
- keep `serialize_actor_rows()` and `serialize_movie_rows()` returning the old fields only
- do not change the current snapshot structure on the first pass

Optional second pass:

- add new endpoints such as:
  - `GET /api/actor/{name}/details`
  - `GET /api/movie/{movie_id}/details`

This avoids accidental frontend regressions.

### Phase 6: Replace hardcoded populate input with CSV

Update `populate_db.py`.

Target behavior:

- read `movie_seed.csv`
- parse the `tmdb_movie_id` column
- ignore the title column for ingestion logic
- call `ingest_movie_by_id()` for rows that are not already present in the database
- optionally refresh rows already present when a refresh flag is provided
- do not wipe the database unless an explicit reset flag is provided
- remove the hardcoded in-file list

Recommended follow-up:

- keep the script name `populate_db.py`
- add `--seed-file movie_seed.csv`
- optionally add `--limit N` for partial rebuild testing
- add `--reset` for destructive rebuilds
- add `--refresh-existing` for metadata refreshes without dropping tables

Recommended sync rules:

- if a CSV movie ID is new, ingest it
- if a CSV movie ID already exists and `--refresh-existing` is not set, skip it
- if a CSV movie ID already exists and `--refresh-existing` is set, refetch and update its metadata
- never delete database rows just because they are missing from the CSV unless you later build a separate prune mode intentionally

### Phase 7: Add tests

Update or extend these test areas.

Unit tests:

- `test_data_lookup.py`
- `test_api_endpoints.py`
- `test_path_utils.py` only if anything path-related is touched, otherwise leave it alone

Smoke tests:

- `api_smoke_test.py`

Fixture and seeding:

- `ci_seed_db.py`

Add test coverage for:

- new database insert and fetch behavior for enriched movie and actor fields
- CSV seed loading in `populate_db.py`
- additive sync behavior when some movie IDs already exist
- reset behavior only when `--reset` is used
- metadata refresh behavior when `--refresh-existing` is used
- movie certification extraction logic
- safe behavior when TMDB omits a field
- unchanged response shape for existing endpoints
- optional detail endpoints if they are added

Important compatibility tests:

- verify `/api/actors` still returns `id`, `name`, `popularity`
- verify `/api/movies` still returns `id`, `title`, `release_date`
- verify `/api/export/frontend-snapshot` still matches the current contract unless intentionally expanded

### Phase 8: Update docs

Update these docs after the code is working:

- `README.md`
- `TESTING.md`
- `API_ENDPOINTS.md`

Add documentation for:

- new schema fields
- how the CSV seed file works
- how to rebuild the database
- whether any new detail endpoints exist

## File-By-File Checklist

### Files that will definitely change

- `db.py`
- `db_helper.py`
- `tmdb_api.py`
- `ingest.py`
- `populate_db.py`
- `ci_seed_db.py`
- `test_data_lookup.py`
- `test_api_endpoints.py`
- `api_smoke_test.py`
- `README.md`
- `TESTING.md`
- `API_ENDPOINTS.md`

### Files likely to stay unchanged on the first pass

- `path_utils.py`
- `versus_game.py` unless actor/movie lookup helpers need richer fields
- `frontend_snapshot.py` if the snapshot contract is intentionally kept stable

### New files recommended

- `movie_seed.csv`
- optionally `backfill_metadata.py` for in-place enrichment of an existing database
- optionally `actor_backfill.py` if actor enrichment becomes too slow during the main populate run
- optionally `logs/` directory for long-running command output

## Suggested Implementation Sequence For One Work Day

This is the practical one-day order.

1. Create `movie_seed.csv` from the current ingest list after converting title-based entries to TMDB IDs.
2. Add a non-destructive CSV sync flow to `populate_db.py`.
3. Update `db.py` schema and add an in-place ensure-schema path.
4. Update `db_helper.py` inserts and selects.
5. Update `tmdb_api.py` to fetch movie details, release dates, person details, and optionally configuration.
6. Update `ingest.py` to write enriched movie and actor metadata.
7. Add an initial metadata backfill path for an already-populated database.
8. Update `ci_seed_db.py` and unit tests.
9. Run targeted unit tests.
10. Start either a full rebuild or an in-place backfill in the background.
11. Run smoke tests against the updated database.
12. Update docs.

## Long-Running Commands

These are the kinds of commands that should fit the workflow you described.

Run from the project root in WSL.

### Targeted tests before the long rebuild

```bash
python3 test_data_lookup.py
python3 test_api_endpoints.py
```

### Full database rebuild in the background

```bash
mkdir -p logs
python3 populate_db.py --reset > logs/populate_db.log 2>&1 &
```

### Add newly listed CSV movies without wiping the database

```bash
mkdir -p logs
python3 populate_db.py > logs/populate_incremental.log 2>&1 &
```

### Refresh metadata for movies already in the database

```bash
mkdir -p logs
python3 populate_db.py --refresh-existing > logs/populate_refresh.log 2>&1 &
```

### In-place metadata backfill for an existing database

```bash
mkdir -p logs
python3 backfill_metadata.py > logs/backfill_metadata.log 2>&1 &
```

### Watch progress while it runs

```bash
tail -f logs/populate_db.log
```

### Start the FastAPI server after rebuild

```bash
uvicorn fastapi_app.main:app --reload > logs/api.log 2>&1 &
```

### Run smoke tests

```bash
python3 api_smoke_test.py
```

### Run the full test pass

```bash
python3 run_all_tests.py
```

## Risk Management

Main risks:

- frontend breakage if existing API payload shapes are changed
- slow rebuilds because actor enrichment creates many extra TMDB requests
- slow incremental refreshes if `--refresh-existing` re-fetches a large catalog
- missing certification data for some movies
- image URL confusion if raw image paths and full URLs are mixed together
- inconsistent test fixtures if CI seeding is not updated alongside the schema

Mitigations:

- keep current endpoint payloads stable on the first pass
- make all new fields nullable
- keep CI and unit tests synthetic and deterministic
- add logs for background rebuilds
- keep the additive sync path non-destructive by default
- split actor enrichment into a separate script if populate becomes too slow

## Decision Points To Lock Before Coding

Decide these up front.

### Decision 1: Current endpoint shape

Recommended answer:

- keep current endpoint shapes unchanged for now

### Decision 2: Where to expose rich metadata first

Recommended answer:

- store it in the database first
- expose it through new detail endpoints second
- expand the frontend snapshot only after the frontend is ready

### Decision 3: How to store genres

Recommended answer:

- store as JSON text in the first implementation

### Decision 4: How to handle actor enrichment speed

Recommended answer:

- start with inline actor detail fetches
- split to a backfill script only if rebuild time becomes too slow

### Decision 5: Default populate behavior

Recommended answer:

- default to additive sync from CSV
- require `--reset` for destructive rebuilds
- use a separate backfill flow for initial metadata migration on an existing database

## Definition Of Done

This work is done when all of the following are true.

- the database stores the new actor and movie metadata fields
- `populate_db.py` reads movie IDs from `movie_seed.csv`
- `movie_seed.csv` includes both `tmdb_movie_id` and `title`
- the current frontend still works against the existing endpoints
- adding a new row to `movie_seed.csv` and rerunning `populate_db.py` adds only the missing movie data
- an existing populated database can be upgraded in place to fetch the new metadata
- unit tests cover the new persistence and compatibility behavior
- smoke tests still pass against a rebuilt database
- the rebuild can be kicked off in the background and monitored via logs
- docs explain the rebuild and seed flow clearly

## Recommended Next Step

After this document is in place, the next implementation step should be:

1. create `movie_seed.csv` with the current list converted to TMDB IDs
2. update `populate_db.py` so it reads the ID column, keeps the title column for human maintenance, and defaults to additive sync
3. then begin the schema, backfill, and ingestion refactor