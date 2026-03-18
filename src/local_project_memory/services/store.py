from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from local_project_memory.domain.models import (
    IndexUpsertRequest,
    IndexUpsertResponse,
    KnowledgeRecord,
    MemoryStoreRequest,
    MemoryStoreResponse,
    RecordType,
)


class InMemoryRepository:
    """Thread-safe in-memory storage shared by store and recall services."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records_by_id: dict[str, KnowledgeRecord] = {}

    def upsert_records(self, records: list[KnowledgeRecord]) -> int:
        with self._lock:
            for record in records:
                self._records_by_id[record.id] = record
            return len(records)

    def store_task_summary(self, request: MemoryStoreRequest) -> KnowledgeRecord:
        now = datetime.now(UTC)
        base_source_id = f"{request.project_id}:{request.task_id}"

        record = KnowledgeRecord(
            id=f"task_{base_source_id}_{uuid4().hex[:8]}",
            project_id=request.project_id,
            scope=request.scope,
            type=RecordType.TASK_SUMMARY,
            text=request.summary,
            summary=request.summary,
            title=f"Task Summary {request.task_id}",
            source_kind="task",
            source_path=f"task://{request.task_id}",
            source_id=base_source_id,
            tags=["task_summary"],
            importance=request.importance,
            confidence=request.confidence,
            verified=request.verified,
            created_at=now,
            updated_at=now,
            last_accessed_at=None,
            access_count=0,
            line_hint=None,
            citation=f"task:{request.task_id}",
            metadata={"related_paths": request.related_paths},
        )

        with self._lock:
            self._records_by_id[record.id] = record

        return record

    def list_records(self) -> list[KnowledgeRecord]:
        with self._lock:
            return list(self._records_by_id.values())

    def clear(self) -> None:
        with self._lock:
            self._records_by_id.clear()


REPOSITORY = InMemoryRepository()


class StoreService:
    """In-memory storage implementation for the MVP scaffold."""

    def upsert(self, request: IndexUpsertRequest) -> IndexUpsertResponse:
        upserted = REPOSITORY.upsert_records(request.records)
        return IndexUpsertResponse(project_id=request.project_id, upserted=upserted)

    def store_task_summary(self, request: MemoryStoreRequest) -> MemoryStoreResponse:
        REPOSITORY.store_task_summary(request)
        return MemoryStoreResponse(project_id=request.project_id, task_id=request.task_id, stored=True)

