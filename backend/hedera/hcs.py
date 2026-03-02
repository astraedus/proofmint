"""
Hedera Consensus Service (HCS) operations.

- create_topic: create a new HCS topic, return topic ID string
- submit_message: publish a dict payload to an existing topic, return sequence number
"""
from __future__ import annotations

import json
import logging

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.consensus.topic_id import TopicId

logger = logging.getLogger(__name__)


def create_topic(client, memo: str = "ProofMint Agent Certificates") -> str:
    """
    Create a new HCS topic.

    Args:
        client: Configured Hedera Client
        memo: Human-readable topic memo

    Returns:
        Topic ID string (e.g. "0.0.1234567")
    """
    tx = TopicCreateTransaction(memo=memo)
    receipt = tx.execute(client)
    topic_id_str = str(receipt.topic_id)
    logger.info("Created HCS topic: %s", topic_id_str)
    return topic_id_str


def submit_message(client, topic_id: str, payload: dict) -> str:
    """
    Submit a JSON payload to an HCS topic.

    Args:
        client: Configured Hedera Client
        topic_id: Topic ID string (e.g. "0.0.8114364")
        payload: Dict to serialise as JSON message

    Returns:
        Sequence number string of the submitted message
    """
    message_str = json.dumps(payload, sort_keys=True)
    tx = TopicMessageSubmitTransaction(
        topic_id=TopicId.from_string(topic_id),
        message=message_str,
    )
    receipt = tx.execute(client)

    # SDK receipt may expose sequence_number differently by version
    seq = getattr(receipt, "topic_sequence_number", None)
    if seq is None:
        seq = getattr(receipt, "sequence_number", "0")

    seq_str = str(seq)
    logger.info("Submitted HCS message to %s — sequence %s", topic_id, seq_str)
    return seq_str
