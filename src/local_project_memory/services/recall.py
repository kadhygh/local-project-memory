from __future__ import annotations

import re

from local_project_memory.domain.models import RecallRequest, RecallResponse, RecallResult
from local_project_memory.services.store import REPOSITORY


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class RecallService:
    """Keyword-based retrieval service backed by the configured repository."""

    def __init__(self, repository=None) -> None:
        self.repository = repository or REPOSITORY

    def recall(self, request: RecallRequest) -> RecallResponse:
        records = self._apply_filters(request)
        query_terms = self._tokenize(request.query)

        scored: list[tuple[float, object]] = []
        for record in records:
            score = self._score_record(record, query_terms)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_results = scored[: max(request.top_k, 0)]

        response_results = [
            RecallResult(
                id=record.id,
                type=record.type,
                title=record.title,
                summary=record.summary,
                score=round(score, 4),
                why_relevant=self._why_relevant(record, query_terms),
                source_kind=record.source_kind,
                source_path=record.source_path,
                citation=record.citation,
                line_hint=record.line_hint,
                verified=record.verified,
                next_candidates=self._next_candidates(record),
            )
            for score, record in top_results
        ]

        return RecallResponse(
            query=request.query,
            project_id=request.project_id,
            strategy=request.strategy,
            results=response_results,
        )

    def _apply_filters(self, request: RecallRequest) -> list[object]:
        records = [r for r in self.repository.list_records() if r.project_id == request.project_id]

        if request.scopes:
            scope_set = set(request.scopes)
            records = [r for r in records if r.scope in scope_set]

        if request.types:
            type_set = set(request.types)
            records = [r for r in records if r.type in type_set]

        if request.filters.verified_only:
            records = [r for r in records if r.verified]

        if request.filters.source_kinds:
            source_kind_set = set(request.filters.source_kinds)
            records = [r for r in records if r.source_kind in source_kind_set]

        if request.filters.paths_prefix:
            prefixes = tuple(request.filters.paths_prefix)
            records = [r for r in records if r.source_path.startswith(prefixes)]

        return records

    def _score_record(self, record: object, query_terms: set[str]) -> float:
        if not query_terms:
            return 0.0

        haystack_title = self._tokenize(record.title)
        haystack_summary = self._tokenize(record.summary)
        haystack_text = self._tokenize(record.text)
        haystack_tags = {tag.lower() for tag in record.tags}
        haystack_path = self._tokenize(record.source_path)

        score = 0.0
        matched_terms = 0
        for term in query_terms:
            matched = False
            if term in haystack_title:
                score += 3.0
                matched = True
            if term in haystack_summary:
                score += 2.0
                matched = True
            if term in haystack_text:
                score += 1.0
                matched = True
            if term in haystack_tags:
                score += 1.5
                matched = True
            if term in haystack_path:
                score += 0.8
                matched = True
            if matched:
                matched_terms += 1

        if matched_terms == 0:
            return 0.0

        score += record.importance * 0.3
        score += record.confidence * 0.2
        if record.verified:
            score += 0.3

        return score

    def _why_relevant(self, record: object, query_terms: set[str]) -> str:
        matched = sorted(query_terms.intersection(self._tokenize(f"{record.title} {record.summary} {record.source_path}")))
        if not matched:
            return "Matched by metadata filters and ranking signals."
        return f"Matched keywords: {', '.join(matched[:6])}."

    def _next_candidates(self, record: object) -> list[str]:
        related_paths = record.metadata.get("related_paths")
        if isinstance(related_paths, list):
            return [str(path) for path in related_paths[:3]]
        return []

    def _tokenize(self, text: str) -> set[str]:
        english_tokens = {token.lower() for token in _TOKEN_PATTERN.findall(text)}
        cjk_tokens = self._tokenize_cjk(text)
        return english_tokens.union(cjk_tokens)

    def _tokenize_cjk(self, text: str) -> set[str]:
        tokens: set[str] = set()
        current_segment: list[str] = []

        for char in text:
            if self._is_cjk(char):
                current_segment.append(char)
                continue

            self._add_segment_tokens(tokens, current_segment)
            current_segment = []

        self._add_segment_tokens(tokens, current_segment)
        return tokens

    def _add_segment_tokens(self, tokens: set[str], segment_chars: list[str]) -> None:
        if not segment_chars:
            return

        segment = "".join(segment_chars)
        if len(segment) == 1:
            tokens.add(segment)
            return

        for index in range(len(segment) - 1):
            tokens.add(segment[index : index + 2])

    def _is_cjk(self, char: str) -> bool:
        codepoint = ord(char)
        return 0x4E00 <= codepoint <= 0x9FFF