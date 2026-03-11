# Testing Overview

This project keeps each test entry point runnable on its own and now also includes a single combined runner for a full summary view.

## Quick Commands

Run everything together:

```bash
python3 run_all_tests.py
```

Run everything except the live smoke test:

```bash
python3 run_all_tests.py --skip-smoke
```

Run each test independently:

```bash
python3 test_api_endpoints.py
python3 test_path_utils.py
python3 api_smoke_test.py
```

## What The Combined Runner Does

- Runs the API unit tests.
- Runs the path utility tests.
- Runs the API smoke test against the local FastAPI server.
- Prints each suite's full output in one place.
- Finishes with an overall summary table showing suite status, pass/fail counts, totals, and duration.

## Smoke Test Requirement

`api_smoke_test.py` calls the live API at `http://localhost:8000`, so start the server first when you want the full combined run:

```bash
uvicorn fastapi_app.main:app --reload
```

If the server is not running, use:

```bash
python3 run_all_tests.py --skip-smoke
```

## Typical Workflow

Fast feedback while changing Python logic:

```bash
python3 run_all_tests.py --skip-smoke
```

Full end-to-end verification before frontend or API work:

```bash
uvicorn fastapi_app.main:app --reload
python3 run_all_tests.py
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
Path Utility Tests | PASS   | 7      | 0      | 7     | 0.08 s
API Smoke Test     | PASS   | 12     | 0      | 12    | 1.21 s
----------------------------------------------------------------------------------------
Combined totals: 30 passed, 0 failed, 30 total
```

That gives you one command for a readable aggregate view while preserving the standalone scripts for targeted debugging.