# Agent & Workflow Instructions: static_website_builder

## Project Architecture & Directory Layout
- **`static_website_builder`**: Public codebase for the static site generator engine (`aqui_brain_dump` Python package).
- **`aquiles.me`** (Sibling directory: `../aquiles.me`): Contains the actual digital garden content files (`content/`), HTML templates (`templates/`), static assets (`static/`), and compiled site output (`output/`).

## Virtual Environment & Tooling
- Python virtual environment is managed using **`uv`**.
- Dependencies and scripts should be executed using `uv run` (e.g., `uv run brain_dump`, `uv run python -m ...`, `uv run pytest`).

## Execution & Garden Building
- To compile the digital garden (`aquiles.me`):
  - Working directory: `/Users/aquiles/Documents/Web/aquiles.me`
  - Command: `uv run --project ../static_website_builder brain_dump` (or `uv run brain_dump` if editable install is active in `aquiles.me`).
- Main entry points defined in `pyproject.toml`:
  - `brain_dump`: `aqui_brain_dump.__main__:main`
  - `garden_tools`: `aqui_brain_dump.garden_tools:main`

## Autonomous & Interaction Rules
1. **Separation of Concerns**: Do not store garden content files inside `static_website_builder`. Code belongs here; content belongs in `../aquiles.me`.
2. **Environment**: Always use `uv` for python commands in this project.
3. **Verification**: When editing engine logic, verify changes by compiling the garden in `../aquiles.me` using `uv run` and testing/inspecting the resulting HTML/XML output.
