# code-check

A centralized code quality checker that can scan multiple repositories and store timestamped reports.

## Project Structure

- `checker.py` - Main script for cloning repos, scanning source files, and generating JSON/Markdown reports.
- `config.json` - Repository list and report directory configuration.
- `reports/` - Generated reports are stored here.
- `.gitignore` - Ignores generated reports and Python temporary files.

## Usage

### Scan multiple repos from config

```bash
python checker.py
```

### Scan a single repo

```bash
python checker.py https://github.com/username/repo.git
```

### Scan a single repo with a custom name

```bash
python checker.py https://github.com/username/repo.git my-custom-name
```

## Example `config.json`

```json
{
  "reports_dir": "reports",
  "repositories": [
    {
      "name": "my-frontend-app",
      "url": "https://github.com/yourusername/frontend-app.git"
    },
    {
      "name": "backend-service",
      "url": "https://github.com/yourusername/backend-service.git"
    },
    {
      "name": "mobile-app",
      "url": "https://github.com/yourusername/react-native-app.git"
    }
  ]
}
```

> Note: The example URLs above are placeholders. Replace them with real repository URLs before running `python checker.py`.

## Notes

- The scanner currently targets JavaScript/TypeScript files under `src`, `lib`, `app`, `client/src`, or `frontend/src`.
- Reports are written as both JSON and Markdown for automation and human review.
- Add repo URLs to `config.json` and run `python checker.py` to generate reports.

## GitHub Actions Workflow

This repository includes a workflow at `.github/workflows/scan.yml` that can scan any repo URL via `workflow_dispatch`.

To run it manually from GitHub:

1. Open the Actions tab.
2. Select `Code Quality Scan`.
3. Choose `Run workflow`.
4. Provide `repo_url` and optionally `repo_name`.

The workflow will clone the target repository and generate a report using `checker.py`.
