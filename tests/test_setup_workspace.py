"""Use invented paths and temporary directories inside this repository only."""

import importlib.util
import json
from pathlib import Path, PureWindowsPath
import tempfile
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "setup_workspace", ROOT / "scripts" / "setup_workspace.py"
)
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


def test_windows_spaces_and_drives_without_filesystem_access():
    repo = PureWindowsPath("C:/Invented Research/projects/example repo")
    destination = PureWindowsPath("C:/Invented Research/example.code-workspace")
    with patch.object(Path, "stat", side_effect=AssertionError("No inspection")):
        config = setup.workspace_config(repo, PureWindowsPath("D:/invented data/testing"), destination)
    assert config == {"folders": [
        {"name": "project", "path": "projects\\example repo"},
        {"name": "private-data", "path": "D:\\invented data\\testing"},
    ]}


@pytest.mark.parametrize("answer, expected", [("", "example"), ("private-data/testing", "testing")])
def test_expected_layout_prompts_without_inspecting_data(answer, expected):
    repo = ROOT / "tests" / "Invented Research" / "projects" / "example"
    with patch.object(Path, "stat", side_effect=AssertionError("No inspection")):
        destination, data = setup.prompt_paths(repo, lambda prompt: answer)
    assert destination == repo.parent.parent / "example-private-analysis.code-workspace"
    assert data == repo.parent.parent / "private-data" / expected


def test_other_layout_requires_both_paths():
    repo = ROOT / "tests" / "invented-repository"
    answers = iter(["../example.code-workspace", "../invented-inputs"])
    destination, data = setup.prompt_paths(repo, lambda prompt: next(answers))
    assert destination == repo.parent / "example.code-workspace"
    assert data == repo.parent / "invented-inputs"
    with pytest.raises(ValueError):
        setup.prompt_paths(repo, lambda prompt: "")
    answers = iter(["../example.code-workspace", ""])
    with pytest.raises(ValueError):
        setup.prompt_paths(repo, lambda prompt: next(answers))


def test_write_and_overwrite_policy():
    with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
        base = Path(directory)
        repo = base / "repository"
        repo.mkdir()
        destination = base / "example.code-workspace"
        data = base / "invented-inputs"
        config = setup.workspace_config(repo, data, destination)
        setup.write_workspace(destination, config, repo)
        assert json.loads(destination.read_text(encoding="utf-8")) == config
        assert len(config["folders"]) == 2
        assert not data.exists()
        with pytest.raises(FileExistsError):
            setup.write_workspace(destination, {}, repo)
        assert json.loads(destination.read_text(encoding="utf-8")) == config
        setup.write_workspace(destination, config, repo, overwrite=True)
        with pytest.raises(ValueError, match="outside"):
            setup.write_workspace(repo / "bad.code-workspace", config, repo)


@pytest.mark.parametrize("answer, replaced", [("yes", True), ("y", False), ("", False), ("no", False)])
def test_main_requires_explicit_overwrite_confirmation(answer, replaced, capsys):
    with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
        base = Path(directory)
        repo = base / "projects" / "example"
        (repo / "scripts").mkdir(parents=True)
        destination = base / "example-private-analysis.code-workspace"
        destination.write_text("original", encoding="utf-8")
        with patch.object(setup, "__file__", str(repo / "scripts" / "setup_workspace.py")), \
                patch.object(setup, "prompt_paths", return_value=(destination, base / "invented-inputs")), \
                patch("builtins.input", return_value=answer):
            assert setup.main() == 0
        if replaced:
            assert json.loads(destination.read_text(encoding="utf-8"))["folders"][0]["name"] == "project"
            assert "verify AI extensions are disabled" in capsys.readouterr().out
        else:
            assert destination.read_text(encoding="utf-8") == "original"
