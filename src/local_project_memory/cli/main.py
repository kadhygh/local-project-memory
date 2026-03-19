from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from local_project_memory.domain.models import RecallRequest
from local_project_memory.indexer.project_index import ProjectIndexer
from local_project_memory.services.recall import RecallService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lpm",
        description="CLI for local-project-memory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index a local project.")
    _add_project_args(index_parser)
    index_parser.add_argument("--scope", help="Override the default project scope.")
    index_parser.add_argument("--json", action="store_true", help="Print JSON output.")

    search_parser = subparsers.add_parser(
        "search",
        help="Index a project in-process and run a recall query.",
    )
    _add_project_args(search_parser)
    search_parser.add_argument("--scope", help="Override the default project scope.")
    search_parser.add_argument("--query", required=True, help="Recall query.")
    search_parser.add_argument("--top-k", type=int, default=5, help="Maximum results to return.")
    search_parser.add_argument("--json", action="store_true", help="Print JSON output.")

    return parser


def _add_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-id", required=True, help="Logical project identifier.")
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root directory. Defaults for docs and Unity roots are resolved from here.",
    )
    parser.add_argument("--docs-root", help="Optional override for the docs root.")
    parser.add_argument("--unity-root", help="Optional override for the Unity project root.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "index":
        return _run_index(args)

    if args.command == "search":
        return _run_search(args)

    parser.error(f"Unsupported command: {args.command}")
    return 2


def run() -> None:
    raise SystemExit(main())


def _run_index(args: argparse.Namespace) -> int:
    result = ProjectIndexer().index_project(
        project_root=Path(args.project_root),
        project_id=args.project_id,
        docs_root=Path(args.docs_root) if args.docs_root else None,
        unity_root=Path(args.unity_root) if args.unity_root else None,
        scope=args.scope,
    )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 0

    print(f"project_id: {result.project_id}")
    print(f"docs_chunks: {result.docs_chunks}")
    print(f"code_chunks: {result.code_chunks}")
    print(f"config_chunks: {result.config_chunks}")
    print(f"upserted: {result.upserted}")
    return 0


def _run_search(args: argparse.Namespace) -> int:
    index_result = ProjectIndexer().index_project(
        project_root=Path(args.project_root),
        project_id=args.project_id,
        docs_root=Path(args.docs_root) if args.docs_root else None,
        unity_root=Path(args.unity_root) if args.unity_root else None,
        scope=args.scope,
    )

    response = RecallService().recall(
        RecallRequest(
            project_id=args.project_id,
            query=args.query,
            top_k=args.top_k,
        )
    )

    payload = {
        "project_id": args.project_id,
        "query": args.query,
        "indexed": asdict(index_result),
        "results": [result.model_dump(mode="json") for result in response.results],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"project_id: {args.project_id}")
    print(f"query: {args.query}")
    print(f"indexed_upserted: {index_result.upserted}")
    print(f"results: {len(response.results)}")
    for result in response.results:
        print(f"- [{result.source_kind}] {result.citation} score={result.score} {result.title}")
    return 0