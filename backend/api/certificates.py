"""
Certificate endpoints.

GET /api/certificates          — paginated list of all certificates
GET /api/certificates/{id}     — single certificate by ID
GET /api/certificates/{id}/verify — verify NFT metadata against HCS via Mirror Node
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.config import settings
from backend.db import get_certificate, list_certificates, update_verification_status, tamper_certificate, restore_certificate
from backend.hedera.mirror import get_hcs_messages, get_nft_info

router = APIRouter(prefix="/api/certificates", tags=["certificates"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_certs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """Return a paginated list of certificates, newest first."""
    return await list_certificates(limit=limit, offset=offset)


@router.get("/{cert_id}")
async def get_cert(cert_id: int) -> dict[str, Any]:
    """Return a single certificate by ID."""
    cert = await get_certificate(cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert


@router.post("/{cert_id}/tamper")
async def tamper_cert(cert_id: int) -> dict[str, Any]:
    """Simulate tampering by corrupting the DB hash. For demo purposes."""
    try:
        result = await tamper_certificate(cert_id)
        return {"cert_id": cert_id, "status": "tampered", **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{cert_id}/restore")
async def restore_cert(cert_id: int) -> dict[str, Any]:
    """Restore original hash after tamper simulation."""
    try:
        result = await restore_certificate(cert_id)
        return {"cert_id": cert_id, "status": "restored", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cert_id}/verify")
async def verify_cert(cert_id: int) -> dict[str, Any]:
    """
    Verify a certificate by cross-checking NFT metadata against HCS via Mirror Node.

    Verification logic:
    1. Fetch the NFT from Mirror Node — confirms it exists on-chain
    2. Fetch the HCS message by sequence number — confirms the audit record
    3. Cross-check that the HCS message references the same task hashes

    Returns a verification report with status: "verified", "tampered", or "unanchored"
    """
    cert = await get_certificate(cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if not cert.get("nft_token_id") or not cert.get("nft_serial_number"):  # 0 treated as absent
        return {
            "cert_id": cert_id,
            "status": "unanchored",
            "message": "This certificate has no on-chain NFT — it was not published to Hedera.",
            "cert": cert,
        }

    network = settings.hedera_network
    nft_info: Optional[dict] = None
    hcs_message: Optional[dict] = None
    errors: list[str] = []

    # Step 1: Fetch NFT from Mirror Node
    try:
        nft_info = await get_nft_info(
            cert["nft_token_id"],
            cert["nft_serial_number"],
            network=network,
        )
    except Exception as exc:
        errors.append(f"NFT lookup failed: {exc}")
        logger.warning("NFT lookup failed for cert %d: %s", cert_id, exc)

    # Step 2: Fetch HCS message
    if cert.get("hcs_topic_id") and cert.get("hcs_sequence_number"):
        try:
            hcs_data = await get_hcs_messages(
                cert["hcs_topic_id"],
                sequence_number=int(cert["hcs_sequence_number"]),
                network=network,
            )
            # Mirror returns single message at /messages/{seq}
            messages = hcs_data.get("messages", [hcs_data])
            hcs_message = messages[0] if messages else hcs_data
        except Exception as exc:
            errors.append(f"HCS lookup failed: {exc}")
            logger.warning("HCS lookup failed for cert %d: %s", cert_id, exc)

    # Step 3: Cross-check
    verified = False
    tampered = False

    if hcs_message:
        decoded = hcs_message.get("message_decoded", "")
        if decoded:
            try:
                hcs_payload = json.loads(decoded)
                # Check input/output hashes match
                hcs_input_hash = hcs_payload.get("input_hash")
                hcs_output_hash = hcs_payload.get("output_hash")
                db_input_hash = cert.get("task_input_hash")
                db_output_hash = cert.get("task_output_hash")

                if hcs_input_hash == db_input_hash and hcs_output_hash == db_output_hash:
                    verified = True
                else:
                    tampered = True
                    errors.append(
                        f"Hash mismatch: HCS input_hash={hcs_input_hash} vs DB={db_input_hash}"
                    )
            except json.JSONDecodeError:
                errors.append("HCS message is not valid JSON")

    status = "verified" if verified else ("tampered" if tampered else "pending")

    # Update DB verification status
    if verified or tampered:
        from datetime import datetime, timezone
        await update_verification_status(
            cert_id,
            status=status,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    return {
        "cert_id": cert_id,
        "status": status,
        "verified": verified,
        "tampered": tampered,
        "nft_on_chain": nft_info is not None,
        "hcs_on_chain": hcs_message is not None,
        "errors": errors,
        "cert": cert,
        "nft_info": nft_info,
        "hcs_message": hcs_message,
    }
