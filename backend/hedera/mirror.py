"""
Hedera Mirror Node REST API queries.

Mirror nodes index all Hedera network activity and expose a REST API.
We use them to verify NFT metadata and retrieve HCS messages without
requiring a live node connection.

Docs: https://docs.hedera.com/hedera/sdks-and-apis/rest-api
"""
from __future__ import annotations

import base64
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_MIRROR_BASES = {
    "testnet": "https://testnet.mirrornode.hedera.com",
    "mainnet": "https://mainnode.mirrornode.hedera.com",
}


def _base(network: str = "testnet") -> str:
    return _MIRROR_BASES.get(network, _MIRROR_BASES["testnet"])


async def get_nft_info(token_id: str, serial: int, network: str = "testnet") -> dict[str, Any]:
    """
    Fetch NFT metadata and ownership info from Mirror Node.

    Args:
        token_id: Token ID string (e.g. "0.0.9876543")
        serial: NFT serial number
        network: "testnet" or "mainnet"

    Returns:
        Mirror Node JSON response dict
    """
    url = f"{_base(network)}/api/v1/tokens/{token_id}/nfts/{serial}"
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(url)
        r.raise_for_status()
        data = r.json()
        # Decode base64 metadata for convenience
        if "metadata" in data and data["metadata"]:
            try:
                data["metadata_decoded"] = base64.b64decode(data["metadata"]).decode("utf-8")
            except Exception:
                data["metadata_decoded"] = None
        return data


async def get_hcs_messages(
    topic_id: str,
    sequence_number: Optional[int] = None,
    network: str = "testnet",
) -> dict[str, Any]:
    """
    Retrieve HCS messages for a topic from Mirror Node.

    Args:
        topic_id: Topic ID string (e.g. "0.0.8114364")
        sequence_number: If given, fetch the specific message by sequence number
        network: "testnet" or "mainnet"

    Returns:
        Mirror Node JSON response dict (has "messages" list key)
    """
    if sequence_number is not None:
        url = f"{_base(network)}/api/v1/topics/{topic_id}/messages/{sequence_number}"
    else:
        url = f"{_base(network)}/api/v1/topics/{topic_id}/messages"

    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(url)
        r.raise_for_status()
        data = r.json()
        # Decode base64 message content for convenience
        messages = data.get("messages") if isinstance(data.get("messages"), list) else [data]
        for msg in messages:
            if "message" in msg and msg["message"]:
                try:
                    msg["message_decoded"] = base64.b64decode(msg["message"]).decode("utf-8")
                except Exception:
                    msg["message_decoded"] = None
        return data


def hashscan_nft_url(token_id: str, serial: int, network: str = "testnet") -> str:
    """Return a HashScan URL for an NFT."""
    return f"https://hashscan.io/{network}/token/{token_id}/{serial}"


def hashscan_topic_url(topic_id: str, network: str = "testnet") -> str:
    """Return a HashScan URL for an HCS topic."""
    return f"https://hashscan.io/{network}/topic/{topic_id}"
