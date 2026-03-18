from fastapi import FastAPI

from local_project_memory.config import Settings
from local_project_memory.domain.models import (
    IndexUpsertRequest,
    IndexUpsertResponse,
    MemoryStoreRequest,
    MemoryStoreResponse,
    RecallRequest,
    RecallResponse,
)
from local_project_memory.services.recall import RecallService
from local_project_memory.services.store import StoreService

settings = Settings()
app = FastAPI(title=settings.app_name)

recall_service = RecallService()
store_service = StoreService()


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/search/recall", response_model=RecallResponse)
def search_recall(request: RecallRequest) -> RecallResponse:
    return recall_service.recall(request)


@app.post(f"{settings.api_prefix}/index/upsert", response_model=IndexUpsertResponse)
def index_upsert(request: IndexUpsertRequest) -> IndexUpsertResponse:
    return store_service.upsert(request)


@app.post(f"{settings.api_prefix}/memory/store", response_model=MemoryStoreResponse)
def memory_store(request: MemoryStoreRequest) -> MemoryStoreResponse:
    return store_service.store_task_summary(request)

