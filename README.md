# Python Research Template

A general-purpose starting point for developing reusable, reproducible Python research analyses with synthetic data.

## Donor giving summaries

Aggregate a gift-level CSV into two ranked CSVs using the standard-library script
(no additional dependencies). Develop and test with invented synthetic records
only. Real donor files must be handled separately in an authorized environment;
do not place real donor records or results in this repository.

From the repository root, with a synthetic input and existing output directory:

```powershell
.\.venv\Scripts\python.exe .\scripts\aggregate_donors.py .\synthetic_data\invented_gifts.csv
```

The input in this command is a placeholder for a user-created synthetic CSV.
By default, outputs are saved beside the resolved input file as
`invented_gifts_all_donors.csv` and `invented_gifts_top_100.csv`.
Use `--all-output` and/or `--top-output` to override either destination independently.
The script reads UTF-8 CSVs (with or without a BOM) and writes UTF-8 CSVs with a
BOM for Excel. Required headers are `FIRST_NAME`, `LAST_NAME`, `SALUTATION`,
`EMAIL`, `ADDRESS`, `CITY`, `STATE`, `ZIP`, `AMOUNT`, `GIFT_DATE`, and `DONOR_ID`.
Original column order and any additional columns are preserved.

- `DONOR_ID` is the only grouping key. IDs are trimmed text; leading zeros
  remain significant. Blank IDs are errors. Names do not determine identity.
- `AMOUNT` becomes total giving across every input row for that donor. All gifts
  count, including repeated rows and negative amounts. Values must use one
  currency and at most two decimal places. Plain numbers, dollar-prefixed
  values, and correctly grouped thousands separators are supported; CSV values
  containing commas must be quoted. Negative values use a leading minus sign
  (for example, `-12.50` or `-$12.50`). Missing or malformed amounts are errors.
  Decimal arithmetic preserves exact sums; output uses two decimal places.
- All remaining details come together from the row with the latest gift date,
  including any blank fields. Equal dates select the last row in input order.
  `GIFT_DATE` therefore means **most recent gift date**, while `AMOUNT` is the
  total across dates. ZIP codes and other text fields retain leading zeros.
- Default dates are ISO `YYYY-MM-DD` or US `MM/DD/YYYY`. Use
  `--date-format "%d/%m/%Y"` for day/month/year inputs. Missing or invalid dates
  are errors. No date filtering is applied.
- Both outputs sort by total giving descending, then donor ID ascending as
  text. The top output contains at most 100 donors; ties at the cutoff are
  resolved by donor ID. Header-only input produces two header-only outputs.

Input and output paths must differ, destination directories must already exist,
and existing outputs require `--overwrite`. All input rows are validated before
writing. Validation errors report row numbers and field names without donor
values. Writes to the two files are sequential: an operating-system failure
during writing can leave a partial set of outputs. CSV output does not retain
spreadsheet formatting. The script loads the donor summaries into memory.

Reusable functions are in `src/donor_giving.py`. Run the synthetic aggregation
tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_donor_giving.py
```

## Directory structure

Use this Windows folder layout:

```text
Research/
  projects/<project-name>/       # Git repository and project .venv
  private-data/<project-name>/   # Private inputs and outputs; outside Git
