from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlparse

import yaml

DEFAULT_OUTPUTS = {
    "publication": Path(__file__).resolve().parents[1] / "_data" / "publications.yml",
    "activity": Path(__file__).resolve().parents[1] / "_data" / "activities.yml",
}

PUBLICATION_FIELDS = ("title", "authors", "venue", "year", "url")
ACTIVITY_FIELDS = ("title", "date", "type", "venue", "description", "url")
DATE_RANGE_SEPARATOR = "〜"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WHITESPACE_PATTERN = re.compile(r"\s+")


def load_entries(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(content)
    if loaded is None:
        return []
    if not isinstance(loaded, list):
        raise ValueError("Top-level YAML value must be a list")
    return [dict(entry) for entry in loaded]


def normalize_publication(values: Mapping[str, str]) -> dict:
    entry = {
        "title": _required_string(values, "title"),
        "authors": _required_string(values, "authors"),
        "venue": _required_string(values, "venue"),
        "year": _parse_year(values.get("year", "")),
        "url": _optional_url(values.get("url", "")),
    }
    return entry


def normalize_activity(values: Mapping[str, str]) -> dict:
    entry = {
        "title": _required_string(values, "title"),
        "date": _parse_activity_date(values.get("date", "")),
        "type": _required_string(values, "type"),
        "venue": _optional_string(values.get("venue", "")),
        "description": _optional_string(values.get("description", "")),
        "url": _optional_url(values.get("url", "")),
    }
    return entry


def validate_entry(kind: str, entry: Mapping[str, object], existing: Sequence[Mapping[str, object]]) -> None:
    if kind not in DEFAULT_OUTPUTS:
        raise ValueError(f"Unsupported entry kind: {kind}")

    candidate_key = _duplicate_key(kind, entry)
    for current in existing:
        if _duplicate_key(kind, current) == candidate_key:
            raise ValueError(f"Duplicate {kind} entry")


def append_entry(path: Path, entry: Mapping[str, object]) -> None:
    original = path.read_text(encoding="utf-8")
    addition = yaml.safe_dump([dict(entry)], allow_unicode=True, sort_keys=False, width=1000)

    if original.strip() == "[]":
        updated = addition
    elif not original.strip():
        updated = addition
    else:
        separator = "" if original.endswith("\n") else "\n"
        updated = f"{original}{separator}{addition}"

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_file = Path(handle.name)
            handle.write(updated)
        os.replace(temp_file, path)
    except Exception:
        if temp_file is not None and temp_file.exists():
            temp_file.unlink()
        raise


def add_entry(kind: str, values: Mapping[str, str], output_path: Path) -> dict:
    existing = load_entries(output_path)
    if kind == "publication":
        entry = normalize_publication(values)
    elif kind == "activity":
        entry = normalize_activity(values)
    else:
        raise ValueError(f"Unsupported entry kind: {kind}")
    validate_entry(kind, entry, existing)
    append_entry(output_path, entry)
    return entry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="kind", required=True)

    publication = subparsers.add_parser("publication")
    publication.add_argument("--title", required=True)
    publication.add_argument("--authors", required=True)
    publication.add_argument("--venue", required=True)
    publication.add_argument("--year", required=True)
    publication.add_argument("--url", default="")
    publication.add_argument("--output", type=Path, default=DEFAULT_OUTPUTS["publication"])

    activity = subparsers.add_parser("activity")
    activity.add_argument("--title", required=True)
    activity.add_argument("--date", required=True)
    activity.add_argument("--type", required=True)
    activity.add_argument("--venue", default="")
    activity.add_argument("--description", default="")
    activity.add_argument("--url", default="")
    activity.add_argument("--output", type=Path, default=DEFAULT_OUTPUTS["activity"])

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    values = vars(args).copy()
    kind = values.pop("kind")
    output_path = values.pop("output")

    try:
        entry = add_entry(kind, values, output_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(entry, ensure_ascii=False))
    return 0


def _required_string(values: Mapping[str, str], key: str) -> str:
    value = _optional_string(values.get(key, ""))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _optional_string(value: str) -> str:
    return str(value).strip()


def _parse_year(value: str) -> int:
    stripped = _required_string({"year": value}, "year")
    if not stripped.isdigit() or len(stripped) != 4:
        raise ValueError("year must be a 4-digit integer")
    return int(stripped)


def _parse_activity_date(value: str) -> str:
    stripped = _required_string({"date": value}, "date")
    if DATE_RANGE_SEPARATOR in stripped:
        start_text, end_text = stripped.split(DATE_RANGE_SEPARATOR, 1)
        start = _parse_single_date(start_text)
        end = _parse_single_date(end_text)
        if start > end:
            raise ValueError("activity date range must not be reversed")
        return f"{start.strftime('%Y-%m-%d')}{DATE_RANGE_SEPARATOR}{end.strftime('%Y-%m-%d')}"
    _parse_single_date(stripped)
    return stripped


def _parse_single_date(value: str) -> datetime:
    if not DATE_PATTERN.match(value):
        raise ValueError("date must be YYYY-MM-DD or YYYY-MM-DD〜YYYY-MM-DD")
    return datetime.strptime(value, "%Y-%m-%d")


def _optional_url(value: str) -> str:
    stripped = _optional_string(value)
    if not stripped:
        return ""
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be an absolute http or https URL")
    return stripped


def _duplicate_key(kind: str, entry: Mapping[str, object]) -> tuple[object, object]:
    title = _normalize_title(entry.get("title", ""))
    if kind == "publication":
        return title, _coerce_year(entry.get("year"))
    return title, _coerce_date(entry.get("date"))


def _normalize_title(value: object) -> str:
    return WHITESPACE_PATTERN.sub(" ", str(value).strip()).casefold()


def _coerce_year(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text.isdigit():
        raise ValueError("year must be a 4-digit integer")
    return int(text)


def _coerce_date(value: object) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
