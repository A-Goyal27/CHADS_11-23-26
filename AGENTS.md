# Project instructions

## Purpose
This repository is a reusable Python research template. Develop and test
analysis code using synthetic data only.

## Data boundary
- Do not access, read, copy, upload, or process private data from any organization. If you think it is borderline, consult user first.
- Do not search outside this repository for research datasets.
- Use invented synthetic examples, never samples derived from private records.
- Keep credentials, private data paths, and sensitive outputs out of code,
  notebooks, logs, and Git history.
- If a task requires private data, stop that part of the task and explain
  what can be developed or tested using synthetic data instead.
- If private information is ever noticed where it shouldn't be, report immediately.

## Project structure
- Store Git repositories under Research/projects/<project-name>.
- Reserve Research/private-data/<project-name> for private inputs and outputs;
  this location does not authorize access to private data.
- Keep private results, notebook outputs, and logs outside the repository.
- Clear notebook outputs before saving notebooks in the repository.
- src/: reusable Python analysis code.
- tests/: automated tests using synthetic inputs.
- notebooks/: exploratory analysis and demonstrations.
- synthetic_data/: clearly labeled synthetic examples and fixtures.
- do not work in research-template unless specifically asked. If unsure, clarify which parent folder to work in

## Python environment
- Use the repository's .venv environment.
- Create a separate .venv for each new project with py -m venv .venv.
- On Windows, use .\.venv\Scripts\python.exe when the environment is not activated.
- PowerShell activation is optional.
- Install recorded dependencies with:
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
- Keep requirements.txt consistent with intentional dependency changes.
- Do not commit .venv or hard-code machine-specific paths.

## Development
- Keep changes focused on the requested task.
- Put reusable logic in src/ so notebooks can stay concise.
- Use relative or configurable paths.
- Use explicit random seeds when reproducible synthetic examples are needed.
- Document assumptions, units, missing-data handling, and statistical choices.
- Do not present synthetic results as real research findings.

## Validation and reporting
- Add or update meaningful tests when analysis behavior changes.
- Run relevant tests using:
  .\.venv\Scripts\python.exe -m pytest
- If there are no tests, report that explicitly; do not claim tests passed.
- Summarize changed files, checks performed, and any remaining limitations.
- Update README.md when setup or usage changes.
