from pathlib import Path

from local_project_memory.domain.models import RecallRequest
from local_project_memory.indexer.project_index import ProjectIndexer
from local_project_memory.services.recall import RecallService


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_project_indexer_indexes_docs_code_and_config(workspace_tmp_path: Path) -> None:
    project_root = workspace_tmp_path / "project_sample"
    docs_root = project_root / "Docs"
    unity_root = project_root / "UnityProject"

    _write(
        docs_root / "readme.md",
        "# Project Docs\nThis system handles mining flow and indexing.\n",
    )
    _write(
        unity_root / "Assets" / "Scripts" / "PlayerController.cs",
        "namespace Demo {\npublic class PlayerController {\n  public void Move() { }\n}\n}\n",
    )
    _write(
        unity_root / "Packages" / "manifest.json",
        "{\n  \"dependencies\": {\n    \"com.unity.textmeshpro\": \"3.0.6\"\n  }\n}\n",
    )
    _write(
        unity_root / "ProjectSettings" / "ProjectSettings.asset",
        "companyName: DemoStudio\nproductName: DemoGame\n",
    )

    indexer = ProjectIndexer()
    result = indexer.index_project(
        project_root=project_root,
        project_id="proj-index-1",
        docs_root=docs_root,
        unity_root=unity_root,
    )

    assert result.docs_chunks >= 1
    assert result.code_chunks >= 1
    assert result.config_chunks >= 1
    assert result.upserted == result.docs_chunks + result.code_chunks + result.config_chunks

    recall = RecallService()
    response = recall.recall(RecallRequest(project_id="proj-index-1", query="PlayerController Move", top_k=5))

    assert len(response.results) >= 1
    assert any(item.source_path.endswith("PlayerController.cs") for item in response.results)


def test_project_indexer_supports_default_roots(workspace_tmp_path: Path) -> None:
    project_root = workspace_tmp_path / "project_default"

    _write(
        project_root / "Docs" / "readme.md",
        "# Default Roots\nDocument indexed via default Docs path.\n",
    )
    _write(
        project_root / "UnityProject" / "Assets" / "A.cs",
        "public class A { }\n",
    )
    _write(
        project_root / "UnityProject" / "Packages" / "manifest.json",
        "{\n  \"dependencies\": {}\n}\n",
    )

    result = ProjectIndexer().index_project(project_root=project_root, project_id="proj-index-2")

    assert result.docs_chunks >= 1
    assert result.code_chunks >= 1
    assert result.config_chunks >= 1

