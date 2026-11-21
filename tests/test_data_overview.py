"""All fixtures and generated reports stay in temporary repository directories."""

import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_data_overview", ROOT / "synthetic_data" / "build_data_overview.py"
)
overview = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(overview)


@pytest.fixture
def work():
    with tempfile.TemporaryDirectory(prefix="overview_test_", dir=ROOT / "tests") as directory:
        yield Path(directory)


def csv_file(work, contents):
    path = work / "invented_fixture.csv"
    path.write_text(contents, encoding="utf-8-sig")
    return path


def test_default_disclosure_and_types(work):
    source = csv_file(work, "NebulaSecret,DragonLabel,QuartzFlag,VoidField,MixedSecret\n"
                      "987654321,ZEBRA_SYNTHETIC,true,,42\n"
                      "3.75,FICTIONAL_TEXT,false,   ,SYNTHETIC_CATEGORY\n")
    report = overview.generate_report(source)
    for secret in ("NebulaSecret", "DragonLabel", "QuartzFlag", "VoidField", "MixedSecret",
                   "987654321", "ZEBRA_SYNTHETIC", "FICTIONAL_TEXT", "SYNTHETIC_CATEGORY",
                   source.name, str(source)):
        assert secret not in report
    assert "column_001 | number" in report
    assert "column_002 | text or mixed" in report
    assert "column_003 | boolean" in report
    assert "column_004 | unknown (no non-missing entries)" in report
    assert "column_005 | text or mixed" in report
    assert "Tentative broad type" in report
    assert "LOCAL DRAFT — REVIEW BEFORE SHARING" in report
    assert "Exact row count" not in report
    assert "Missing count" not in report
    for section in ("Research question", "Row meaning", "Variable definitions and units",
                    "Table relationships", "Analysis requirements",
                    "Synthetic-data specifications", "Unresolved questions",
                    "Observed structural information", "User-supplied descriptions",
                    "Invented synthetic assumptions"):
        assert section in report


def test_local_details_missing_and_header_escaping(work):
    source = csv_file(work, 'SyntheticName,Other|<x>\nINVENTED_VALUE, \n,7\n')
    report = overview.generate_report(source, local_details=True)
    assert "LOCAL DETAIL — NOT FOR AUTOMATIC SHARING" in report
    assert "Exact row count (excluding header): 2" in report
    assert "SyntheticName | 1 | text or mixed" in report
    assert "Other&#124;&#60;x&#62; | 1 | integer" in report
    assert "INVENTED_VALUE" not in report
    assert "Other|<x>" not in report


@pytest.mark.parametrize("contents", ["", "\n", ",named\n1,2\n", "a,b\n1\n",
                                      "a,b\n1,2,3\n", 'a\n"unterminated'])
def test_empty_and_malformed(work, contents):
    with pytest.raises(overview.OverviewError):
        overview.generate_report(csv_file(work, contents))


def test_header_only_and_encoding(work):
    source = csv_file(work, "InventedHeader\n")
    assert "unknown (no non-missing entries)" in overview.generate_report(source)
    with pytest.raises(overview.OverviewError, match="Could not read CSV"):
        overview.generate_report(source, encoding="invented-invalid-encoding")


def test_write_helper_overwrite(work):
    target = work / "report.md"
    overview.write_report("invented report", target)
    with pytest.raises(overview.OverviewError, match="Report exists"):
        overview.write_report("replacement", target)
    assert target.read_text(encoding="utf-8") == "invented report"
    overview.write_report("replacement", target, overwrite=True)
    assert target.read_text(encoding="utf-8") == "replacement"


@pytest.mark.parametrize("relative", ["report.md", "synthetic_data/report.md",
                                      "tests/../synthetic_data/report.md"])
def test_reject_repository_output(work, relative):
    source = csv_file(work, "Invented\n1\n")
    with pytest.raises(overview.OverviewError, match="outside the repository"):
        overview.validate_paths(source, ROOT / relative, overwrite=True)


def test_resolved_link_output_rejected(work):
    source = csv_file(work, "Invented\n1\n")
    link = work / "linked_directory"
    try:
        link.symlink_to(work, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires unavailable OS privileges")
    with pytest.raises(overview.OverviewError, match="outside the repository"):
        overview.validate_paths(source, link / "report.md")


def test_cli_rejects_repository_and_input_overwrite_without_disclosure(work, capsys):
    source = csv_file(work, "SecretSyntheticName\nDISTINCTIVE_FAKE_VALUE\n")
    before = source.read_bytes()
    for output in (source, work / "report.md"):
        assert overview.main(["--input", str(source), "--output", str(output),
                              "--overwrite"]) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "outside the repository" in captured.err
        assert "SecretSyntheticName" not in captured.err
        assert str(source) not in captured.err
    assert source.read_bytes() == before
    assert not (work / "report.md").exists()


def test_path_policy_existing_report_and_input_alias_without_filesystem_access():
    # Mock resolved path objects to exercise external-path branches without
    # reading or writing anything outside the repository. CLI policy is unchanged.
    source = MagicMock(spec=Path)
    target = MagicMock(spec=Path)
    target.is_relative_to.return_value = False
    target.exists.return_value = True
    target.samefile.return_value = False
    with patch.object(Path, "resolve", side_effect=[source, target]):
        with pytest.raises(overview.OverviewError, match="Report exists"):
            overview.validate_paths("invented-input", "invented-output")
    with patch.object(Path, "resolve", side_effect=[source, target]):
        assert overview.validate_paths("invented-input", "invented-output", True) == (source, target)
    target.samefile.return_value = True
    with patch.object(Path, "resolve", side_effect=[source, target]):
        with pytest.raises(overview.OverviewError, match="must not overwrite the input"):
            overview.validate_paths("invented-input", "invented-output", True)


def test_default_output_name(work):
    source = csv_file(work, "Invented\n1\n").resolve()
    assert overview.default_output_path(source) == work / "invented_fixture_overview.md"
    assert overview.default_output_path(work / "invented.multi.csv") == work / "invented.multi_overview.md"


def test_cli_default_output_still_rejects_repository(work, capsys):
    source = csv_file(work, "Invented\n1\n")
    assert overview.main(["--input", str(source)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "outside the repository" in captured.err
    assert not overview.default_output_path(source).exists()


@pytest.mark.parametrize("output_path", [None, ""])
def test_default_output_uses_resolved_source_without_external_access(output_path):
    source = MagicMock(spec=Path)
    target = MagicMock(spec=Path)
    source.stem = "invented_fixture"
    source.with_name.return_value.resolve.return_value = target
    target.is_relative_to.return_value = False
    target.exists.return_value = False
    with patch.object(Path, "resolve", return_value=source):
        assert overview.validate_paths("invented-input", output_path) == (source, target)
    source.with_name.assert_called_once_with("invented_fixture_overview.md")


