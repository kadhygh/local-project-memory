import json
from pathlib import Path

from local_project_memory.cli.main import main


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cli_index_outputs_json_summary(workspace_tmp_path: Path, capsys) -> None:
    project_root = workspace_tmp_path / "project_cli_index"
    _write(project_root / "Docs" / "readme.md", "# Docs\nIndex me.\n")
    _write(project_root / "UnityProject" / "Assets" / "Scripts" / "PlayerController.cs", "public class PlayerController { }\n")
    _write(project_root / "UnityProject" / "Packages" / "manifest.json", "{\n  \"dependencies\": {}\n}\n")

    exit_code = main(
        [
            "index",
            "--project-id",
            "cli-proj-1",
            "--project-root",
            str(project_root),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["project_id"] == "cli-proj-1"
    assert payload["docs_chunks"] >= 1
    assert payload["code_chunks"] >= 1
    assert payload["config_chunks"] >= 1


def test_cli_search_indexes_and_returns_results(workspace_tmp_path: Path, capsys) -> None:
    project_root = workspace_tmp_path / "project_cli_search"
    _write(project_root / "Docs" / "readme.md", "# Docs\nGateway overview.\n")
    _write(
        project_root / "UnityProject" / "Assets" / "Editor" / "UnityGatewayAgent.cs",
        "public class UnityGatewayAgent { }\n",
    )
    _write(project_root / "UnityProject" / "Packages" / "manifest.json", "{\n  \"dependencies\": {}\n}\n")

    exit_code = main(
        [
            "search",
            "--project-id",
            "cli-proj-2",
            "--project-root",
            str(project_root),
            "--query",
            "UnityGatewayAgent",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["indexed"]["upserted"] >= 1
    assert len(payload["results"]) >= 1
    assert payload["results"][0]["source_path"].endswith("UnityGatewayAgent.cs")