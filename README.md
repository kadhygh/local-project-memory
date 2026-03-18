# local-project-memory

`local-project-memory` is a local-first project memory and indexing service for long-lived LLM workflows.

It helps agents and IDE assistants work against real codebases by:

- indexing project documents, code, and selected config files
- returning structured recall results with citations
- storing validated task summaries for reuse across tasks

The current MVP includes:

- a FastAPI service surface
- an in-memory storage backend
- Markdown, C#, and config chunking
- keyword-based recall with metadata filters
- project-level indexing for local repositories

## Scope

The project is not Unity-only. Unity is the first real validation target, but the service is intended to evolve into a general local project memory layer for any codebase that benefits from:

- project knowledge recall
- cross-task memory
- source-grounded citations
- reduced blind search during development work

## Repository Layout

```text
docs/
  design/
  research/
  roadmap/
  validation/
src/local_project_memory/
tests/
```

## Current Status

- MVP indexing and recall loop is working
- real-project smoke check has been run against `project_mining`
- storage is still in-memory
- LanceDB integration is not yet implemented

See [`docs/roadmap/progress.md`](docs/roadmap/progress.md) for the current implementation state.

## Quick Start

Install dependencies:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
python -m pytest -q tests/test_api.py tests/test_indexer.py tests/test_models.py tests/test_project_index.py tests/test_services.py -p no:cacheprovider
```

## Next Major Steps

- add a user-facing indexing command or API workflow
- introduce a LanceDB-backed storage adapter
- run the first full MVP acceptance pass on a real local Unity project
