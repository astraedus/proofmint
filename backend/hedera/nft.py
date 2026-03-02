"""
Hedera Token Service (HTS) NFT operations.

Two-phase workflow:
  1. create_nft_collection — called once to create the NFT token type.
     Returns token ID string (store in HEDERA_NFT_TOKEN_ID env var).
  2. mint_nft — called per completed task, attaches metadata bytes,
     returns the serial number of the minted NFT.

Metadata convention: UTF-8 JSON blob, max ~100 bytes (HCS carries the full payload).
"""
from __future__ import annotations

import json
import logging

from hiero_sdk_python import (
    AccountId,
    PrivateKey,
    SupplyType,
    TokenCreateTransaction,
    TokenId,
    TokenMintTransaction,
    TokenType,
)

logger = logging.getLogger(__name__)


def create_nft_collection(
    client,
    account_id: str,
    private_key: str,
    name: str = "ProofMint Certificates",
    symbol: str = "PROOF",
    max_supply: int = 1_000_000,
) -> str:
    """
    Create a non-fungible token collection on HTS.

    The supply key is set to the operator key so minting is permissioned
    only to the holder of the private key (i.e. this backend).

    Args:
        client: Configured Hedera Client
        account_id: Operator account ID string (treasury for the token)
        private_key: Operator private key string (used as supply key)
        name: Human-readable token name
        symbol: Token symbol (ticker)
        max_supply: Maximum NFTs that can ever be minted

    Returns:
        Token ID string (e.g. "0.0.9876543")
    """
    pk = PrivateKey.from_string(private_key)
    treasury = AccountId.from_string(account_id)

    tx = (
        TokenCreateTransaction()
        .set_token_name(name)
        .set_token_symbol(symbol)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(max_supply)
        .set_treasury_account_id(treasury)
        .set_supply_key(pk.public_key())
        .set_initial_supply(0)
    )

    receipt = tx.execute(client)
    token_id_str = str(receipt.token_id)
    logger.info("Created NFT collection: %s (%s / %s)", token_id_str, name, symbol)
    return token_id_str


def mint_nft(
    client,
    token_id: str,
    metadata: dict,
) -> int:
    """
    Mint a single NFT in an existing collection.

    Args:
        client: Configured Hedera Client
        token_id: Token ID string (e.g. "0.0.9876543")
        metadata: Dict serialised to UTF-8 JSON bytes and attached to the NFT.
                  Keep it short — the full task details live on HCS.

    Returns:
        Serial number of the minted NFT (int, >= 1)
    """
    metadata_bytes = json.dumps(metadata, sort_keys=True).encode("utf-8")
    if len(metadata_bytes) > 100:
        # HTS metadata field has practical limits; we keep it as a pointer
        # to HCS rather than carrying the full payload here.
        logger.warning(
            "NFT metadata is %d bytes — consider shortening (HCS carries the full payload)",
            len(metadata_bytes),
        )

    tx = (
        TokenMintTransaction()
        .set_token_id(TokenId.from_string(token_id))
        .set_metadata([metadata_bytes])
    )

    receipt = tx.execute(client)

    # SDK returns serial_numbers as a protobuf RepeatedScalarContainer
    serials = receipt.serial_numbers
    serial = int(serials[0]) if len(serials) > 0 else 0

    logger.info("Minted NFT serial %d for token %s", serial, token_id)
    return serial
