import argparse
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY_PATTERN = re.compile(r"Summary:\s+(\d+) passed,\s+(\d+) failed,\s+(\d+) total")

TEST_SUITES = [
    {
        "key": "api-unit",
        "name": "API Unit Tests",
        "command": [sys.executable, "test_api_endpoints.py"],
        "requires_server": False,
        "description": "FastAPI endpoint tests with mocked dependencies.",
    },
    {
        "key": "path-unit",
        "name": "Path Utility Tests",
        "command": [sys.executable, "test_path_utils.py"],
        "requires_server": False,
        "description": "Core pathfinding and normalization tests.",
    },
    {
        "key": "api-smoke",
        "name": "API Smoke Test",
        "command": [sys.executable, "api_smoke_test.py"],
        "requires_server": True,
        "description": "Live HTTP checks against a running FastAPI server.",
    },
]


def format_duration(seconds):
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"


def parse_summary(output):
    match = SUMMARY_PATTERN.search(output)
    if not match:
        return None
    passed, failed, total = (int(value) for value in match.groups())
    return {"passed": passed, "failed": failed, "total": total}


def print_rule(char="=", width=88):
    print(char * width)


def print_header(title):
    print_rule("=")
    print(title)
    print_rule("=")


def print_suite_output(name, command, duration, returncode, output, parsed_summary, skipped=False, skip_reason=None):
    print_rule("-")
    print(name)
    print_rule("-")
    print(f"Command:  {' '.join(command)}")
    print(f"Duration: {format_duration(duration)}")

    if skipped:
        print("Status:   SKIPPED")
        print(f"Reason:   {skip_reason}")
    else:
        status = "PASS" if returncode == 0 else "FAIL"
        print(f"Status:   {status} (exit code {returncode})")
        if parsed_summary:
            print(
                "Summary:  "
                f"{parsed_summary['passed']} passed, "
                f"{parsed_summary['failed']} failed, "
                f"{parsed_summary['total']} total"
            )

    print("Output:")
    rendered_output = output.rstrip() or "<no output>"
    for line in rendered_output.splitlines():
        print(f"  {line}")
    print()


def print_overall_summary(results):
    print_header("Overall Test Summary")
    headers = ("Suite", "Status", "Passed", "Failed", "Total", "Duration")
    rows = []
    aggregate_passed = 0
    aggregate_failed = 0
    aggregate_total = 0

    for result in results:
        summary = result.get("summary") or {}
        passed = summary.get("passed", "-")
        failed = summary.get("failed", "-")
        total = summary.get("total", "-")
        status = result["status"]
        rows.append(
            (
                result["name"],
                status,
                str(passed),
                str(failed),
                str(total),
                format_duration(result["duration"]),
            )
        )
        if isinstance(passed, int):
            aggregate_passed += passed
        if isinstance(failed, int):
            aggregate_failed += failed
        if isinstance(total, int):
            aggregate_total += total

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(values):
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))

    print_rule("-")
    print(
        "Combined totals: "
        f"{aggregate_passed} passed, {aggregate_failed} failed, {aggregate_total} total"
    )

    failed_suites = [result for result in results if result["status"] == "FAIL"]
    skipped_suites = [result for result in results if result["status"] == "SKIPPED"]
    if failed_suites:
        print("Failing suites: " + ", ".join(result["name"] for result in failed_suites))
    if skipped_suites:
        print("Skipped suites: " + ", ".join(result["name"] for result in skipped_suites))


def run_suite(suite):
    start = time.perf_counter()
    completed = subprocess.run(
        suite["command"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - start
    combined_output = completed.stdout
    if completed.stderr:
        combined_output = f"{combined_output}\n{completed.stderr}".strip()

    parsed_summary = parse_summary(combined_output)
    return {
        "name": suite["name"],
        "command": suite["command"],
        "duration": duration,
        "returncode": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "output": combined_output,
        "summary": parsed_summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run all project tests and print a combined summary."
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip api_smoke_test.py when the FastAPI server is not running.",
    )
    args = parser.parse_args()

    print_header("Co-Stars Backend Test Runner")
    print("This runner preserves the existing standalone test scripts and adds one combined report.")
    print()

    results = []
    for suite in TEST_SUITES:
        if args.skip_smoke and suite["requires_server"]:
            result = {
                "name": suite["name"],
                "command": suite["command"],
                "duration": 0.0,
                "returncode": None,
                "status": "SKIPPED",
                "output": "Smoke test skipped by --skip-smoke.",
                "summary": None,
            }
            print_suite_output(
                suite["name"],
                suite["command"],
                result["duration"],
                0,
                result["output"],
                None,
                skipped=True,
                skip_reason="Requires a running FastAPI server at http://localhost:8000.",
            )
            results.append(result)
            continue

        result = run_suite(suite)
        print_suite_output(
            suite["name"],
            suite["command"],
            result["duration"],
            result["returncode"],
            result["output"],
            result["summary"],
        )
        results.append(result)

    print_overall_summary(results)

    if any(result["status"] == "FAIL" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())