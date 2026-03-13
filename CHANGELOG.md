# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog and the project uses Semantic Versioning.

## [Unreleased]

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