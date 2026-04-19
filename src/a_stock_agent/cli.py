from __future__ import annotations

import argparse

from .config import get_settings
from .database import SQLiteRepository
from .knowledge import DeterministicEmbeddingService, KnowledgeService


def import_document() -> None:
    parser = argparse.ArgumentParser(description="Import a document into the local RAG knowledge base.")
    parser.add_argument("path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    service = KnowledgeService(
        repository=SQLiteRepository(settings.database_path),
        embedding_service=DeterministicEmbeddingService(dimensions=64),
    )
    result = service.import_file(args.path, force=args.force)
    print(f"{result.status}: {result.title} ({result.chunks_count} chunks)")
