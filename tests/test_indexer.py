from pathlib import Path

from local_project_memory.indexer.pipeline import IndexerPipeline


def test_discover_markdown_is_stable_and_sorted(workspace_tmp_path: Path) -> None:
    (workspace_tmp_path / "b.md").write_text("# B\ntext\n", encoding="utf-8")
    (workspace_tmp_path / "a.md").write_text("# A\ntext\n", encoding="utf-8")
    (workspace_tmp_path / "code.cs").write_text("class A {}", encoding="utf-8")

    pipeline = IndexerPipeline()
    files = pipeline.discover_markdown(workspace_tmp_path)

    assert [f.path.name for f in files] == ["a.md", "b.md"]


def test_markdown_chunking_preserves_order_and_citation(workspace_tmp_path: Path) -> None:
    content = """# Intro
First paragraph line one
still first paragraph

Second paragraph

## Details
Third paragraph
"""
    (workspace_tmp_path / "notes.md").write_text(content, encoding="utf-8")

    pipeline = IndexerPipeline()
    chunks = pipeline.build_markdown_chunks(workspace_tmp_path, project_id="unity-sample")

    assert len(chunks) == 3
    assert [chunk.line_hint for chunk in chunks] == [2, 5, 8]
    assert [chunk.citation for chunk in chunks] == [
        "notes.md:2",
        "notes.md:5",
        "notes.md:8",
    ]
    assert chunks[0].title == "notes.md - Intro"
    assert chunks[2].title == "notes.md - Details"


def test_markdown_chunk_ids_are_deterministic(workspace_tmp_path: Path) -> None:
    (workspace_tmp_path / "doc.md").write_text("# Head\nPara one\n\nPara two\n", encoding="utf-8")
    pipeline = IndexerPipeline()

    first = pipeline.build_markdown_chunks(workspace_tmp_path, project_id="p1")
    second = pipeline.build_markdown_chunks(workspace_tmp_path, project_id="p1")

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]


def test_code_chunking_preserves_order_citation_and_kind(workspace_tmp_path: Path) -> None:
    code = """namespace Game.Core
{
    public class Player
    {
        public void Move(int step)
        {
        }
    }
}
"""
    (workspace_tmp_path / "Player.cs").write_text(code, encoding="utf-8")

    pipeline = IndexerPipeline()
    chunks = pipeline.build_code_chunks(workspace_tmp_path, project_id="code-project")

    assert len(chunks) == 3
    assert [chunk.type for chunk in chunks] == ["code_chunk", "code_chunk", "code_chunk"]
    assert [chunk.source_kind for chunk in chunks] == ["code", "code", "code"]
    assert [chunk.line_hint for chunk in chunks] == [1, 3, 5]
    assert [chunk.citation for chunk in chunks] == [
        "Player.cs:1",
        "Player.cs:3",
        "Player.cs:5",
    ]
    assert chunks[0].title == "Player.cs - Game.Core"
    assert chunks[1].title == "Player.cs - Player"
    assert chunks[2].title == "Player.cs - Move"


def test_code_chunk_ids_are_deterministic(workspace_tmp_path: Path) -> None:
    code = """public class InventoryService
{
    public int Count()
    {
        return 1;
    }
}
"""
    (workspace_tmp_path / "InventoryService.cs").write_text(code, encoding="utf-8")

    pipeline = IndexerPipeline()
    first = pipeline.build_code_chunks(workspace_tmp_path, project_id="code-id")
    second = pipeline.build_code_chunks(workspace_tmp_path, project_id="code-id")

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]


def test_config_chunking_manifest_json_preserves_order_and_citation(workspace_tmp_path: Path) -> None:
    manifest = """{
  "dependencies": {
    "com.unity.textmeshpro": "3.0.6"
  },
  "scopedRegistries": []
}
"""
    (workspace_tmp_path / "manifest.json").write_text(manifest, encoding="utf-8")

    pipeline = IndexerPipeline()
    chunks = pipeline.build_config_chunks(workspace_tmp_path, project_id="cfg-project")

    assert len(chunks) == 2
    assert [chunk.source_kind for chunk in chunks] == ["config", "config"]
    assert [chunk.line_hint for chunk in chunks] == [2, 5]
    assert [chunk.citation for chunk in chunks] == [
        "manifest.json:2",
        "manifest.json:5",
    ]
    assert chunks[0].title == "manifest.json - dependencies"
    assert chunks[1].title == "manifest.json - scopedRegistries"


def test_config_chunk_ids_are_deterministic(workspace_tmp_path: Path) -> None:
    config = """root: true
section_a:
  k1: v1
section_b:
  k2: v2
"""
    (workspace_tmp_path / "settings.yaml").write_text(config, encoding="utf-8")

    pipeline = IndexerPipeline()
    first = pipeline.build_config_chunks(workspace_tmp_path, project_id="cfg-id")
    second = pipeline.build_config_chunks(workspace_tmp_path, project_id="cfg-id")

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]

