"""Build a locally reviewed CSV overview; standard library only."""

import argparse
import csv
import math
from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class OverviewError(Exception):
    """A safe, non-data-bearing error for the command line."""


def _kind(value):
    if value.lower() in {"true", "false"}:
        return "boolean"
    if re.fullmatch(r"[+-]?\d+", value):
        return "integer"
    try:
        if math.isfinite(float(value)):
            return "number"
    except (ValueError, OverflowError):
        pass
    return "text or mixed"


def _broad_type(kinds):
    if not kinds:
        return "unknown (no non-missing entries)"
    if kinds <= {"integer", "number"}:
        return "number" if "number" in kinds else "integer"
    return next(iter(kinds)) if len(kinds) == 1 else "text or mixed"


def _cell(text):
    # Encode header characters to prevent Markdown/HTML injection, including newlines.
    return "".join(c if c.isascii() and c.isalnum() else f"&#{ord(c)};" for c in text)


def generate_report(input_path, encoding="utf-8-sig", local_details=False):
    """Read one CSV and return Markdown. No values are retained in the report."""
    try:
        with Path(input_path).open("r", encoding=encoding, newline="") as stream:
            reader = csv.reader(stream, strict=True)
            names = next(reader, None)
            if not names or any(not name.strip() for name in names):
                raise OverviewError("CSV must have a nonempty header for every column.")
            kinds = [set() for _ in names]
            missing = [0 for _ in names]
            count = 0
            for row in reader:
                if len(row) != len(names):
                    raise OverviewError("CSV rows must match the header width.")
                count += 1
                for index, value in enumerate(row):
                    value = value.strip()
                    if not value:
                        missing[index] += 1
                    else:
                        kinds[index].add(_kind(value))
    except OverviewError:
        raise
    except (OSError, UnicodeError, LookupError, csv.Error, ValueError):
        raise OverviewError("Could not read CSV; check format, encoding, and access.") from None

    types = [_broad_type(group) for group in kinds]
    lines = [
        "# LOCAL DRAFT — REVIEW BEFORE SHARING",
        "",
        "Structural information can still be sensitive. This report is not automatically "
        "anonymized or approved for sharing. Human review is required before sharing any "
        "part with an AI assistant or copying it into a repository.",
        "",
        "## Observed structural information",
        "",
        "Aliases follow original column order. Types are tentative lexical inferences, "
        "not variable definitions or meanings.",
        "",
        "| Column alias | Tentative broad type |",
        "| --- | --- |",
    ]
    for index, kind in enumerate(types, 1):
        lines.append(f"| column_{index:03d} | {kind} |")
    if local_details:
        lines += ["", "## LOCAL DETAIL — NOT FOR AUTOMATIC SHARING", "",
                  f"Exact row count (excluding header): {count}", "",
                  "| Alias | Original column name (HTML-escaped) | Missing count | Tentative broad type |",
                  "| --- | --- | --- | --- |"]
        for index, (name, absent, kind) in enumerate(zip(names, missing, types), 1):
            lines.append(f"| column_{index:03d} | {_cell(name)} | {absent} | {kind} |")
    lines += ["", "## User-supplied descriptions", "",
              "Complete only with reviewed, approved information. These descriptions "
              "are separate from observed structure and invented assumptions."]
    for title in ("Research question", "Row meaning", "Variable definitions and units",
                  "Table relationships", "Analysis requirements"):
        lines += ["", f"### {title}", "", ""]
    lines += ["", "## Invented synthetic assumptions", "",
              "Record invented choices explicitly; do not treat them as observations.",
              "", "### Synthetic-data specifications", "", "",
              "## Unresolved questions", "", ""]
    return "\n".join(lines)


def default_output_path(source):
    """Choose a report beside the resolved input CSV."""
    return source.with_name(f"{source.stem}_overview.md")


def validate_paths(input_path, output_path=None, overwrite=False):
    """Resolve links before checking the CLI workflow restrictions."""
    try:
        source = Path(input_path).resolve(strict=True)
        target = (Path(output_path) if output_path
                  else default_output_path(source)).resolve()
        if target.is_relative_to(REPOSITORY_ROOT):
            raise OverviewError("Output must be outside the repository.")
        if target == source or (target.exists() and target.samefile(source)):
            raise OverviewError("Output must not overwrite the input.")
        if target.exists() and not overwrite:
            raise OverviewError("Report exists; use --overwrite to replace it.")
        return source, target
    except (OSError, RuntimeError, ValueError):
        raise OverviewError("Could not validate input and output locations.") from None


def write_report(report, output_path, overwrite=False):
    """Write exactly one location; caller applies its workflow path policy."""
    try:
        with Path(output_path).open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
            stream.write(report)
    except FileExistsError:
        raise OverviewError("Report exists; use --overwrite to replace it.") from None
    except (OSError, UnicodeError):
        raise OverviewError("Could not write report; check output location and access.") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a local CSV draft requiring human review.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", help="Optional destination; defaults to <input-stem>_overview.md beside the resolved CSV.")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--local-details", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        source, target = validate_paths(args.input, args.output, args.overwrite)
        report = generate_report(source, args.encoding, args.local_details)
        write_report(report, target, args.overwrite)
    except OverviewError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
