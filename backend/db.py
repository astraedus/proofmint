"""
SQLite database layer via aiosqlite.

Schema:
  certificates — one row per completed agent task with full traceability:
    - what was submitted (input hash)
    - what was produced (output hash, verdict, summary)
    - where it lives on-chain (HCS topic + sequence number, NFT token + serial)
    - verification status
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)

_DB_PATH = "proofmint.db"

# In-memory store for tamper originals (keyed by cert_id)
_tamper_originals: dict[int, str] = {}

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    task_input_hash TEXT NOT NULL,
    task_output_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    verdict TEXT,
    summary TEXT,
    hcs_topic_id TEXT,
    hcs_sequence_number TEXT,
    nft_token_id TEXT,
    nft_serial_number INTEGER,
    issues_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    verified_at TEXT,
    verification_status TEXT
);
"""


def _set_db_path(path: str) -> None:
    """Override DB path (used in tests)."""
    global _DB_PATH
    _DB_PATH = path


async def init_db(db_path: str = _DB_PATH) -> None:
    """Create tables if they don't exist, and run migrations."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(_CREATE_TABLE)
        # Migration: add issues_json column if missing
        cursor = await db.execute("PRAGMA table_info(certificates)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "issues_json" not in columns:
            await db.execute("ALTER TABLE certificates ADD COLUMN issues_json TEXT")
            logger.info("Added issues_json column to certificates table")
        await db.commit()
    logger.info("Database initialised at %s", db_path)


async def save_certificate(
    task_type: str,
    task_input_hash: str,
    task_output_hash: str,
    agent_id: str,
    verdict: Optional[str] = None,
    summary: Optional[str] = None,
    hcs_topic_id: Optional[str] = None,
    hcs_sequence_number: Optional[str] = None,
    nft_token_id: Optional[str] = None,
    nft_serial_number: Optional[int] = None,
    issues_json: Optional[str] = None,
    verification_status: str = "pending",
    db_path: str = _DB_PATH,
) -> int:
    """Insert a certificate row and return its ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO certificates
                (task_type, task_input_hash, task_output_hash, agent_id, verdict,
                 summary, hcs_topic_id, hcs_sequence_number, nft_token_id,
                 nft_serial_number, issues_json, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_type, task_input_hash, task_output_hash, agent_id, verdict,
                summary, hcs_topic_id, hcs_sequence_number, nft_token_id,
                nft_serial_number, issues_json, verification_status,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_certificate(cert_id: int, db_path: str = _DB_PATH) -> Optional[dict[str, Any]]:
    """Return a single certificate by ID, or None."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM certificates WHERE id = ?", (cert_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("issues_json"):
                d["issues"] = json.loads(d["issues_json"])
            else:
                d["issues"] = []
            return d


async def list_certificates(
    limit: int = 20,
    offset: int = 0,
    db_path: str = _DB_PATH,
) -> list[dict[str, Any]]:
    """Return a paginated list of certificates, newest first."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM certificates ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def tamper_certificate(cert_id: int, db_path: str = _DB_PATH) -> dict[str, str]:
    """Corrupt task_output_hash to simulate tampering. Stores original for restore."""
    cert = await get_certificate(cert_id, db_path)
    if not cert:
        raise ValueError(f"Certificate {cert_id} not found")
    original_hash = cert["task_output_hash"]
    _tamper_originals[cert_id] = original_hash
    tampered_hash = "TAMPERED_" + original_hash[:56]
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE certificates SET task_output_hash = ?, verification_status = 'pending' WHERE id = ?",
            (tampered_hash, cert_id),
        )
        await db.commit()
    logger.info("Certificate %d tampered: %s -> %s", cert_id, original_hash[:16], tampered_hash[:16])
    return {"original_hash": original_hash, "tampered_hash": tampered_hash}


async def restore_certificate(cert_id: int, db_path: str = _DB_PATH) -> dict[str, str]:
    """Restore original task_output_hash after tamper simulation."""
    original_hash = _tamper_originals.pop(cert_id, None)
    if not original_hash:
        raise ValueError(f"No tamper record for certificate {cert_id}")
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE certificates SET task_output_hash = ?, verification_status = 'pending' WHERE id = ?",
            (original_hash, cert_id),
        )
        await db.commit()
    logger.info("Certificate %d restored to original hash", cert_id)
    return {"restored_hash": original_hash}


async def update_verification_status(
    cert_id: int,
    status: str,
    verified_at: Optional[str] = None,
    db_path: str = _DB_PATH,
) -> None:
    """Update the verification_status and optionally verified_at timestamp."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE certificates
            SET verification_status = ?,
                verified_at = COALESCE(?, verified_at)
            WHERE id = ?
            """,
            (status, verified_at, cert_id),
        )
        await db.commit()
