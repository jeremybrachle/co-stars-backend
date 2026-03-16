# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog and the project uses Semantic Versioning.

## [Unreleased]

## [2.1.0] - 2026-03-14

### Added
- CSV-driven seed ingestion via `movie_seed.csv` with additive sync, reset, refresh, and limit support in `populate_db.py`.
- Enriched TMDB metadata storage for movies (`genres_json`, `overview`, `poster_path`, `original_language`, `content_rating`) and actors (`birthday`, `deathday`, `place_of_birth`, `biography`, `profile_path`, `known_for_department`).
- Non-destructive schema migration support through `ensure_schema()` plus `backfill_metadata.py` for in-place metadata refreshes on existing databases.
- Ready-to-render TMDB image URLs on enriched catalog and snapshot responses via `poster_url` and `profile_url`.
- Dedicated frontend migration handoff document in `FRONTEND_ENRICHMENT_HANDOFF.md` for adopting the enriched backend contract.

### Changed
- `GET /api/actors` and `GET /api/movies` now return additive enriched metadata while preserving existing core fields.
- `GET /api/export/frontend-snapshot` now exports enriched actor and movie records and is versioned as `2.1.0`.
- TMDB ingestion now enriches movies with content ratings and enriches cast members with person-detail metadata during ingest and refresh flows.
- API unit tests, data lookup tests, and smoke tests now validate the enriched catalog and snapshot payloads.

## [2.0.1] - 2026-03-13

### Added
- Snapshot export validation that rejects levels referencing actors missing from the current graph.
- Local artifact workflow for generating and committing `dist/frontend-manifest.json` and `dist/frontend-snapshot.json` from the real database.

### Changed
- Snapshot deployment now publishes committed JSON artifacts from `dist/` to S3 instead of requiring `movies.db` in the GitHub checkout.
- Snapshot deployment documentation now treats the manifest and snapshot files as the frontend release artifacts.
- CI fixture naming now makes placeholder data explicit, including `Fixture Bridge Line`, to avoid confusion with TMDB-backed content.

## [2.0.0] - 2026-03-11

### Added
- Version 2.0.0 baseline for the Co-Stars backend.
- Actor and movie catalog endpoints with raw popularity data.
- Path generation, validation, and normalization endpoints.
- Frontend snapshot export and manifest endpoints for frontend-local gameplay.
- Standalone API tests, data lookup tests, path utility tests, smoke tests, and aggregate test runner support.
- GitHub Actions CI workflow for build and unit-focused test jobs.