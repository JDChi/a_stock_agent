from __future__ import annotations

from .config import get_settings
from .database import SQLiteRepository
from .knowledge import DeterministicEmbeddingService, KnowledgeService
from .market_data import AKShareService


def search_knowledge(query: str, top_k: int = 8, filters: dict | None = None) -> dict:
    settings = get_settings()
    service = KnowledgeService(
        repository=SQLiteRepository(settings.database_path),
        embedding_service=DeterministicEmbeddingService(dimensions=64),
    )
    hits = service.search(query, top_k=top_k)
    return {
        "query": query,
        "filters": filters or {},
        "hits": [
            {
                "document_id": hit.document_id,
                "document_title": hit.document_title,
                "chunk_index": hit.chunk_index,
                "text": hit.text,
                "score": hit.score,
                "metadata": hit.metadata,
            }
            for hit in hits
        ],
    }


def get_stock_snapshot(symbol: str) -> dict:
    return AKShareService().get_stock_snapshot(symbol).model_dump()


def get_stock_history(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> dict:
    return AKShareService().get_stock_history(symbol, start_date, end_date, adjust).model_dump()


def get_company_profile(symbol: str) -> dict:
    return AKShareService().get_company_profile(symbol)


def get_financial_indicators(symbol: str, start_year: int | None = None) -> dict:
    return AKShareService().get_financial_indicators(symbol, start_year=start_year)
