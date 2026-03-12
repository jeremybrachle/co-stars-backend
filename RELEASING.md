# Release Management

This project now uses a simple release workflow built around three files:

- `VERSION` is the single source of truth for the current application version.
- `CHANGELOG.md` stores released notes plus the working `Unreleased` section.
- `bump_version.py` updates the version and rolls the `Unreleased` notes into a dated release section.
- `.github/workflows/release.yml` publishes a GitHub Release from the matching changelog section.

## Current Baseline

- Initial stable baseline: `2.0.0`
- Release date: `2026-03-11`

## Versioning Rules

Use Semantic Versioning:

- `MAJOR`: breaking API or behavior changes.
- `MINOR`: backward-compatible features.
- `PATCH`: backward-compatible fixes and small improvements.

## Standard Workflow

1. Make your code changes.
2. Add release notes under `## [Unreleased]` in `CHANGELOG.md`.
3. Run one of these commands:

```bash
python3 bump_version.py patch
python3 bump_version.py minor
python3 bump_version.py major
python3 bump_version.py 1.2.3
```

4. Review the updated `VERSION` and `CHANGELOG.md`.
5. Commit the release bump.
6. Tag the release in git to trigger the GitHub Release workflow:

```bash
git tag v2.0.0
git push origin v2.0.0
```

7. GitHub Actions will then:

- verify that the pushed tag matches the value in `VERSION`
- extract the `## [2.0.0]` section from `CHANGELOG.md`
- publish a GitHub Release named `v2.0.0` with those exact notes

This keeps the git tag, the GitHub Release version, the API version, and the changelog entry aligned.

## Manual Release Trigger

You can also run the `Release` workflow manually from the GitHub Actions tab and provide a version like `2.0.0`.

The manual workflow still validates the requested version against `VERSION` and still uses the matching `CHANGELOG.md` section for the release body.

## CI Behavior

GitHub Actions runs on:

- Pushes to `main`
- Pushes to other branches
- Pull requests, which are the GitHub equivalent of GitLab merge requests

The workflow seeds a deterministic SQLite database before DB-backed tests so CI does not depend on a local tracked `movies.db` file or TMDB ingestion.

For now, CI is unit-focused. Live smoke tests are not part of the GitHub pipeline until the backend deployment flow is ready.