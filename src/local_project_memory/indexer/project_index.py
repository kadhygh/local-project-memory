from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import re

from local_project_memory.domain.models import IndexUpsertRequest, KnowledgeRecord
from local_project_memory.indexer.pipeline import ChunkCandidate, IndexerPipeline
from local_project_memory.indexer.record_mapper import chunk_candidate_to_record
from local_project_memory.services.store import StoreService


_CODE_BOUNDARY_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?"
    r"(?:class|interface|enum|struct|void|int|float|double|bool|string|Task<|Task\s|IEnumerable<)"
)


@dataclass(slots=True)
class ProjectIndexResult:
    project_id: str
    docs_chunks: int
    code_chunks: int
    config_chunks: int
    upserted: int


class ProjectIndexer:
    """Index a local project directory into the current MemoryService store."""

    def __init__(
        self,
        *,
        pipeline: IndexerPipeline | None = None,
        store_service: StoreService | None = None,
    ) -> None:
        self.pipeline = pipeline or IndexerPipeline()
        self.store_service = store_service or StoreService()

    def index_project(
        self,
        *,
        project_root: str | Path,
        project_id: str,
        docs_root: str | Path | None = None,
        unity_root: str | Path | None = None,
        scope: str | None = None,
    ) -> ProjectIndexResult:
        root = Path(project_root)
        docs_dir = Path(docs_root) if docs_root is not None else root / "Docs"
        unity_dir = Path(unity_root) if unity_root is not None else root / "UnityProject"
        effective_scope = scope or f"project:{project_id}"

        doc_chunks = self._build_docs_chunks(docs_dir, project_id=project_id, scope=effective_scope)
        code_chunks = self._build_code_chunks(unity_dir, project_id=project_id, scope=effective_scope)
        config_chunks = self._build_config_chunks(unity_dir, project_id=project_id, scope=effective_scope)

        all_chunks = [*doc_chunks, *code_chunks, *config_chunks]
        records = [chunk_candidate_to_record(chunk) for chunk in all_chunks]

        upserted = self._upsert(project_id=project_id, records=records)
        return ProjectIndexResult(
            project_id=project_id,
            docs_chunks=len(doc_chunks),
            code_chunks=len(code_chunks),
            config_chunks=len(config_chunks),
            upserted=upserted,
        )

    def _build_docs_chunks(self, docs_dir: Path, *, project_id: str, scope: str) -> list[ChunkCandidate]:
        if not docs_dir.exists() or not docs_dir.is_dir():
            return []
        return self.pipeline.build_markdown_chunks(docs_dir, project_id=project_id, scope=scope)

    def _build_code_chunks(self, unity_dir: Path, *, project_id: str, scope: str) -> list[ChunkCandidate]:
        assets_dir = unity_dir / "Assets"
        if not assets_dir.exists():
            return []

        chunks: list[ChunkCandidate] = []
        code_files = sorted(assets_dir.rglob("*.cs"), key=lambda p: p.as_posix().lower())

        for source_path in code_files:
            text = self._read_text_file(source_path)
            if not text:
                continue
            relative_path = self._relative_path(source_path, unity_dir)
            file_chunks = self._chunk_code_text(
                text=text,
                project_id=project_id,
                scope=scope,
                relative_path=relative_path,
            )
            chunks.extend(file_chunks)

        return chunks

    def _build_config_chunks(self, unity_dir: Path, *, project_id: str, scope: str) -> list[ChunkCandidate]:
        candidate_files: list[Path] = []
        manifest = unity_dir / "Packages" / "manifest.json"
        if manifest.exists():
            candidate_files.append(manifest)

        project_settings = unity_dir / "ProjectSettings"
        if project_settings.exists():
            for path in sorted(project_settings.rglob("*"), key=lambda p: p.as_posix().lower()):
                if path.is_file():
                    candidate_files.append(path)

        chunks: list[ChunkCandidate] = []
        for source_path in candidate_files:
            text = self._read_text_file(source_path)
            if not text:
                continue
            relative_path = self._relative_path(source_path, unity_dir)
            file_chunks = self._chunk_config_text(
                text=text,
                project_id=project_id,
                scope=scope,
                relative_path=relative_path,
            )
            chunks.extend(file_chunks)

        return chunks

    def _upsert(self, *, project_id: str, records: list[KnowledgeRecord]) -> int:
        if not records:
            return 0
        response = self.store_service.upsert(IndexUpsertRequest(project_id=project_id, records=records))
        return response.upserted

    def _chunk_code_text(
        self,
        *,
        text: str,
        project_id: str,
        scope: str,
        relative_path: str,
    ) -> list[ChunkCandidate]:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        boundaries = [index for index, line in enumerate(lines) if _CODE_BOUNDARY_PATTERN.match(line)]
        if not boundaries:
            boundaries = [0]
        if boundaries[-1] != len(lines):
            boundaries.append(len(lines))

        chunks: list[ChunkCandidate] = []
        for order in range(len(boundaries) - 1):
            start = boundaries[order]
            end = boundaries[order + 1]
            segment_lines = lines[start:end]
            segment_text = "\n".join(segment_lines).strip()
            if not segment_text:
                continue

            line_hint = start + 1
            chunk_id = self._build_chunk_id(
                prefix="code",
                project_id=project_id,
                relative_path=relative_path,
                chunk_index=order,
                line_hint=line_hint,
                text=segment_text,
            )
            title = f"{Path(relative_path).name} - block {order + 1}"
            citation = f"{relative_path}:{line_hint}"
            source_id = f"{relative_path}#block-{order:04d}"
            metadata: dict[str, str | int] = {
                "relative_path": relative_path,
                "block_order": order,
            }

            chunks.append(
                ChunkCandidate(
                    id=chunk_id,
                    project_id=project_id,
                    scope=scope,
                    type="code_chunk",
                    text=segment_text,
                    summary=self._summarize(segment_text),
                    title=title,
                    source_kind="code",
                    source_path=relative_path,
                    source_id=source_id,
                    citation=citation,
                    line_hint=line_hint,
                    metadata=metadata,
                )
            )

        return chunks

    def _chunk_config_text(
        self,
        *,
        text: str,
        project_id: str,
        scope: str,
        relative_path: str,
    ) -> list[ChunkCandidate]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs: list[tuple[int, str]] = []
        current_start: int | None = None
        current_lines: list[str] = []
        lines = normalized.split("\n")

        for line_no, line in enumerate(lines + [""], start=1):
            if line.strip():
                if current_start is None:
                    current_start = line_no
                current_lines.append(line)
                continue
            if current_lines and current_start is not None:
                paragraphs.append((current_start, "\n".join(current_lines).strip()))
            current_start = None
            current_lines = []

        chunks: list[ChunkCandidate] = []
        for order, (line_hint, paragraph_text) in enumerate(paragraphs):
            chunk_id = self._build_chunk_id(
                prefix="cfg",
                project_id=project_id,
                relative_path=relative_path,
                chunk_index=order,
                line_hint=line_hint,
                text=paragraph_text,
            )
            title = f"{Path(relative_path).name} - section {order + 1}"
            citation = f"{relative_path}:{line_hint}"
            source_id = f"{relative_path}#section-{order:04d}"
            metadata: dict[str, str | int] = {
                "relative_path": relative_path,
                "section_order": order,
            }

            chunks.append(
                ChunkCandidate(
                    id=chunk_id,
                    project_id=project_id,
                    scope=scope,
                    type="doc_chunk",
                    text=paragraph_text,
                    summary=self._summarize(paragraph_text),
                    title=title,
                    source_kind="config",
                    source_path=relative_path,
                    source_id=source_id,
                    citation=citation,
                    line_hint=line_hint,
                    metadata=metadata,
                )
            )

        return chunks

    def _read_text_file(self, path: Path) -> str:
        raw = path.read_bytes()
        if b"\x00" in raw:
            return ""
        return raw.decode("utf-8", errors="ignore")

    def _build_chunk_id(
        self,
        *,
        prefix: str,
        project_id: str,
        relative_path: str,
        chunk_index: int,
        line_hint: int,
        text: str,
    ) -> str:
        digest = sha1(
            f"{project_id}|{relative_path}|{chunk_index}|{line_hint}|{text}".encode("utf-8")
        ).hexdigest()[:16]
        return f"{prefix}_{digest}"

    def _relative_path(self, path: Path, root: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()

    def _summarize(self, text: str, limit: int = 160) -> str:
        first_line = text.split("\n", maxsplit=1)[0].strip()
        if len(first_line) <= limit:
            return first_line
        return f"{first_line[: limit - 1].rstrip()}..."

