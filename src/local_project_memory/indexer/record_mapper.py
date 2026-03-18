from datetime import UTC, datetime

from local_project_memory.domain.models import KnowledgeRecord, RecordType
from local_project_memory.indexer.pipeline import ChunkCandidate


def chunk_candidate_to_record(
    chunk: ChunkCandidate,
    *,
    created_at: datetime | None = None,
) -> KnowledgeRecord:
    """Map a pipeline chunk candidate to a KnowledgeRecord."""

    now = created_at or datetime.now(UTC)

    return KnowledgeRecord(
        id=chunk.id,
        project_id=chunk.project_id,
        scope=chunk.scope,
        type=RecordType(chunk.type),
        text=chunk.text,
        summary=chunk.summary,
        title=chunk.title,
        source_kind=chunk.source_kind,
        source_path=chunk.source_path,
        source_id=chunk.source_id,
        created_at=now,
        updated_at=now,
        line_hint=chunk.line_hint,
        citation=chunk.citation,
        metadata=dict(chunk.metadata),
    )

