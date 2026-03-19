from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from local_project_memory.domain.models import KnowledgeRecord, MemoryStoreRequest, RecordType


class LanceDbRepository:
    """Persistent repository backed by a LanceDB table."""

    def __init__(self, uri: str | Path, table_name: str = "knowledge_items") -> None:
        self.uri = str(uri)
        self.table_name = table_name
        self._lock = RLock()
        self._db = None

    def upsert_records(self, records: list[KnowledgeRecord]) -> int:
        if not records:
            return 0

        rows = [self._record_to_row(record) for record in records]

        with self._lock:
            table = self._open_table()
            if table is None:
                table = self._connect().create_table(self.table_name, data=rows, mode="overwrite")
                self._ensure_indexes(table)
                return len(rows)

            if hasattr(table, "merge_insert"):
                try:
                    (
                        table.merge_insert("id")
                        .when_matched_update_all()
                        .when_not_matched_insert_all()
                        .execute(rows)
                    )
                    self._post_upsert(table)
                    return len(rows)
                except Exception:
                    pass

            existing_rows = {row["id"]: row for row in table.to_arrow().to_pylist()}
            for row in rows:
                existing_rows[row["id"]] = row

            table = self._connect().create_table(
                self.table_name,
                data=list(existing_rows.values()),
                mode="overwrite",
            )
            self._ensure_indexes(table)
            return len(rows)

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
        self.upsert_records([record])
        return record

    def list_records(self) -> list[KnowledgeRecord]:
        with self._lock:
            table = self._open_table()
            if table is None:
                return []
            rows = table.to_arrow().to_pylist()
        return [self._row_to_record(row) for row in rows]

    def clear(self) -> None:
        with self._lock:
            db = self._connect()
            try:
                db.drop_table(self.table_name)
            except Exception:
                pass

    def _connect(self):
        if self._db is None:
            import lancedb

            Path(self.uri).mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(self.uri)
        return self._db

    def _open_table(self):
        db = self._connect()
        try:
            return db.open_table(self.table_name)
        except Exception:
            return None

    def _ensure_indexes(self, table) -> None:
        try:
            table.create_scalar_index("id")
        except Exception:
            pass
        self._post_upsert(table)

    def _post_upsert(self, table) -> None:
        try:
            table.optimize()
        except Exception:
            pass

    def _record_to_row(self, record: KnowledgeRecord) -> dict[str, object]:
        return {
            "id": record.id,
            "project_id": record.project_id,
            "scope": record.scope,
            "type": record.type.value,
            "text": record.text,
            "summary": record.summary,
            "title": record.title,
            "source_kind": record.source_kind,
            "source_path": record.source_path,
            "source_id": record.source_id,
            "tags_json": json.dumps(record.tags, ensure_ascii=False),
            "importance": record.importance,
            "confidence": record.confidence,
            "verified": record.verified,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "last_accessed_at": record.last_accessed_at.isoformat() if record.last_accessed_at else None,
            "access_count": record.access_count,
            "line_hint": record.line_hint,
            "citation": record.citation,
            "metadata_json": json.dumps(record.metadata, ensure_ascii=False),
        }

    def _row_to_record(self, row: dict[str, object]) -> KnowledgeRecord:
        return KnowledgeRecord(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            scope=str(row["scope"]),
            type=RecordType(str(row["type"])),
            text=str(row["text"]),
            summary=str(row["summary"]),
            title=str(row["title"]),
            source_kind=str(row["source_kind"]),
            source_path=str(row["source_path"]),
            source_id=str(row["source_id"]),
            tags=json.loads(str(row.get("tags_json") or "[]")),
            importance=float(row.get("importance", 0.5)),
            confidence=float(row.get("confidence", 0.5)),
            verified=bool(row.get("verified", False)),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            last_accessed_at=(
                datetime.fromisoformat(str(row["last_accessed_at"]))
                if row.get("last_accessed_at")
                else None
            ),
            access_count=int(row.get("access_count", 0)),
            line_hint=int(row["line_hint"]) if row.get("line_hint") is not None else None,
            citation=str(row["citation"]),
            metadata=json.loads(str(row.get("metadata_json") or "{}")),
        )