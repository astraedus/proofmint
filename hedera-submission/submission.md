# Hedera Hello Future Apex -- ProofMint Submission

## Track
AI & Agents

## Title
ProofMint -- Verifiable AI Agent Certificates on Hedera

## Description (100 words max)
ProofMint mints NFT certificates on Hedera for every AI agent task. When an AI agent reviews code, the full work details are published to Hedera Consensus Service, then an NFT is minted via Hedera Token Service referencing the HCS message. Anyone can verify a certificate by querying the Mirror Node REST API to cross-reference the NFT metadata against the HCS audit trail. Three Hedera services work together: HTS for permanent proof-of-work certificates, HCS for ordered immutable audit logs, and Mirror Node for independent verification. Built with hiero-sdk-python, FastAPI, and Next.js.

## Tech Stack
- Hedera Token Service (HTS) via hiero-sdk-python -- NFT collection + minting
- Hedera Consensus Service (HCS) via hiero-sdk-python -- audit trail
- Hedera Mirror Node REST API -- verification queries
- FastAPI (Python backend)
- Next.js 15 (certificate dashboard)
- SQLite (local state)
- AI code review agent (rule-based + Gemini fallback)
- edge-tts (demo narration)

## How Hedera Is Used

**Three Hedera services are structurally essential:**

1. **HTS NFT Collection**: On first run, ProofMint creates an NFT collection (token 0.0.8114539 on testnet, type NON_FUNGIBLE_UNIQUE, supply key = operator). This is the certificate registry.

2. **HCS Audit Trail**: After every AI task, the full details (input hash, output hash, verdict, issues, timestamp) are published to an HCS topic (0.0.8114364). This is the immutable, ordered record of what the AI did.

3. **HTS NFT Minting**: After HCS publish, an NFT is minted with compact metadata pointing to the HCS message (topic ID + sequence number). The NFT is the transferable, permanent certificate.

4. **Mirror Node Verification**: The verify endpoint fetches the NFT metadata from Mirror Node, extracts the HCS reference, fetches the HCS message, and compares hashes. If the local database is tampered with, the on-chain hashes will not match.

### Concrete Hedera Transactions (all confirmed on testnet)
- `TokenCreateTransaction` -- created NFT collection 0.0.8114539
- `TokenMintTransaction` -- minted serials 1-6 (each a certificate)
- `TopicCreateTransaction` -- created HCS topic 0.0.8114364
- `TopicMessageSubmitTransaction` -- published 10 audit messages
- Mirror Node queries: `/api/v1/tokens/{id}/nfts/{serial}`, `/api/v1/topics/{id}/messages`

## Why This Can't Exist Without Hedera

Remove any one service and the system breaks:
- Without HTS: No transferable proof-of-work certificates
- Without HCS: No immutable audit trail for the NFT to reference
- Without Mirror Node: No independent verification (must trust the database)

The combination is unique to Hedera: low-cost NFT minting ($0.001/mint), native HCS for ordered message logging (no smart contract needed), and Mirror Node for permissionless verification. On Ethereum, per-task NFT minting would cost $2-50 in gas, making it economically unviable.

## Repo
https://github.com/astraedus/proofmint

## Live Demo
- NFT Collection: https://hashscan.io/testnet/token/0.0.8114539
- HCS Topic: https://hashscan.io/testnet/topic/0.0.8114364
- Dashboard: (will be deployed)

## Demo Video
(YouTube link -- to be recorded)

## Team
Diven Rastdus -- full-stack + AI engineer, solo builder
