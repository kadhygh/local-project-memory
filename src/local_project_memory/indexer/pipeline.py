from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import re
from typing import Iterable


@dataclass(slots=True)
class SourceFile:
    path: Path
    kind: str


@dataclass(slots=True)
class ChunkCandidate:
    """Intermediate chunk model that can be mapped into KnowledgeRecord later."""

    id: str
    project_id: str
    scope: str
    type: str
    text: str
    summary: str
    title: str
    source_kind: str
    source_path: str
    source_id: str
    citation: str
    line_hint: int
    metadata: dict[str, str | int]


@dataclass(slots=True)
class _Section:
    title: str
    start_line: int
    body: list[tuple[int, str]]


class IndexerPipeline:
    """Filesystem discovery and first-pass chunking for Markdown, C#, and config files."""

    DOCUMENT_PATTERNS = ("*.md",)
    CODE_PATTERNS = ("*.cs",)
    CONFIG_PATTERNS = ("manifest.json", "*.json", "*.yaml", "*.yml")
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    CODE_NAMESPACE_PATTERN = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*[{;]?\s*$")
    CODE_TYPE_PATTERN = re.compile(
        r"^\s*(?:(?:public|private|protected|internal|static|sealed|abstract|partial|readonly|unsafe|new)\s+)*"
        r"(class|interface|enum|struct|record)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
    )
    CODE_METHOD_PATTERN = re.compile(
        r"^\s*(?:(?:public|private|protected|internal|static|virtual|override|abstract|async|sealed|extern|unsafe|new|partial)\s+)+"
        r"[A-Za-z_][A-Za-z0-9_<>\[\],\.\?\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:\{|=>|where|\;)?\s*$"
    )
    JSON_KEY_PATTERN = re.compile(r'^\s*"([^"]+)"\s*:')
    YAML_KEY_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)\s*:")
    DEFAULT_SCOPE_TEMPLATE = "project:{project_id}"
    MAX_SUMMARY_LENGTH = 160

    def discover(self, root: Path) -> list[SourceFile]:
        results: list[SourceFile] = []
        seen_paths: set[str] = set()

        for pattern in self.DOCUMENT_PATTERNS:
            for path in root.rglob(pattern):
                canonical = path.resolve().as_posix().lower()
                if canonical in seen_paths:
                    continue
                seen_paths.add(canonical)
                results.append(SourceFile(path=path, kind="document"))

        for pattern in self.CODE_PATTERNS:
            for path in root.rglob(pattern):
                canonical = path.resolve().as_posix().lower()
                if canonical in seen_paths:
                    continue
                seen_paths.add(canonical)
                results.append(SourceFile(path=path, kind="code"))

        for pattern in self.CONFIG_PATTERNS:
            for path in root.rglob(pattern):
                canonical = path.resolve().as_posix().lower()
                if canonical in seen_paths:
                    continue
                seen_paths.add(canonical)
                results.append(SourceFile(path=path, kind="config"))

        return sorted(results, key=lambda item: self._sort_key(item.path, root))

    def discover_markdown(self, root: Path) -> list[SourceFile]:
        """Discover markdown files only, in deterministic order."""
        return [
            source
            for source in self.discover(root)
            if source.kind == "document" and source.path.suffix.lower() == ".md"
        ]

    def discover_code(self, root: Path) -> list[SourceFile]:
        """Discover C# files only, in deterministic order."""
        return [
            source
            for source in self.discover(root)
            if source.kind == "code" and source.path.suffix.lower() == ".cs"
        ]

    def discover_config(self, root: Path) -> list[SourceFile]:
        """Discover config files only, in deterministic order."""
        return [source for source in self.discover(root) if source.kind == "config"]

    def build_markdown_chunks(
        self,
        root: Path,
        project_id: str,
        scope: str | None = None,
    ) -> list[ChunkCandidate]:
        """
        Build deterministic markdown chunks from heading/paragraph structure.

        Output is intentionally an intermediate model that can be mapped to
        KnowledgeRecord by the storage layer.
        """
        chunks: list[ChunkCandidate] = []
        effective_scope = scope or self.DEFAULT_SCOPE_TEMPLATE.format(project_id=project_id)

        for source in self.discover_markdown(root):
            relative_path = self._relative_path(source.path, root)
            text = source.path.read_text(encoding="utf-8", errors="ignore")
            file_chunks = self._chunk_markdown_text(
                text=text,
                project_id=project_id,
                scope=effective_scope,
                relative_path=relative_path,
            )
            chunks.extend(file_chunks)

        return chunks

    def build_code_chunks(
        self,
        root: Path,
        project_id: str,
        scope: str | None = None,
    ) -> list[ChunkCandidate]:
        """Build deterministic C# chunks using simple structural anchors."""
        chunks: list[ChunkCandidate] = []
        effective_scope = scope or self.DEFAULT_SCOPE_TEMPLATE.format(project_id=project_id)

        for source in self.discover_code(root):
            relative_path = self._relative_path(source.path, root)
            text = source.path.read_text(encoding="utf-8", errors="ignore")
            file_chunks = self._chunk_code_text(
                text=text,
                project_id=project_id,
                scope=effective_scope,
                relative_path=relative_path,
            )
            chunks.extend(file_chunks)

        return chunks

    def build_config_chunks(
        self,
        root: Path,
        project_id: str,
        scope: str | None = None,
    ) -> list[ChunkCandidate]:
        """Build deterministic config chunks for JSON/YAML style files."""
        chunks: list[ChunkCandidate] = []
        effective_scope = scope or self.DEFAULT_SCOPE_TEMPLATE.format(project_id=project_id)

        for source in self.discover_config(root):
            relative_path = self._relative_path(source.path, root)
            text = source.path.read_text(encoding="utf-8", errors="ignore")
            file_chunks = self._chunk_config_text(
                text=text,
                project_id=project_id,
                scope=effective_scope,
                relative_path=relative_path,
            )
            chunks.extend(file_chunks)

        return chunks

    def _chunk_markdown_text(
        self,
        text: str,
        project_id: str,
        scope: str,
        relative_path: str,
    ) -> list[ChunkCandidate]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        sections = self._split_sections(lines=lines, fallback_title=Path(relative_path).stem)

        chunks: list[ChunkCandidate] = []
        for section_order, section in enumerate(sections):
            paragraphs = self._split_paragraphs(section.body)
            for paragraph_order, (line_hint, paragraph_text) in enumerate(paragraphs):
                chunk_index = len(chunks)
                chunk_id = self._build_chunk_id(
                    project_id=project_id,
                    relative_path=relative_path,
                    chunk_index=chunk_index,
                    line_hint=line_hint,
                    text=paragraph_text,
                    kind_prefix="doc",
                )
                title = self._build_title(file_path=relative_path, section_title=section.title)
                chunk_text = self._build_chunk_text(section.title, paragraph_text)
                citation = f"{relative_path}:{line_hint}"
                source_id = f"{relative_path}#chunk-{chunk_index:04d}"
                summary = self._summarize(paragraph_text)
                metadata: dict[str, str | int] = {
                    "section_title": section.title,
                    "section_order": section_order,
                    "paragraph_order": paragraph_order,
                    "relative_path": relative_path,
                }

                chunks.append(
                    ChunkCandidate(
                        id=chunk_id,
                        project_id=project_id,
                        scope=scope,
                        type="doc_chunk",
                        text=chunk_text,
                        summary=summary,
                        title=title,
                        source_kind="document",
                        source_path=relative_path,
                        source_id=source_id,
                        citation=citation,
                        line_hint=line_hint,
                        metadata=metadata,
                    )
                )

        return chunks

    def _chunk_code_text(
        self,
        text: str,
        project_id: str,
        scope: str,
        relative_path: str,
    ) -> list[ChunkCandidate]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        anchors = self._find_code_anchors(lines)
        spans = self._build_spans(anchors=anchors, total_lines=len(lines))

        chunks: list[ChunkCandidate] = []
        if not spans:
            spans = self._build_fallback_spans(lines)

        for chunk_index, (line_hint, end_line, anchor_kind, anchor_name) in enumerate(spans):
            span_text = "\n".join(lines[line_hint - 1 : end_line]).strip()
            if not span_text:
                continue

            chunk_id = self._build_chunk_id(
                project_id=project_id,
                relative_path=relative_path,
                chunk_index=chunk_index,
                line_hint=line_hint,
                text=span_text,
                kind_prefix="code",
            )
            symbol_name = anchor_name or f"block-{chunk_index:04d}"
            title = f"{Path(relative_path).name} - {symbol_name}"
            citation = f"{relative_path}:{line_hint}"
            source_id = f"{relative_path}#chunk-{chunk_index:04d}"
            metadata: dict[str, str | int] = {
                "relative_path": relative_path,
                "anchor_kind": anchor_kind,
                "anchor_name": symbol_name,
                "chunk_order": chunk_index,
            }

            chunks.append(
                ChunkCandidate(
                    id=chunk_id,
                    project_id=project_id,
                    scope=scope,
                    type="code_chunk",
                    text=span_text,
                    summary=self._summarize(span_text),
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
        text: str,
        project_id: str,
        scope: str,
        relative_path: str,
    ) -> list[ChunkCandidate]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        anchors = self._find_config_anchors(lines)
        spans = self._build_spans(anchors=anchors, total_lines=len(lines))

        chunks: list[ChunkCandidate] = []
        if not spans:
            non_empty = [index for index, line in enumerate(lines, start=1) if line.strip()]
            if non_empty:
                spans = [(non_empty[0], len(lines), "config", "full-file")]

        for chunk_index, (line_hint, end_line, anchor_kind, anchor_name) in enumerate(spans):
            span_text = "\n".join(lines[line_hint - 1 : end_line]).strip()
            if not span_text:
                continue

            chunk_id = self._build_chunk_id(
                project_id=project_id,
                relative_path=relative_path,
                chunk_index=chunk_index,
                line_hint=line_hint,
                text=span_text,
                kind_prefix="cfg",
            )
            key_name = anchor_name or f"block-{chunk_index:04d}"
            title = f"{Path(relative_path).name} - {key_name}"
            citation = f"{relative_path}:{line_hint}"
            source_id = f"{relative_path}#chunk-{chunk_index:04d}"
            metadata: dict[str, str | int] = {
                "relative_path": relative_path,
                "anchor_kind": anchor_kind,
                "config_key": key_name,
                "chunk_order": chunk_index,
            }

            chunks.append(
                ChunkCandidate(
                    id=chunk_id,
                    project_id=project_id,
                    scope=scope,
                    type="doc_chunk",
                    text=span_text,
                    summary=self._summarize(span_text),
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

    def _find_code_anchors(self, lines: list[str]) -> list[tuple[int, str, str]]:
        anchors: list[tuple[int, str, str]] = []
        control_prefixes = ("if ", "for ", "foreach ", "while ", "switch ", "catch ", "lock ", "using ")

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            namespace_match = self.CODE_NAMESPACE_PATTERN.match(line)
            if namespace_match:
                anchors.append((line_no, "namespace", namespace_match.group(1)))
                continue

            type_match = self.CODE_TYPE_PATTERN.match(line)
            if type_match:
                anchors.append((line_no, type_match.group(1), type_match.group(2)))
                continue

            lowered = stripped.lower()
            if any(lowered.startswith(prefix) for prefix in control_prefixes):
                continue

            method_match = self.CODE_METHOD_PATTERN.match(line)
            if method_match:
                anchors.append((line_no, "method", method_match.group(1)))

        return anchors

    def _find_config_anchors(self, lines: list[str]) -> list[tuple[int, str, str]]:
        anchors: list[tuple[int, str, str]] = []

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip(" "))
            if indent > 2:
                continue

            json_match = self.JSON_KEY_PATTERN.match(line)
            if json_match:
                anchors.append((line_no, "json-key", json_match.group(1)))
                continue

            yaml_match = self.YAML_KEY_PATTERN.match(stripped)
            if yaml_match:
                anchors.append((line_no, "yaml-key", yaml_match.group(1)))

        return anchors

    def _build_spans(self, anchors: list[tuple[int, str, str]], total_lines: int) -> list[tuple[int, int, str, str]]:
        spans: list[tuple[int, int, str, str]] = []
        for index, (start_line, anchor_kind, anchor_name) in enumerate(anchors):
            next_start = anchors[index + 1][0] if index + 1 < len(anchors) else total_lines + 1
            end_line = max(start_line, next_start - 1)
            spans.append((start_line, end_line, anchor_kind, anchor_name))
        return spans

    def _build_fallback_spans(self, lines: list[str]) -> list[tuple[int, int, str, str]]:
        spans: list[tuple[int, int, str, str]] = []
        current_start: int | None = None

        for line_no, line in list(enumerate(lines, start=1)) + [(-1, "")]:
            if not line.strip():
                if current_start is not None:
                    spans.append((current_start, line_no - 1, "fallback", "fallback"))
                    current_start = None
                continue

            if current_start is None:
                current_start = line_no

        return spans

    def _split_sections(self, lines: list[str], fallback_title: str) -> list[_Section]:
        sections: list[_Section] = []
        current = _Section(title=fallback_title, start_line=1, body=[])

        for line_no, line in enumerate(lines, start=1):
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                if current.body:
                    sections.append(current)
                current = _Section(title=heading_match.group(2).strip(), start_line=line_no, body=[])
                continue
            current.body.append((line_no, line))

        if current.body:
            sections.append(current)

        if not sections and lines:
            sections.append(_Section(title=fallback_title, start_line=1, body=[(1, "\n".join(lines))]))

        return sections

    def _split_paragraphs(self, body: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
        paragraphs: list[tuple[int, str]] = []
        current_start: int | None = None
        current_lines: list[str] = []

        for line_no, line in list(body) + [(-1, "")]:
            if not line.strip():
                if current_lines and current_start is not None:
                    paragraph_text = "\n".join(current_lines).strip()
                    if paragraph_text:
                        paragraphs.append((current_start, paragraph_text))
                current_start = None
                current_lines = []
                continue

            if current_start is None:
                current_start = line_no
            current_lines.append(line.rstrip())

        return paragraphs

    def _build_chunk_id(
        self,
        project_id: str,
        relative_path: str,
        chunk_index: int,
        line_hint: int,
        text: str,
        kind_prefix: str = "doc",
    ) -> str:
        digest = sha1(
            f"{project_id}|{relative_path}|{chunk_index}|{line_hint}|{text}".encode("utf-8")
        ).hexdigest()[:16]
        return f"{kind_prefix}_{digest}"

    def _build_title(self, file_path: str, section_title: str) -> str:
        file_name = Path(file_path).name
        return f"{file_name} - {section_title}"

    def _build_chunk_text(self, section_title: str, paragraph_text: str) -> str:
        return f"# {section_title}\n\n{paragraph_text}"

    def _summarize(self, paragraph_text: str) -> str:
        first_sentence = paragraph_text.split("\n", maxsplit=1)[0].strip()
        if len(first_sentence) <= self.MAX_SUMMARY_LENGTH:
            return first_sentence
        return f"{first_sentence[: self.MAX_SUMMARY_LENGTH - 1].rstrip()}..."

    def _relative_path(self, path: Path, root: Path) -> str:
        try:
            relative = path.relative_to(root)
        except ValueError:
            relative = path
        return relative.as_posix()

    def _sort_key(self, path: Path, root: Path) -> str:
        return self._relative_path(path, root).lower()
