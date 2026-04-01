# Testing Overview

This project keeps each test entry point runnable on its own and now also includes a single combined runner for a full summary view.

## Quick Commands

Run everything together:

```bash
./venv/bin/python run_all_tests.py
```

Run everything except the live smoke test:

```bash
./venv/bin/python run_all_tests.py --skip-smoke
```

Run each test independently:

```bash
./venv/bin/python test_api_endpoints.py
./venv/bin/python test_data_lookup.py
./venv/bin/python test_path_utils.py
./venv/bin/python api_smoke_test.py
```

## What The Combined Runner Does

- Runs the API unit tests.
- Runs the data lookup and snapshot assembly unit tests.
- Runs the path utility tests.
- Runs the API smoke test against the local FastAPI server.
- Prints each suite's full output in one place.

### Data Lookup Unit Tests

Run the DB lookup and snapshot builder tests:

```bash
./venv/bin/python test_data_lookup.py
```

This script:
- Verifies DB helper lookup behavior against a temporary SQLite fixture
- Checks ordering, exclusions, existence checks, and ID-based record lookups
- Verifies frontend snapshot and manifest assembly with mocked data providers
- Finishes with an overall summary table showing suite status, pass/fail counts, totals, and duration.

## Smoke Test Requirement

`api_smoke_test.py` calls the live API at `http://localhost:8000`, so start the server first when you want the full combined run:

```bash
./venv/bin/uvicorn fastapi_app.main:app --reload
```

If the server is not running, use:

```bash
./venv/bin/python run_all_tests.py --skip-smoke
```

## Typical Workflow

Fast feedback while changing Python logic:

```bash
./venv/bin/python run_all_tests.py --skip-smoke
```

Full end-to-end verification before frontend or API work:

```bash
./venv/bin/uvicorn fastapi_app.main:app --reload
./venv/bin/python run_all_tests.py
```

## Output Shape

The runner keeps each test suite's existing output intact, then adds a combined table like this:

```text
========================================================================================
Overall Test Summary
========================================================================================
Suite              | Status | Passed | Failed | Total | Duration
-------------------+--------+--------+--------+-------+---------
API Unit Tests     | PASS   | 11     | 0      | 11    | 0.42 s
Data Lookup Tests  | PASS   | 6      | 0      | 6     | 0.05 s
Path Utility Tests | PASS   | 7      | 0      | 7     | 0.08 s
API Smoke Test     | PASS   | 12     | 0      | 12    | 1.21 s
----------------------------------------------------------------------------------------
Combined totals: 36 passed, 0 failed, 36 total
```

That gives you one command for a readable aggregate view while preserving the standalone scripts for targeted debugging.