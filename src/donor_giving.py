"""Summarize gift CSVs; development and tests use synthetic data only."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import re


REQUIRED_COLUMNS = (
    "FIRST_NAME", "LAST_NAME", "SALUTATION", "EMAIL", "ADDRESS", "CITY",
    "STATE", "ZIP", "AMOUNT", "GIFT_DATE", "DONOR_ID",
)
MONEY = re.compile(r"[+-]?\$?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?\Z")


def _amount(value, row_number):
    value = value.strip()
    if not MONEY.fullmatch(value):
        raise ValueError(f"Row {row_number}: invalid AMOUNT.")
    try:
        return Decimal(value.replace("$", "").replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"Row {row_number}: invalid AMOUNT.") from None


def _date(value, row_number, date_format):
    formats = (date_format,) if date_format else ("%Y-%m-%d", "%m/%d/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Row {row_number}: invalid GIFT_DATE.")


def aggregate_gifts(input_path, *, date_format=None):
    """Return (original headers, sorted donor rows), retaining latest-row details.

    IDs are trimmed text keys. All gifts count, including repeats and negatives.
    Amounts must have at most two decimal places and use a single currency.
    Equal gift dates select the last input row, including its blank fields.
    """
    donors = {}
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)):
            raise ValueError("Input requires unique column headers.")
        if not set(REQUIRED_COLUMNS).issubset(headers):
            raise ValueError("Input is missing required columns.")
        for number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {number}: column count does not match header.")
            donor_id = row["DONOR_ID"].strip()
            if not donor_id:
                raise ValueError(f"Row {number}: blank DONOR_ID.")
            amount = _amount(row["AMOUNT"], number)
            date = _date(row["GIFT_DATE"], number, date_format)
            row["DONOR_ID"] = donor_id
            if donor_id not in donors:
                donors[donor_id] = [amount, date, row]
            else:
                donor = donors[donor_id]
                # Keep addition exact even when inputs exceed Decimal's default precision.
                with localcontext() as context:
                    context.prec = max(len(donor[0].as_tuple().digits),
                                       len(amount.as_tuple().digits)) + 4
                    donor[0] += amount
                if date >= donor[1]:
                    donor[1:] = [date, row]
    ordered = sorted(donors.items())
    ordered.sort(key=lambda item: item[1][0], reverse=True)
    rows = []
    for _, (total, _, row) in ordered:
        result = row.copy()
        result["AMOUNT"] = format(total, ".2f")
        rows.append(result)
    return headers, rows


def write_summaries(input_path, all_output=None, top_output=None, *, date_format=None,
                    overwrite=False):
    """Validate input and destinations, then write all donors and the top 100."""
    source = Path(input_path).resolve()
    outputs = [
        Path(all_output).resolve() if all_output is not None
        else source.with_name(f"{source.stem}_all_donors.csv"),
        Path(top_output).resolve() if top_output is not None
        else source.with_name(f"{source.stem}_top_100.csv"),
    ]
    if source in outputs or outputs[0] == outputs[1]:
        raise ValueError("Input and both output paths must be different.")
    for output in outputs:
        if output.exists() and not overwrite:
            raise ValueError("Output already exists; use --overwrite to replace it.")
        if not output.parent.is_dir() or output.is_dir():
            raise ValueError("Output requires an existing parent directory and a file path.")
    headers, rows = aggregate_gifts(source, date_format=date_format)
    for output, selected in zip(outputs, (rows, rows[:100])):
        with output.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(selected)
    return len(rows), min(100, len(rows))
