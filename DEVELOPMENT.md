# Development Guide

## Project Setup & Environment

This project uses [`uv`](https://github.com/astral-sh/uv) to manage Python dependencies and virtual environments.

### Setting Up Environment
```bash
uv sync
```

### Directory Relationship
- **`static_website_builder`** (this directory): Public repository containing the static site generator package (`aqui_brain_dump`).
- **`aquiles.me`** (sibling directory `../aquiles.me`): Private/separate repository containing the Markdown notes, templates, assets, and output directory for the digital garden.

### Compiling the Garden
To test and compile the garden from `aquiles.me`:

```bash
cd ../aquiles.me
uv run --project ../static_website_builder brain_dump
```

Or run `garden_tools` utility scripts:
```bash
uv run --project ../static_website_builder garden_tools
```
