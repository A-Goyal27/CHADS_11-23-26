"""CSV deduplication by DONOR_ID, retaining the first complete row."""

import csv
from pathlib import Path


def write_deduplicated(input_path, output_path=None, *, overwrite=False):
    """Write unique rows and return (rows read, rows kept).

    Keep the first occurrence of each trimmed text DONOR_ID in input order,
    preserving that entire row unchanged. Blank IDs are errors; leading zeros
    remain significant. Unique rows are held in memory. Validate the complete
    input before opening the output; an I/O failure during writing may leave a
    partial output. Symlink inputs default to an output beside their target.
    """
    source = Path(input_path).resolve()
    output = (Path(output_path).resolve() if output_path is not None
              else source.with_name(f"{source.stem}_deduplicated.csv"))
    if output == source or (output.exists() and source.samefile(output)):
        raise ValueError("Input and output must be different files.")
    if not output.parent.is_dir() or output.is_dir():
        raise ValueError("Output requires an existing parent directory and a file path.")
    if output.exists() and not overwrite:
        raise ValueError("Output already exists; use --overwrite to replace it.")

    seen = set()
    rows = []
    count = 0
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        headers = next(reader, None)
        if not headers or any(not header.strip() for header in headers):
            raise ValueError("Input requires nonblank column headers.")
        if headers.count("DONOR_ID") != 1:
            raise ValueError("Input requires exactly one DONOR_ID column.")
        donor_column = headers.index("DONOR_ID")
        for number, row in enumerate(reader, start=2):
            if len(row) != len(headers):
                raise ValueError(f"Row {number}: column count does not match header.")
            count += 1
            key = row[donor_column].strip()
            if not key:
                raise ValueError(f"Row {number}: blank DONOR_ID.")
            if key not in seen:
                seen.add(key)
                rows.append(row)

    with output.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    return count, len(rows)
