"""Keep the first CSV row per DONOR_ID. Run from any working directory."""

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from csv_deduplicate import write_deduplicated


def main():
    parser = argparse.ArgumentParser(description="Remove duplicate DONOR_IDs, keeping the first row in file order.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path,
                        help="Default: <input-name>_deduplicated.csv beside input")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        write_deduplicated(args.input, args.output, overwrite=args.overwrite)
    except (OSError, UnicodeError, csv.Error):
        parser.exit(2, "Error: Unable to read or write CSV files. Check paths, encoding, and CSV syntax.\n")
    except ValueError as error:
        parser.exit(2, f"Error: {error}\n")
    print("Wrote deduplicated CSV.")


if __name__ == "__main__":
    main()
