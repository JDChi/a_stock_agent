from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    sha256 TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(document_id, chunk_index)
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    text,
                    tokenize='unicode61'
                );
                CREATE TABLE IF NOT EXISTS market_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_document(self, title: str, source_path: str, source_type: str, sha256: str) -> int:
        self.initialize()
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM documents WHERE sha256 = ?", (sha256,)).fetchone()
            if row:
                return int(row["id"])
            cursor = conn.execute(
                """
                INSERT INTO documents (title, source_path, source_type, sha256)
                VALUES (?, ?, ?, ?)
                """,
                (title, source_path, source_type, sha256),
            )
            return int(cursor.lastrowid)

    def find_document_by_hash(self, sha256: str) -> dict[str, Any] | None:
        self.initialize()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE sha256 = ?", (sha256,)).fetchone()
            return _row_to_dict(row) if row else None

    def add_chunk(
        self,
        document_id: int,
        chunk_index: int,
        text: str,
        metadata: dict[str, Any],
        embedding: bytes | None,
    ) -> int:
        self.initialize()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, text, metadata_json, embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, chunk_index, text, json.dumps(metadata), embedding),
            )
            chunk_id = int(cursor.lastrowid)
            conn.execute(
                "INSERT INTO chunks_fts (chunk_id, text) VALUES (?, ?)",
                (chunk_id, text),
            )
            return chunk_id

    def search_chunks(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        self.initialize()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT c.id, c.document_id, c.chunk_index, c.text, c.metadata_json, c.embedding,
                       d.title AS document_title, d.source_path, d.source_type
                FROM chunks_fts f
                JOIN chunks c ON c.id = f.chunk_id
                JOIN documents d ON d.id = c.document_id
                WHERE chunks_fts MATCH ?
                ORDER BY bm25(chunks_fts)
                LIMIT ?
                """,
                (_fts_query(query), limit),
            ).fetchall()
            return [_decode_chunk_row(row) for row in rows]

    def list_documents(self) -> list[dict[str, Any]]:
        self.initialize()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT d.*,
                       (SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id) AS chunks_count
                FROM documents d
                ORDER BY d.created_at DESC, d.id DESC
                """
            ).fetchall()
            return [_row_to_dict(row) for row in rows]

    def delete_document(self, document_id: int) -> None:
        self.initialize()
        with self.connect() as conn:
            chunk_ids = [
                row["id"]
                for row in conn.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,))
            ]
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            if chunk_ids:
                placeholders = ",".join("?" for _ in chunk_ids)
                conn.execute(f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids)

    def create_session(self, session_id: str, user_id: str | None = None) -> None:
        self.initialize()
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, user_id) VALUES (?, ?)",
                (session_id, user_id),
            )

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.initialize()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _decode_chunk_row(row: sqlite3.Row) -> dict[str, Any]:
    data = _row_to_dict(row)
    data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
    return data


def _fts_query(query: str) -> str:
    terms = [term.strip() for term in query.replace('"', " ").split() if term.strip()]
    return " OR ".join(terms) if terms else query
