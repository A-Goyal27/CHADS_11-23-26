"""Command-line CSV donor aggregation. Run from any working directory."""

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from donor_giving import write_summaries


def main():
    parser = argparse.ArgumentParser(description="Sum gifts per DONOR_ID and export ranked CSVs.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--all-output", required=True, type=Path)
    parser.add_argument("--top-output", required=True, type=Path)
    parser.add_argument("--date-format", help="Explicit strptime format, e.g. %%d/%%m/%%Y")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        counts = write_summaries(args.input, args.all_output, args.top_output,
                                 date_format=args.date_format, overwrite=args.overwrite)
    except (OSError, UnicodeError, csv.Error):
        # File/decoder/parser errors may expose sensitive paths or contents.
        parser.exit(2, "Error: Unable to read or write CSV files. Check paths, encoding, and CSV syntax.\n")
    except ValueError as error:
        parser.exit(2, f"Error: {error}\n")
    print(f"Wrote {counts[0]} donor summaries and {counts[1]} top-donor summaries.")


if __name__ == "__main__":
    main()
