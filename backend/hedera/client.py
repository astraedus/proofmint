"""
Shared Hedera client setup.
Returns an operator-configured Client for testnet or mainnet.
"""
from __future__ import annotations

from hiero_sdk_python import AccountId, Client, PrivateKey


def get_client(account_id: str, private_key: str, network: str = "testnet") -> Client:
    """
    Build and return a Hedera client with operator set.

    Args:
        account_id: Hedera account ID string (e.g. "0.0.8112540")
        private_key: DER-encoded private key string
        network: "testnet" or "mainnet"

    Returns:
        Configured Client instance ready for transaction execution
    """
    aid = AccountId.from_string(account_id)
    pk = PrivateKey.from_string(private_key)

    if network == "mainnet":
        client = Client.for_mainnet()
    else:
        client = Client.for_testnet()

    client.set_operator(aid, pk)
    return client
