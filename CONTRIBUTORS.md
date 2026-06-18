# Contributors Guide

Getting started with the **web-panel** project.

## Quick Start

```bash
git clone https://github.com/Apkawa/web-panel.git
cd web-panel
uv sync
uv run web-panel
```

Open <http://localhost:8502> in your browser.

## Development Checklist

| Step | Command | Description |
| --- | --- | --- |
| Run tests | `uv run pytest` | Execute the test suite |
| Install hooks | `uv run pre-commit install` | Enable pre-commit checks |
| Lint & format | `uv run poe check` + `uv run poe format` | Ruff linting and formatting |
| Type check | `uv run poe types` | mypy strict mode |

## Before Submitting

1. Ensure all tests pass (`uv run pytest`).
2. Run pre-commit hooks (`pre-commit run --all-files`).
3. Verify typing (`uv run poe types`).
