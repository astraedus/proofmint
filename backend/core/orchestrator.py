"""
Task orchestrator: the core pipeline for ProofMint.

For each submitted task:
  1. Run the AI agent (code review, etc.)
  2. Publish full details to HCS (immutable record)
  3. Mint an NFT referencing the HCS message
  4. Persist everything to the DB
  5. Return a CertificateRecord

All on-chain operations are non-blocking — if Hedera is unconfigured
or fails, we still save the result locally and surface the error clearly.
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.agents.code_reviewer import CodeReviewResult, review_code
from backend.config import settings
from backend.db import save_certificate
from backend.hedera.client import get_client
from backend.hedera.hcs import create_topic, submit_message
from backend.hedera.mirror import hashscan_nft_url, hashscan_topic_url
from backend.hedera.nft import create_nft_collection, mint_nft

logger = logging.getLogger(__name__)


@dataclass
class CertificateRecord:
    id: int
    task_type: str
    verdict: str
    summary: str
    agent_id: str
    model_used: str
    input_hash: str
    output_hash: str
    hcs_topic_id: Optional[str]
    hcs_sequence_number: Optional[str]
    hcs_url: Optional[str]
    nft_token_id: Optional[str]
    nft_serial_number: Optional[int]
    nft_url: Optional[str]
    issues: list[dict]
    created_at: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _is_hedera_configured() -> bool:
    return bool(settings.hedera_account_id and settings.hedera_private_key)


def _get_client():
    return get_client(
        settings.hedera_account_id,
        settings.hedera_private_key,
        settings.hedera_network,
    )


def _ensure_topic(client) -> str:
    """Return existing topic ID or create a new one and warn operator."""
    if settings.hedera_topic_id:
        return settings.hedera_topic_id
    logger.warning("HEDERA_TOPIC_ID not set — creating a new HCS topic (set env var to reuse)")
    return create_topic(client, memo="ProofMint Agent Certificates")


def _ensure_nft_collection(client) -> str:
    """Return existing NFT token ID or create a new collection and warn operator."""
    if settings.hedera_nft_token_id:
        return settings.hedera_nft_token_id
    logger.warning(
        "HEDERA_NFT_TOKEN_ID not set — creating a new NFT collection (set env var to reuse)"
    )
    return create_nft_collection(
        client,
        account_id=settings.hedera_account_id,
        private_key=settings.hedera_private_key,
    )


async def run_code_review(
    code: str,
    language: str = "python",
    submitter_id: Optional[str] = None,
) -> CertificateRecord:
    """
    Full pipeline: AI code review -> HCS -> NFT -> DB.

    Args:
        code: Source code to review
        language: Programming language hint
        submitter_id: Optional identifier for the entity submitting the task

    Returns:
        CertificateRecord with full traceability data
    """
    # Step 1: AI agent
    result: CodeReviewResult = await review_code(
        code=code,
        language=language,
        gemini_api_key=settings.gemini_api_key,
    )

    input_hash = _sha256(code)
    output_hash = result.output_hash()
    created_at = datetime.now(timezone.utc).isoformat()

    # Step 2: HCS publication
    hcs_topic_id: Optional[str] = None
    hcs_sequence_number: Optional[str] = None
    hcs_url: Optional[str] = None
    nft_token_id: Optional[str] = None
    nft_serial_number: Optional[int] = None
    nft_url: Optional[str] = None

    if _is_hedera_configured():
        try:
            client = _get_client()
            hcs_topic_id = _ensure_topic(client)

            hcs_payload = {
                "type": "code_review",
                "agent_id": result.agent_id,
                "model_used": result.model_used,
                "language": language,
                "submitter_id": submitter_id,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "verdict": result.verdict,
                "summary": result.summary[:500],
                "issues_count": len(result.issues),
                "timestamp": created_at,
            }
            hcs_sequence_number = submit_message(client, hcs_topic_id, hcs_payload)
            hcs_url = hashscan_topic_url(hcs_topic_id, settings.hedera_network)
            logger.info("HCS message submitted: topic=%s seq=%s", hcs_topic_id, hcs_sequence_number)

            # Step 3: Mint NFT — metadata must stay <=100 bytes; full data lives on HCS
            nft_token_id = _ensure_nft_collection(client)
            nft_metadata = {
                "v": result.verdict[:4],      # "appr" / "chan" / "need"
                "t": hcs_topic_id,
                "s": hcs_sequence_number,
            }
            nft_serial_number = mint_nft(client, nft_token_id, nft_metadata)
            nft_url = hashscan_nft_url(nft_token_id, nft_serial_number, settings.hedera_network)
            logger.info("NFT minted: token=%s serial=%d", nft_token_id, nft_serial_number)

        except Exception as exc:
            logger.error("Hedera operations failed: %s", exc, exc_info=True)
            # Non-fatal: certificate is still saved locally

    # Step 4: Persist to DB
    cert_id = await save_certificate(
        task_type="code_review",
        task_input_hash=input_hash,
        task_output_hash=output_hash,
        agent_id=result.agent_id,
        verdict=result.verdict,
        summary=result.summary,
        hcs_topic_id=hcs_topic_id,
        hcs_sequence_number=hcs_sequence_number,
        nft_token_id=nft_token_id,
        nft_serial_number=nft_serial_number,
        verification_status="verified" if nft_serial_number else "pending",
    )

    return CertificateRecord(
        id=cert_id,
        task_type="code_review",
        verdict=result.verdict,
        summary=result.summary,
        agent_id=result.agent_id,
        model_used=result.model_used,
        input_hash=input_hash,
        output_hash=output_hash,
        hcs_topic_id=hcs_topic_id,
        hcs_sequence_number=hcs_sequence_number,
        hcs_url=hcs_url,
        nft_token_id=nft_token_id,
        nft_serial_number=nft_serial_number,
        nft_url=nft_url,
        issues=[
            {
                "severity": i.severity,
                "category": i.category,
                "description": i.description,
                "line_hint": i.line_hint,
            }
            for i in result.issues
        ],
        created_at=created_at,
    )
