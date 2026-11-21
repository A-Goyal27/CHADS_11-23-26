"""Invented gift records only; no external datasets are accessed."""

import csv
import importlib.util
from pathlib import Path
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("donor_giving", ROOT / "src/donor_giving.py")
giving = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(giving)


@pytest.fixture
def work():
    with tempfile.TemporaryDirectory(prefix="synthetic_giving_", dir=ROOT / "tests") as directory:
        yield Path(directory)


def gift(donor="001", amount="10.00", date="2026-01-01", **details):
    row = dict.fromkeys(giving.REQUIRED_COLUMNS, "")
    row.update(DONOR_ID=donor, AMOUNT=amount, GIFT_DATE=date,
               FIRST_NAME="Invented", LAST_NAME="Example", ZIP="00123")
    row.update(details)
    return row


def write_input(work, rows, headers=giving.REQUIRED_COLUMNS):
    source = work / "synthetic_gifts.csv"
    with source.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    return source


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def test_sums_latest_details_ties_and_text_ids(work):
    source = write_input(work, [
        gift(amount="$1,000.10", ADDRESS="Old invented address"),
        gift(amount="0.20", date="06/01/2026", ADDRESS="New invented address"),
        gift(amount="-2.00", date="06/01/2026", EMAIL="", ADDRESS="Final invented address"),
        gift(donor="002", amount="998.30"),
        gift(donor="003", amount="-5.00"),
    ])
    headers, rows = giving.aggregate_gifts(source)
    assert headers == list(giving.REQUIRED_COLUMNS)
    assert [r["DONOR_ID"] for r in rows] == ["001", "002", "003"]
    assert rows[0]["AMOUNT"] == "998.30"
    assert rows[0]["GIFT_DATE"] == "06/01/2026"
    assert rows[0]["ADDRESS"] == "Final invented address"
    assert rows[0]["EMAIL"] == ""
    assert rows[0]["ZIP"] == "00123"


def test_old_rows_do_not_replace_latest_and_repeats_count(work):
    source = write_input(work, [gift(date="2026-12-01", CITY="Invented City"),
                                gift(), gift()])
    _, rows = giving.aggregate_gifts(source)
    assert rows[0]["CITY"] == "Invented City"
    assert rows[0]["AMOUNT"] == "30.00"


@pytest.mark.parametrize("count", [0, 3, 105])
def test_exports_and_top_limit(work, count):
    source = write_input(work, [gift(donor=f"{n:03}", amount=str(n)) for n in range(count)])
    all_path, top_path = work / "all.csv", work / "top.csv"
    assert giving.write_summaries(source, all_path, top_path) == (count, min(count, 100))
    headers, rows = read_csv(all_path)
    assert headers == list(giving.REQUIRED_COLUMNS)
    assert len(rows) == count
    assert read_csv(top_path)[1] == rows[:100]
    if count:
        assert rows[0]["DONOR_ID"] == f"{count - 1:03}"


@pytest.mark.parametrize("field,value", [
    ("DONOR_ID", "  "), ("AMOUNT", ""), ("AMOUNT", "NaN"),
    ("AMOUNT", "1,00"), ("AMOUNT", "1.001"), ("GIFT_DATE", ""),
    ("GIFT_DATE", "2026-02-30"),
])
def test_invalid_rows_do_not_create_outputs_or_reveal_values(work, field, value):
    source = write_input(work, [gift(**{field: value})])
    outputs = work / "all.csv", work / "top.csv"
    with pytest.raises(ValueError, match=f"Row 2: .*{field}"):
        giving.write_summaries(source, *outputs)
    assert not any(p.exists() for p in outputs)


def test_custom_date_format(work):
    source = write_input(work, [gift(date="31/12/2026")])
    assert giving.aggregate_gifts(source, date_format="%d/%m/%Y")[1][0]["AMOUNT"] == "10.00"
    with pytest.raises(ValueError, match="GIFT_DATE"):
        giving.aggregate_gifts(source)


def test_headers_and_row_shape(work):
    source = write_input(work, [], headers=["DONOR_ID"])
    with pytest.raises(ValueError, match="missing required"):
        giving.aggregate_gifts(source)
    source.write_text("DONOR_ID,DONOR_ID\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        giving.aggregate_gifts(source)
    source = write_input(work, [])
    with source.open("a", encoding="utf-8") as stream:
        stream.write("only_one_field\n")
    with pytest.raises(ValueError, match="column count"):
        giving.aggregate_gifts(source)


def test_column_order_and_extra_columns(work):
    headers = ["EXTRA", *reversed(giving.REQUIRED_COLUMNS)]
    source = write_input(work, [gift(EXTRA="Invented extra")], headers=headers)
    found_headers, rows = giving.aggregate_gifts(source)
    assert found_headers == headers
    assert rows[0]["EXTRA"] == "Invented extra"


def test_overwrite_and_path_protection(work):
    source = write_input(work, [gift()])
    all_path, top_path = work / "all.csv", work / "top.csv"
    all_path.write_text("Keep existing contents", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        giving.write_summaries(source, all_path, top_path)
    assert all_path.read_text() == "Keep existing contents"
    assert not top_path.exists()
    giving.write_summaries(source, all_path, top_path, overwrite=True)
    assert len(read_csv(all_path)[1]) == 1
    for paths in [(source, top_path), (all_path, all_path)]:
        with pytest.raises(ValueError, match="must be different"):
            giving.write_summaries(source, *paths, overwrite=True)


def test_large_amounts_are_exact(work):
    source = write_input(work, [gift(amount="123456789012345678901234567890.10"),
                                gift(amount="0.20")])
    assert giving.aggregate_gifts(source)[1][0]["AMOUNT"] == "123456789012345678901234567890.30"


def test_cli(work):
    import sys
    source = write_input(work, [gift()])
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/aggregate_donors.py"), str(source),
        "--all-output", str(work / "all.csv"), "--top-output", str(work / "top.csv"),
    ], capture_output=True, text=True, cwd=work)
    assert result.returncode == 0, result.stderr
    assert "Wrote 1 donor summaries" in result.stdout


@pytest.mark.parametrize("override", [None, "all", "top"])
def test_cli_default_destinations(work, override):
    import sys
    input_dir = work / "input folder"
    input_dir.mkdir()
    source = write_input(input_dir, [gift()])
    command = [sys.executable, str(ROOT / "scripts/aggregate_donors.py"), str(source)]
    all_path = input_dir / "synthetic_gifts_all_donors.csv"
    top_path = input_dir / "synthetic_gifts_top_100.csv"
    if override:
        custom = work / "custom.csv"
        command.extend([f"--{override}-output", str(custom)])
        if override == "all":
            all_path = custom
        else:
            top_path = custom
    result = subprocess.run(command, capture_output=True, text=True, cwd=work)
    assert result.returncode == 0, result.stderr
    assert len(read_csv(all_path)[1]) == 1
    assert read_csv(top_path) == read_csv(all_path)
    # Existing default outputs retain the same overwrite protection.
    result = subprocess.run(command, capture_output=True, text=True, cwd=work)
    assert result.returncode == 2
    assert "already exists" in result.stderr
