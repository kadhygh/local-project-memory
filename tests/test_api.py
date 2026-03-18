from pathlib import Path

from fastapi.testclient import TestClient

from local_project_memory.api.app import app
from local_project_memory.domain.models import RecordType
from local_project_memory.indexer.pipeline import IndexerPipeline
from local_project_memory.indexer.record_mapper import chunk_candidate_to_record


client = TestClient(app)


def test_api_can_upsert_markdown_chunks_and_recall(workspace_tmp_path: Path) -> None:
    (workspace_tmp_path / "notes.md").write_text(
        "# Acceptance\nThis document defines MVP acceptance.\n\n## Validation\nValidation uses recall.\n",
        encoding="utf-8",
    )

    pipeline = IndexerPipeline()
    chunks = pipeline.build_markdown_chunks(workspace_tmp_path, project_id="api-proj-1")
    records = [chunk_candidate_to_record(chunk).model_dump(mode="json") for chunk in chunks]

    upsert_response = client.post(
        "/v1/index/upsert",
        json={"project_id": "api-proj-1", "records": records},
    )
    assert upsert_response.status_code == 200
    assert upsert_response.json()["upserted"] == 2

    recall_response = client.post(
        "/v1/search/recall",
        json={"project_id": "api-proj-1", "query": "mvp validation", "top_k": 5},
    )
    assert recall_response.status_code == 200
    body = recall_response.json()
    assert len(body["results"]) >= 1
    assert body["results"][0]["source_path"] == "notes.md"
    assert body["results"][0]["citation"].startswith("notes.md:")


def test_api_memory_store_round_trip() -> None:
    store_response = client.post(
        "/v1/memory/store",
        json={
            "project_id": "api-proj-2",
            "task_id": "task-42",
            "scope": "session:task-42",
            "summary": "Confirmed UIRoot is the panel opening entrypoint",
            "related_paths": ["Assets/Scripts/UI/UIRoot.cs"],
            "verified": True,
        },
    )
    assert store_response.status_code == 200
    assert store_response.json()["stored"] is True

    recall_response = client.post(
        "/v1/search/recall",
        json={
            "project_id": "api-proj-2",
            "query": "panel opening entrypoint",
            "scopes": ["session:task-42"],
            "types": [RecordType.TASK_SUMMARY.value],
            "filters": {"verified_only": True, "source_kinds": ["task"]},
            "top_k": 5,
        },
    )
    assert recall_response.status_code == 200
    body = recall_response.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["source_kind"] == "task"
    assert body["results"][0]["next_candidates"] == ["Assets/Scripts/UI/UIRoot.cs"]

