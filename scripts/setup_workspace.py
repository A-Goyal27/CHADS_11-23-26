"""Generate a VS Code workspace without accessing the selected data folder."""

import json
import ntpath
import os
from pathlib import Path, PureWindowsPath


def workspace_config(repository, data_folder, destination):
    """Build configuration from absolute paths, using no filesystem operations."""
    path_module = ntpath if isinstance(repository, PureWindowsPath) else os.path

    def folder_path(folder):
        try:
            return path_module.relpath(str(folder), str(destination.parent))
        except ValueError:  # Windows paths on different drives cannot be relative.
            return str(folder)

    return {"folders": [
        {"name": "project", "path": folder_path(repository)},
        {"name": "private-data", "path": folder_path(data_folder)},
    ]}


def absolute_path(value, base):
    """Normalize a path lexically; never resolve or inspect the data folder."""
    path = Path(value).expanduser()
    return Path(os.path.abspath(path if path.is_absolute() else base / path))


def write_workspace(destination, config, repository, overwrite=False):
    """Write outside the repository; require explicit permission to replace a file."""
    destination = destination.resolve()
    if destination == repository or repository in destination.parents:
        raise ValueError("The workspace file must be outside the repository.")
    if destination.suffix != ".code-workspace":
        raise ValueError("The destination must end in .code-workspace.")
    with destination.open("w" if overwrite else "x", encoding="utf-8") as stream:
        stream.write(json.dumps(config, indent=2) + "\n")


def prompt_paths(repository, input_fn=input):
    """Collect paths separately from configuration generation and writing."""
    filename = repository.name + "-private-analysis.code-workspace"
    if repository.parent.name.lower() == "projects":
        research = repository.parent.parent
        destination = research / filename
        suggestion = research / "private-data" / repository.name
        answer = input_fn(f"Private-data folder [{suggestion}]: ").strip()
        data_folder = absolute_path(answer, research) if answer else suggestion
    else:
        answer = input_fn("Workspace destination (.code-workspace file, required): ").strip()
        if not answer:
            raise ValueError("A workspace destination is required for this layout.")
        destination = absolute_path(answer, repository)
        answer = input_fn("Private-data folder path (required): ").strip()
        if not answer:
            raise ValueError("A data-folder path is required for this layout.")
        data_folder = absolute_path(answer, repository)
    return destination, data_folder


def main():
    repository = Path(__file__).resolve().parent.parent
    try:
        destination, data_folder = prompt_paths(repository)
        destination = destination.resolve()
        config = workspace_config(repository, data_folder, destination)
        try:
            write_workspace(destination, config, repository)
        except FileExistsError:
            answer = input("Workspace already exists. Overwrite? Type yes to confirm: ")
            if answer.strip().lower() != "yes":
                print("Cancelled; existing workspace unchanged.")
                return 0
            write_workspace(destination, config, repository, overwrite=True)
    except (OSError, ValueError, EOFError) as error:
        print(f"Workspace not generated: {error}")
        return 1
    print(f"Workspace saved: {destination}")
    print("Open this workspace in Private Analysis and verify AI extensions are disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
