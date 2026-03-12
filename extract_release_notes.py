import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
HEADER_PATTERN = re.compile(r"^## \[(?P<version>[^\]]+)\](?:\s+-\s+.+)?$", re.MULTILINE)


def get_release_notes(version):
    changelog_text = CHANGELOG_FILE.read_text(encoding="utf-8")
    matches = list(HEADER_PATTERN.finditer(changelog_text))

    for index, match in enumerate(matches):
        if match.group("version") != version:
            continue

        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(changelog_text)
        notes = changelog_text[start:end].strip()
        if not notes:
            raise ValueError(f"CHANGELOG.md section for version {version} is empty")
        return notes

    raise ValueError(f"Version {version} was not found in CHANGELOG.md")


def main():
    parser = argparse.ArgumentParser(
        description="Extract the release notes for a semantic version from CHANGELOG.md"
    )
    parser.add_argument("version", help="Version number without the leading v, for example 2.0.0")
    parser.add_argument(
        "--output",
        help="Optional file path to write the extracted notes to",
    )
    args = parser.parse_args()

    notes = get_release_notes(args.version)
    if args.output:
        Path(args.output).write_text(notes + "\n", encoding="utf-8")
    else:
        print(notes)


if __name__ == "__main__":
    main()