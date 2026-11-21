"""Deduplication checks using invented synthetic records only."""

import csv
import importlib.util
from pathlib import Path
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("csv_deduplicate", ROOT / "src/csv_deduplicate.py")
dedup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dedup)


@pytest.fixture
def work():
    with tempfile.TemporaryDirectory(prefix="synthetic_dedup_", dir=ROOT / "tests") as directory:
        yield Path(directory)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.reader(stream))


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_first_donor_row_order_and_quoting(work, encoding):
    source = work / "invented gifts.csv"
    rows = [["DONOR_ID", "note", "empty"], ["001", 'Invented, "name"\nline', ""],
            ["002", "Example", ""], ["001", 'Invented, "name"\nline', ""],
            ["001", "example", ""], ["001", " example", ""],
            ["1", "example", ""], [" 002 ", "Different later details", ""]]
    with source.open("w", encoding=encoding, newline="") as stream:
        csv.writer(stream).writerows(rows)
    original = source.read_bytes()
    assert dedup.write_deduplicated(source) == (7, 3)
    output = work / "invented gifts_deduplicated.csv"
    assert read_rows(output) == [rows[i] for i in [0, 1, 2, 6]]
    assert output.read_bytes().startswith(b"\xef\xbb\xbf")
    assert source.read_bytes() == original


def test_header_only_and_explicit_output(work):
    source = work / "invented.csv"
    source.write_text("DONOR_ID,note\n", encoding="utf-8")
    output = work / "chosen.csv"
    assert dedup.write_deduplicated(source, output) == (0, 0)
    assert read_rows(output) == [["DONOR_ID", "note"]]


@pytest.mark.parametrize("content", ["ID\n001\n", "DONOR_ID,DONOR_ID\n001,002\n",
                                   "DONOR_ID,note\n ,invented\n",
                                   "DONOR_ID,note\n001,first\n,second\n"])
def test_requires_unambiguous_nonblank_donor_ids(work, content):
    source = work / "invented.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="DONOR_ID"):
        dedup.write_deduplicated(source)
    assert not (work / "invented_deduplicated.csv").exists()


@pytest.mark.parametrize("content", ["", "DONOR_ID, \n", "DONOR_ID,note\n001\n",
                                        "DONOR_ID,note\n\n", 'DONOR_ID,note\n001,"unclosed'])
def test_invalid_input_does_not_touch_output(work, content):
    source, output = work / "invented.csv", work / "chosen.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, csv.Error)):
        dedup.write_deduplicated(source, output)
    assert not output.exists()
    output.write_text("existing", encoding="utf-8")
    with pytest.raises((ValueError, csv.Error)):
        dedup.write_deduplicated(source, output, overwrite=True)
    assert output.read_text() == "existing"


def test_destination_guards(work):
    source, output = work / "invented.csv", work / "chosen.csv"
    source.write_text("DONOR_ID\n001\n001\n", encoding="utf-8")
    output.write_text("existing", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        dedup.write_deduplicated(source, output)
    assert output.read_text() == "existing"
    dedup.write_deduplicated(source, output, overwrite=True)
    assert read_rows(output) == [["DONOR_ID"], ["001"]]
    for destination in [source, work / "missing" / "out.csv", work]:
        with pytest.raises(ValueError):
            dedup.write_deduplicated(source, destination, overwrite=True)
    alias = work / "alias.csv"
    alias.hardlink_to(source)
    with pytest.raises(ValueError, match="different files"):
        dedup.write_deduplicated(source, alias, overwrite=True)
    assert source.read_text() == "DONOR_ID\n001\n001\n"


def test_cli_from_another_directory_and_safe_errors(work):
    source = work / "invented gifts.csv"
    source.write_text("DONOR_ID\n001\n001\n", encoding="utf-8")
    command = [str(ROOT / ".venv/Scripts/python.exe"),
               str(ROOT / "scripts/remove_duplicates.py"), str(source)]
    result = subprocess.run(command, cwd=work, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == "Wrote deduplicated CSV.\n"
    assert read_rows(work / "invented gifts_deduplicated.csv") == [["DONOR_ID"], ["001"]]
    result = subprocess.run(command, cwd=work, capture_output=True, text=True)
    assert result.returncode == 2
    assert "--overwrite" in result.stderr
    source.write_text('DONOR_ID\n"invented-secret', encoding="utf-8")
    result = subprocess.run(command + ["--overwrite"], cwd=work, capture_output=True, text=True)
    assert result.returncode == 2
    assert "invented-secret" not in result.stderr
    assert str(work) not in result.stderr

