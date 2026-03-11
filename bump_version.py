import argparse
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
UNRELEASED_HEADER = "## [Unreleased]"
DEFAULT_UNRELEASED_BODY = "### Added\n- Describe upcoming changes here."


def parse_version(value):
    match = SEMVER_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def increment_version(current_version, bump_kind):
    major, minor, patch = parse_version(current_version)
    if bump_kind == "major":
        return f"{major + 1}.0.0"
    if bump_kind == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    parse_version(bump_kind)
    return bump_kind


def extract_unreleased_body(changelog_text):
    marker_index = changelog_text.find(UNRELEASED_HEADER)
    if marker_index == -1:
        raise ValueError("CHANGELOG.md is missing the Unreleased section")

    after_header = changelog_text[marker_index + len(UNRELEASED_HEADER):]
    next_release_index = after_header.find("\n## [")
    if next_release_index == -1:
        unreleased_body = after_header.strip()
        remainder = ""
    else:
        unreleased_body = after_header[:next_release_index].strip()
        remainder = after_header[next_release_index + 1 :].lstrip("\n")

    if not unreleased_body:
        unreleased_body = DEFAULT_UNRELEASED_BODY

    return unreleased_body, remainder


def update_changelog(new_version):
    changelog_text = CHANGELOG_FILE.read_text(encoding="utf-8")
    before_unreleased, _separator, _after_unreleased = changelog_text.partition(UNRELEASED_HEADER)
    if not _separator:
        raise ValueError("CHANGELOG.md is missing the Unreleased section")

    unreleased_body, remainder = extract_unreleased_body(changelog_text)
    released_section = f"## [{new_version}] - {date.today().isoformat()}\n\n{unreleased_body.strip()}"
    new_changelog = (
        f"{before_unreleased}{UNRELEASED_HEADER}\n\n{DEFAULT_UNRELEASED_BODY}\n\n"
        f"{released_section}"
    )
    if remainder:
        new_changelog = f"{new_changelog}\n\n{remainder.strip()}\n"
    else:
        new_changelog = f"{new_changelog}\n"

    CHANGELOG_FILE.write_text(new_changelog, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Bump the project version and roll the Unreleased changelog section into a dated release entry."
    )
    parser.add_argument(
        "target",
        help="Semantic version bump kind (major, minor, patch) or an explicit version like 1.2.3",
    )
    args = parser.parse_args()

    current_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    parse_version(current_version)
    new_version = increment_version(current_version, args.target)

    VERSION_FILE.write_text(f"{new_version}\n", encoding="utf-8")
    update_changelog(new_version)

    print(f"Version updated: {current_version} -> {new_version}")
    print("CHANGELOG.md promoted the Unreleased section into a dated release entry.")


if __name__ == "__main__":
    main()