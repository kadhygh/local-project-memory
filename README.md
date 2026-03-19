# local-project-memory

`local-project-memory` is a local-first project memory and indexing service for long-lived LLM workflows.

It helps agents and IDE assistants work against real codebases by:

- indexing project documents, code, and selected config files
- returning structured recall results with citations
- storing validated task summaries for reuse across tasks

The current MVP includes:

- a FastAPI service surface
- a storage abstraction with memory and LanceDB backends
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
- LanceDB persistence adapter is available
- retrieval is still keyword-based and not yet hybrid / vector-backed

See [docs/README.md](docs/README.md) for the full documentation map.

See [docs/roadmap/progress.md](docs/roadmap/progress.md) for the current implementation state.

## Quick Start

Install dependencies:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
python -m pytest -q tests/test_api.py tests/test_cli.py tests/test_indexer.py tests/test_lancedb_store.py tests/test_models.py tests/test_project_index.py tests/test_services.py -p no:cacheprovider
```

Run project indexing from the CLI:

```bash
python -m local_project_memory.cli.main index --project-id project-mining --project-root D:\Projects\project_mining --json
```

Run project indexing with LanceDB persistence:

```bash
python -m local_project_memory.cli.main index --project-id project-mining --project-root D:\Projects\project_mining --storage-backend lancedb --lancedb-uri data\project-mining-lancedb --json
```

Query an existing LanceDB-backed index without re-indexing:

```bash
python -m local_project_memory.cli.main search --project-id project-mining --project-root D:\Projects\project_mining --storage-backend lancedb --lancedb-uri data\project-mining-lancedb --query "UnityGatewayAgent" --no-index --json
```

Note: the `search` command only works across separate processes when using the LanceDB backend. The default in-memory backend still requires indexing and searching in the same process.

## Next Major Steps

- evolve recall from keyword scoring to hybrid retrieval
- add a user-facing API workflow for project indexing
- run the first full MVP acceptance pass on a real local Unity project