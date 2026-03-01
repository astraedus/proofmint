"""
Standalone test script: mint one NFT on Hedera testnet.

Run from the proofmint project root:
    source venv/bin/activate
    python3 scripts/test_nft_mint.py

This script:
1. Loads credentials from .env
2. Creates a new NFT collection (or uses existing HEDERA_NFT_TOKEN_ID)
3. Submits a test message to HCS (or uses existing HEDERA_TOPIC_ID)
4. Mints one NFT with metadata pointing at the HCS message
5. Prints HashScan URLs for verification
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

HEDERA_ACCOUNT_ID = os.environ.get("HEDERA_ACCOUNT_ID", "")
HEDERA_PRIVATE_KEY = os.environ.get("HEDERA_PRIVATE_KEY", "")
HEDERA_TOPIC_ID = os.environ.get("HEDERA_TOPIC_ID", "")
HEDERA_NFT_TOKEN_ID = os.environ.get("HEDERA_NFT_TOKEN_ID", "")
HEDERA_NETWORK = os.environ.get("HEDERA_NETWORK", "testnet")


def _check_env() -> None:
    missing = [k for k in ("HEDERA_ACCOUNT_ID", "HEDERA_PRIVATE_KEY") if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        print("Copy the values from your .env file or set them in the shell.")
        sys.exit(1)


def _hashscan_nft(token_id: str, serial: int) -> str:
    return f"https://hashscan.io/{HEDERA_NETWORK}/token/{token_id}/{serial}"


def _hashscan_topic(topic_id: str) -> str:
    return f"https://hashscan.io/{HEDERA_NETWORK}/topic/{topic_id}"


def main() -> None:
    _check_env()

    print(f"\nProofMint NFT Mint Test — {HEDERA_NETWORK}")
    print("=" * 50)

    from backend.hedera.client import get_client
    from backend.hedera.hcs import create_topic, submit_message
    from backend.hedera.nft import create_nft_collection, mint_nft

    # Build client
    print(f"\n[1/4] Connecting to Hedera {HEDERA_NETWORK}...")
    client = get_client(HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY, HEDERA_NETWORK)
    print(f"      Operator: {HEDERA_ACCOUNT_ID}")

    # HCS topic
    if HEDERA_TOPIC_ID:
        topic_id = HEDERA_TOPIC_ID
        print(f"\n[2/4] Using existing HCS topic: {topic_id}")
    else:
        print("\n[2/4] Creating new HCS topic...")
        topic_id = create_topic(client, memo="ProofMint Test")
        print(f"      Created topic: {topic_id}")
        print(f"      Add to .env: HEDERA_TOPIC_ID={topic_id}")

    # Submit HCS message
    print("\n[3/4] Submitting test message to HCS...")
    payload = {
        "type": "code_review",
        "agent_id": "proofmint-test-agent-v1",
        "verdict": "approved",
        "summary": "Test review: code looks good",
        "input_hash": "abc123",
        "output_hash": "def456",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    seq = submit_message(client, topic_id, payload)
    print(f"      Sequence number: {seq}")
    print(f"      HashScan: {_hashscan_topic(topic_id)}")

    # NFT collection
    if HEDERA_NFT_TOKEN_ID:
        nft_token_id = HEDERA_NFT_TOKEN_ID
        print(f"\n[4/4] Using existing NFT collection: {nft_token_id}")
    else:
        print("\n[4/4] Creating new NFT collection...")
        nft_token_id = create_nft_collection(
            client,
            account_id=HEDERA_ACCOUNT_ID,
            private_key=HEDERA_PRIVATE_KEY,
            name="ProofMint Test Certificates",
            symbol="PTEST",
        )
        print(f"      Created collection: {nft_token_id}")
        print(f"      Add to .env: HEDERA_NFT_TOKEN_ID={nft_token_id}")

    # Mint NFT
    print("\n      Minting NFT...")
    nft_metadata = {
        "type": "proof_of_work",
        "task": "code_review",
        "verdict": "approved",
        "hcs_topic": topic_id,
        "hcs_seq": seq,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    serial = mint_nft(client, nft_token_id, nft_metadata)

    print("\n" + "=" * 50)
    print("SUCCESS!")
    print(f"  NFT Token:    {nft_token_id}")
    print(f"  Serial:       {serial}")
    print(f"  HCS Topic:    {topic_id}")
    print(f"  HCS Seq:      {seq}")
    print(f"  NFT URL:      {_hashscan_nft(nft_token_id, serial)}")
    print(f"  Topic URL:    {_hashscan_topic(topic_id)}")
    print("=" * 50)
    print("\nNote: It may take 30-60 seconds for transactions to appear on HashScan.")


if __name__ == "__main__":
    main()
