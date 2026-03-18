from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RecordType(str, Enum):
    DOC_CHUNK = "doc_chunk"
    CODE_CHUNK = "code_chunk"
    TASK_SUMMARY = "task_summary"


class RetrievalStrategy(str, Enum):
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    VECTOR = "vector"


class ScopeKind(str, Enum):
    PROJECT = "project"
    SESSION = "session"


class KnowledgeRecord(BaseModel):
    id: str
    project_id: str
    scope: str
    type: RecordType
    text: str
    summary: str
    title: str
    source_kind: str
    source_path: str
    source_id: str
    tags: list[str] = Field(default_factory=list)
    importance: float = 0.5
    confidence: float = 0.5
    verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None
    access_count: int = 0
    line_hint: int | None = None
    citation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecallFilters(BaseModel):
    verified_only: bool = False
    source_kinds: list[str] = Field(default_factory=list)
    paths_prefix: list[str] = Field(default_factory=list)


class RecallRequest(BaseModel):
    project_id: str
    query: str
    scopes: list[str] = Field(default_factory=list)
    types: list[RecordType] = Field(default_factory=list)
    top_k: int = 8
    filters: RecallFilters = Field(default_factory=RecallFilters)
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID


class RecallResult(BaseModel):
    id: str
    type: RecordType
    title: str
    summary: str
    score: float
    why_relevant: str
    source_kind: str
    source_path: str
    citation: str
    line_hint: int | None = None
    verified: bool = False
    next_candidates: list[str] = Field(default_factory=list)


class RecallResponse(BaseModel):
    query: str
    project_id: str
    strategy: RetrievalStrategy
    results: list[RecallResult] = Field(default_factory=list)


class IndexUpsertRequest(BaseModel):
    project_id: str
    records: list[KnowledgeRecord]


class IndexUpsertResponse(BaseModel):
    project_id: str
    upserted: int


class MemoryStoreRequest(BaseModel):
    project_id: str
    task_id: str
    scope: str
    summary: str
    related_paths: list[str] = Field(default_factory=list)
    verified: bool = False
    importance: float = 0.6
    confidence: float = 0.6


class MemoryStoreResponse(BaseModel):
    project_id: str
    task_id: str
    stored: bool
