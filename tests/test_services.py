from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from local_project_memory.domain.models import (
    IndexUpsertRequest,
    KnowledgeRecord,
    MemoryStoreRequest,
    RecallFilters,
    RecallRequest,
    RecordType,
)
from local_project_memory.services.recall import RecallService
from local_project_memory.services.store import StoreService


def _record(*, record_id: str, project_id: str, text: str, summary: str, title: str, source_path: str) -> KnowledgeRecord:
    now = datetime.now(UTC)
    return KnowledgeRecord(
        id=record_id,
        project_id=project_id,
        scope=f"project:{project_id}",
        type=RecordType.CODE_CHUNK,
        text=text,
        summary=summary,
        title=title,
        source_kind="code",
        source_path=source_path,
        source_id=f"{source_path}:symbol",
        created_at=now,
        updated_at=now,
        citation=f"{source_path}:10",
        tags=["ui"],
        importance=0.7,
        confidence=0.8,
        verified=True,
    )


def test_upsert_and_recall_keyword_match() -> None:
    project_id = "proj-recall-001"
    store = StoreService()
    recall = RecallService()

    records = [
        _record(
            record_id="r-1",
            project_id=project_id,
            text="UIRoot opens panel instances",
            summary="UI entrypoint for opening panels",
            title="UIRoot.cs",
            source_path="Assets/Scripts/UI/UIRoot.cs",
        ),
        _record(
            record_id="r-2",
            project_id=project_id,
            text="Monster spawner logic",
            summary="Spawner tick",
            title="MonsterSpawner.cs",
            source_path="Assets/Scripts/Gameplay/MonsterSpawner.cs",
        ),
    ]

    upsert_response = store.upsert(IndexUpsertRequest(project_id=project_id, records=records))
    assert upsert_response.upserted == 2

    response = recall.recall(
        RecallRequest(
            project_id=project_id,
            query="ui panel open entry",
            top_k=2,
        )
    )

    assert len(response.results) >= 1
    assert response.results[0].source_path == "Assets/Scripts/UI/UIRoot.cs"
    assert response.results[0].score > 0


def test_memory_store_can_be_recalled_with_filters() -> None:
    project_id = "proj-recall-002"
    store = StoreService()
    recall = RecallService()

    store.store_task_summary(
        MemoryStoreRequest(
            project_id=project_id,
            task_id="task-1",
            scope="session:task-1",
            summary="Confirmed UIRoot is the panel opening entrypoint",
            related_paths=["Assets/Scripts/UI/UIRoot.cs"],
            verified=True,
        )
    )

    response = recall.recall(
        RecallRequest(
            project_id=project_id,
            query="panel opening entrypoint",
            scopes=["session:task-1"],
            types=[RecordType.TASK_SUMMARY],
            filters=RecallFilters(verified_only=True, source_kinds=["task"]),
            top_k=5,
        )
    )

    assert len(response.results) == 1
    result = response.results[0]
    assert result.type == RecordType.TASK_SUMMARY
    assert result.source_kind == "task"
    assert result.next_candidates == ["Assets/Scripts/UI/UIRoot.cs"]