```

Keep private results, notebook outputs, and logs outside the repository. Clear notebook outputs before saving or committing notebooks. The private-data location is a storage convention, not permission to access private data: development and testing in this template use synthetic data only. Do not search outside the repository for research datasets, or access, read, copy, upload, or process private data. If a task requires private data, stop that part and explain what can be developed with synthetic data instead.

Within each repository:

- `src/`: Reusable Python code for data processing, analysis, and synthetic data generation.
- `tests/`: Tests for analysis logic, data transformations, and expected input behavior.
- `notebooks/`: Exploratory analyses and explanations that use the shared code in `src/`.
- `synthetic_data/`: Artificial datasets for development, testing, and demonstrations. Keep real datasets out of this directory and repository.

## Private Analysis workspace

After cloning, run from the repository in PowerShell (only standard-library Python is needed):

```powershell
py .\scripts\setup_workspace.py
```

For `Research/projects/<repository-name>`, this saves
`Research/<repository-name>-private-analysis.code-workspace` and prompts for a
data folder, suggesting `Research/private-data/<repository-name>`. You can select
another folder, such as `private-data/testing` (relative to `Research`). The data
folder need not exist; the script does not inspect or create it. With a different
repository layout, both the workspace file destination and data-folder path are
required; relative paths are interpreted from the repository. The destination
parent must already exist, and the workspace must be outside the repository.
An existing workspace is replaced only after you type `yes`.

The workspace has two direct folders, `project` and `private-data`, so the existing
folder-scoped `.vscode/tasks.json` tasks are discovered. The script locates the
repository from its own location, regardless of the terminal's working directory.
It does not open the workspace automatically. Open the generated workspace in
**Private Analysis** and verify AI extensions are disabled. The workspace file
does not select a VS Code profile or disable extensions.

Workspace generation does not create a virtual environment, install dependencies,
modify Codex permissions, or establish private-data access restrictions.

## Python setup on Windows

Run these commands in PowerShell for each new project:

```powershell
cd <path-to-Research>\projects\<project-name>
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- `cd` selects the project repository; replace the placeholders with your folder locations.
- `py -m venv .venv` uses the Windows Python launcher to create an isolated Python environment for this project. Install Python with the launcher available before running it.
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` installs the project's recorded dependencies into that environment. Keep `requirements.txt` consistent with intentional dependency changes.

PowerShell activation is optional. Use `.\.venv\Scripts\python.exe` directly from the repository root to ensure commands use the project's environment. Optionally run `.\.venv\Scripts\Activate.ps1` to activate it, then use `python` in that shell. Do not commit `.venv` or hard-code machine-specific paths.

Run the relevant tests with the project interpreter:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

This runs the automated tests using the project's installed dependencies. If no tests exist, report that explicitly rather than claiming tests passed.

## Intended workflow

1. Create synthetic datasets that represent the expected structure and relevant edge cases of the research inputs. Record generation parameters and random seeds for reproducibility.
2. Explore ideas in `notebooks/`, move reusable logic into `src/`, and validate it with tests in `tests/`.
3. Develop and verify the analysis locally using synthetic data only.
4. Execute the analysis against real datasets only in separately authorized environments, following their access and data-handling requirements. Keep real data, credentials, and sensitive outputs in those environments.

Document dependencies, configuration, and execution steps as analyses are added so others can reproduce the synthetic-data workflow.

Use invented examples, never samples derived from private records. Label synthetic datasets and results clearly; do not present them as real research findings. Document assumptions, units, missing-data handling, and statistical choices, and add meaningful tests when analysis behavior changes. Keep credentials, private data paths, and sensitive outputs out of code, notebooks, logs, and Git history. Report any misplaced private information immediately without copying it into reports.

Use this template to start a separate project under `Research/projects/<project-name>`. Change `research-template` itself only when specifically asked; if the target project is unclear, clarify which folder to use.

## Local data-overview draft

### Run from VS Code

1. Open the project in the **Private Analysis** profile with AI extensions disabled.
2. Choose **Terminal → Run Task**, then **Generate default data overview** or **Generate local-details data overview**. Only the latter includes original column names and exact counts.
3. On each run, enter the full input CSV path **without surrounding quotation marks**. Leave the output prompt blank to save `<input-name>_overview.md` beside the input CSV, or enter a full output Markdown path to choose a destination. Paths containing spaces are supported.
4. Save reports outside the repository, choose an existing destination folder, and review reports before sharing.

The tasks use the repository's `.venv/Scripts/python.exe` directly and retain the script's output-location and overwrite protections. They do not add `--overwrite` or run automatically when the workspace opens. These tasks run using your permissions and do not change Codex access restrictions.

The tasks use `${workspaceFolder}` for the interpreter, script, and working directory. In this folder-level `.vscode/tasks.json`, it resolves to the project folder containing that configuration, so clones and renamed projects need no task edits. In a multi-folder workspace, select the overview task belonging to the intended project folder. Limitation: open each repository root as a VS Code workspace folder (directly or via Add Folder to Workspace); opening only its parent directory does not discover nested task files. Each clone needs its own `.venv` as described above. Keep these tasks in the project?s `.vscode/tasks.json` so their folder scope is preserved.

### Run manually

Run `synthetic_data/build_data_overview.py` manually in your Private Analysis VS Code profile. In PowerShell, from your project repository, replace these placeholders with your authorized locations:

```powershell
.\.venv\Scripts\python.exe synthetic_data\build_data_overview.py --input "<path-to-Research>\private-data\<project-name>\<input.csv>"
```

By default, the draft is saved in the same folder as the resolved input CSV: `input.csv` produces `input_overview.md`. If the input is a symlink, the destination is beside the actual target CSV. Keep the input and report outside the repository. You can still supply `--output "<path-to-Research>\private-data\<project-name>\reports\<draft.md>"` to choose a different destination; create that parent folder first. The script reads only the specified CSV, writes only the selected report, and does not print report contents or data-derived details. Use `--encoding <encoding>` to override `utf-8-sig`, `--overwrite` to replace an existing report, and `--local-details` only when you want original column names, exact row count, missing counts, and tentative types in a clearly marked local section.

The default draft includes ordered neutral column aliases and tentative broad types, with blank sections for approved descriptions and explicitly invented synthetic assumptions. Structural information can still be sensitive: this is not automatic anonymization or approval to share. Review the entire draft before sharing any part with an AI assistant. After review, you may manually copy approved material into `synthetic_data/data_overview.md`. Running in Private Analysis does not protect a report written into the repository.

The CLI resolves paths, including existing symlinks/junctions, rejects output inside this repository, and refuses to overwrite the input (including existing hard-link aliases). This output-location check is a workflow safeguard, not a security boundary; concurrent filesystem changes can invalidate checks. Keep destination paths under your control. Existing reports require `--overwrite`; missing parent directories are not created. The report-writing helper is separately testable and does not apply the CLI path policy.

CSV support is limited to one comma-delimited file with a required header, consistent row widths, and standard CSV quoting. Empty files, blank header cells, malformed quoting, and inconsistent rows are rejected; header-only files are supported. Duplicate headers remain separate ordered columns. Missing means empty or whitespace-only after trimming; tokens such as `NA` or `null` are not treated as missing. Blank lines are rejected as inconsistent rows. Types are lexical guesses across non-missing cells: boolean (`true`/`false`), integer, finite number, text or mixed, or unknown. Numeric-looking identifiers can be misclassified; dates, units, variable meanings, categories, and relationships are not inferred. No ranges, values, sample rows, or category labels are emitted. Local headers are HTML-escaped for Markdown rendering. Disclosure filtering omits listed details but cannot guarantee anonymity; column count, order, and tentative types may themselves reveal information.

Tests use invented temporary CSV fixtures and helper outputs within the repository:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_overview.py
```
