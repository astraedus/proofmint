# ProofMint — Lessons

## Hedera SDK (hiero-sdk-python 0.2.x)

### TokenCreateTransaction API
- Use method chaining: `.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE).set_supply_type(SupplyType.FINITE)` etc.
- `set_supply_key` takes a `PublicKey` object, not a `PrivateKey` — call `pk.public_key()`
- `set_initial_supply(0)` is required for NFT collections

### TokenMintTransaction
- `set_metadata` takes a list of bytes objects, one per NFT to mint: `.set_metadata([metadata_bytes])`
- Receipt serial numbers: check `receipt.serial_numbers` (list) first, then `receipt.serial_number` (singular)
- **CRITICAL: NFT metadata has a hard ~100-byte limit on HTS.** If metadata exceeds this, the tx executes but `serial_numbers` returns EMPTY — no error raised, serial silently becomes 0. Keep metadata to an absolute minimum (a compact JSON pointer to HCS is enough). Full data goes on HCS.
- Zero is NOT a valid serial number — treat `serial == 0` as a mint failure (falsy check: `if not serial_number`)

### TopicMessageSubmitTransaction
- `message` arg should be bytes, not str: encode first with `.encode("utf-8")`
- Sequence number on receipt: `receipt.topic_sequence_number` (may be None on some versions) — also check `receipt.sequence_number`

### Client setup
- `tx.execute(client)` both executes AND gets the receipt internally — do NOT call `get_receipt()` separately

## Mirror Node

- Mirror Node may take 30-60 seconds to index fresh transactions — verification calls can return 404 briefly
- NFT metadata is returned as base64 — always decode before comparing
- HCS message content is also base64 on the mirror node response

## Project structure
- `.env` is gitignored — credentials must be copied manually or set via environment
- `HEDERA_NFT_TOKEN_ID` starts empty — auto-created on first review submission, but operator should save and set it to avoid creating a new collection each restart
