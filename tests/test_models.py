from datetime import UTC, datetime

from local_project_memory.domain.models import KnowledgeRecord, RecordType


def test_knowledge_record_can_be_created() -> None:
    now = datetime.now(UTC)
    record = KnowledgeRecord(
        id="ki_1",
        project_id="sample-project",
        scope="project:sample-project",
        type=RecordType.DOC_CHUNK,
        text="sample text",
        summary="sample summary",
        title="Sample",
        source_kind="document",
        source_path="Docs/Sample.md",
        source_id="Docs/Sample.md#intro",
        created_at=now,
        updated_at=now,
        citation="Docs/Sample.md:1",
    )

    assert record.project_id == "sample-project"
    assert record.type is RecordType.DOC_CHUNK

