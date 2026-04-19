from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from a_stock_agent.agent import AGENT_NAME
from a_stock_agent.config import Settings
from a_stock_agent.database import SQLiteRepository
from a_stock_agent.knowledge import DeterministicEmbeddingService, KnowledgeService
from a_stock_agent.market_data import AKShareService

from .schemas import ChatRequest, ChatResponse, KnowledgeImportRequest

DISCLAIMER = (
    "Research-only output. This service does not provide personalized investment "
    "advice, trading instructions, order placement, or position sizing."
)


def create_app(database_path: str | Path | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if database_path is not None:
        settings.database_path = Path(database_path)

    repository = SQLiteRepository(settings.database_path)
    repository.initialize()
    knowledge_service = KnowledgeService(
        repository=repository,
        embedding_service=DeterministicEmbeddingService(dimensions=64),
    )

    app = FastAPI(title="A Stock Agent API", version="0.1.0")
    app.state.settings = settings
    app.state.repository = repository
    app.state.knowledge_service = knowledge_service

    @app.get("/health")
    def health() -> dict[str, Any]:
        repository.initialize()
        return {
            "status": "ok",
            "database": "ok",
            "embedding_model": settings.embedding_model,
            "agent": AGENT_NAME,
        }

    @app.get("/api/v1/config")
    def config() -> dict[str, Any]:
        return {
            "embedding_model": settings.embedding_model,
            "data_source": "akshare",
            "llm_provider": settings.llm_provider,
            "enable_live_akshare": settings.enable_live_akshare,
            "enable_adk_web_ui": settings.enable_adk_web_ui,
            "agent": AGENT_NAME,
        }

    @app.post("/api/v1/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        repository.create_session(session_id, request.user_id)
        repository.add_message(session_id, "user", request.message)
        answer = _research_stub_answer(request.message, request.symbols)
        repository.add_message(session_id, "assistant", answer)
        return ChatResponse(
            session_id=session_id,
            answer=answer,
            citations=[],
            tool_calls=[],
            data_timestamp=_now(),
            disclaimer=DISCLAIMER,
        )

    @app.post("/api/v1/chat/stream")
    def chat_stream(request: ChatRequest) -> StreamingResponse:
        response = chat(request)

        def events():
            yield f"event: message\ndata: {response.answer}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.post("/api/v1/knowledge/import")
    def import_knowledge(request: KnowledgeImportRequest) -> dict[str, Any]:
        try:
            result = knowledge_service.import_file(request.file_path, force=request.force)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "document_id": result.document_id,
            "title": result.title,
            "chunks_count": result.chunks_count,
            "status": result.status,
            "skipped_reason": result.skipped_reason,
        }

    @app.get("/api/v1/knowledge/documents")
    def list_documents() -> dict[str, Any]:
        return {"documents": repository.list_documents()}

    @app.delete("/api/v1/knowledge/documents/{document_id}")
    def delete_document(document_id: int) -> dict[str, Any]:
        repository.delete_document(document_id)
        return {"status": "deleted", "document_id": document_id}

    @app.get("/api/v1/stocks/{symbol}/snapshot")
    def stock_snapshot(symbol: str) -> dict[str, Any]:
        try:
            return AKShareService().get_stock_snapshot(symbol).model_dump()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/v1/stocks/{symbol}/history")
    def stock_history(
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> dict[str, Any]:
        try:
            return AKShareService().get_stock_history(symbol, start_date, end_date, adjust).model_dump()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


def _research_stub_answer(message: str, symbols: list[str]) -> str:
    symbol_text = ", ".join(symbols) if symbols else "the mentioned A-share securities"
    return (
        f"I received your research question about {symbol_text}: {message}. "
        "The v1 API boundary is ready; live ADK model execution can be enabled by "
        "configuring the LLM provider and using the ADK runtime."
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
