"""
Task submission endpoints.

POST /api/tasks/review — submit code for AI review, get back a certificate
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.core.orchestrator import CertificateRecord, run_code_review

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

_MAX_CODE_BYTES = 100_000  # 100 KB


class CodeReviewRequest(BaseModel):
    code: str = Field(..., description="Source code to review")
    language: str = Field(default="python", description="Programming language hint")
    submitter_id: Optional[str] = Field(
        default=None,
        description="Optional identifier for the submitting agent or user",
        max_length=128,
    )

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("code must not be empty")
        if len(v.encode()) > _MAX_CODE_BYTES:
            raise ValueError(f"code exceeds maximum size of {_MAX_CODE_BYTES} bytes")
        return v

    @field_validator("language")
    @classmethod
    def language_alphanumeric(cls, v: str) -> str:
        # Prevent injection via language field
        if not v.replace("-", "").replace("+", "").replace("#", "").isalnum():
            raise ValueError("language must be alphanumeric")
        return v.lower()


class CodeReviewResponse(BaseModel):
    cert_id: int
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


@router.post("/review", response_model=CodeReviewResponse)
async def submit_code_review(body: CodeReviewRequest) -> CodeReviewResponse:
    """
    Submit source code for AI-powered review.

    The agent analyses the code, publishes a verifiable record to Hedera HCS,
    and mints an NFT certificate. Returns the full certificate including
    on-chain references.
    """
    try:
        record: CertificateRecord = await run_code_review(
            code=body.code,
            language=body.language,
            submitter_id=body.submitter_id,
        )
    except Exception as exc:
        logger.error("Code review pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Review pipeline error: {exc}")

    return CodeReviewResponse(
        cert_id=record.id,
        task_type=record.task_type,
        verdict=record.verdict,
        summary=record.summary,
        agent_id=record.agent_id,
        model_used=record.model_used,
        input_hash=record.input_hash,
        output_hash=record.output_hash,
        hcs_topic_id=record.hcs_topic_id,
        hcs_sequence_number=record.hcs_sequence_number,
        hcs_url=record.hcs_url,
        nft_token_id=record.nft_token_id,
        nft_serial_number=record.nft_serial_number,
        nft_url=record.nft_url,
        issues=record.issues,
        created_at=record.created_at,
    )
