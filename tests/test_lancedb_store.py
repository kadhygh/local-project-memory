from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("lancedb")

from local_project_memory.domain.models import IndexUpsertRequest, KnowledgeRecord, RecallRequest, RecordType
from local_project_memory.services.lancedb_store import LanceDbRepository
from local_project_memory.services.recall import RecallService
from local_project_memory.services.store import StoreService


def _record(project_id: str) -> KnowledgeRecord:
    now = datetime.now(UTC)
    return KnowledgeRecord(
        id="ldb-1",
        project_id=project_id,
        scope=f"project:{project_id}",
        type=RecordType.CODE_CHUNK,
        text="UnityGatewayAgent handles gateway requests",
        summary="Gateway agent entrypoint",
        title="UnityGatewayAgent.cs",
        source_kind="code",
        source_path="Assets/Editor/LocalLLMGateway/UnityGatewayAgent.cs",
        source_id="Assets/Editor/LocalLLMGateway/UnityGatewayAgent.cs:UnityGatewayAgent",
        tags=["gateway"],
        importance=0.7,
        confidence=0.8,
        verified=True,
        created_at=now,
        updated_at=now,
        citation="Assets/Editor/LocalLLMGateway/UnityGatewayAgent.cs:13",
    )


def test_lancedb_repository_persists_and_recalls(workspace_tmp_path: Path) -> None:
    uri = workspace_tmp_path / "lancedb_repo"
    repo = LanceDbRepository(uri=uri)
    store = StoreService(repository=repo)
    record = _record("ldb-proj-1")

    upsert = store.upsert(IndexUpsertRequest(project_id="ldb-proj-1", records=[record]))
    assert upsert.upserted == 1

    repo_reopened = LanceDbRepository(uri=uri)
    response = RecallService(repository=repo_reopened).recall(
        RecallRequest(project_id="ldb-proj-1", query="UnityGatewayAgent gateway", top_k=5)
    )

    assert len(response.results) >= 1
    assert response.results[0].source_path.endswith("UnityGatewayAgent.cs")