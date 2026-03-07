# ProofMint

AI Agent Proof-of-Work NFT Certificates on Hedera.

AI agents perform tasks (code review, security audit). Each completed task:
1. Publishes full details to HCS (Hedera Consensus Service) — immutable audit record
2. Mints an NFT certificate on HTS (Hedera Token Service) referencing the HCS message
3. Anyone can verify the certificate by checking NFT metadata against HCS via Mirror Node

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Hedera testnet credentials from portal.hedera.com

uvicorn backend.main:app --reload
```

API docs: http://localhost:8000/docs

## Test NFT Minting

```bash
source venv/bin/activate
python3 scripts/test_nft_mint.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/tasks/review | Submit code for AI review — returns certificate |
| GET | /api/certificates | List all certificates |
| GET | /api/certificates/{id} | Get single certificate |
| GET | /api/certificates/{id}/verify | Verify certificate against Hedera |

## Architecture

```
POST /api/tasks/review
  -> AI Agent (Gemini / rule-based fallback)
  -> HCS: publish task details as immutable message
  -> HTS: mint NFT with metadata pointing at HCS message
  -> DB: persist certificate record
  -> Return CertificateRecord with all on-chain references

GET /api/certificates/{id}/verify
  -> Fetch NFT from Mirror Node
  -> Fetch HCS message from Mirror Node
  -> Cross-check hashes
  -> Return verification report
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| HEDERA_ACCOUNT_ID | Yes | Hedera account (e.g. 0.0.12345) |
| HEDERA_PRIVATE_KEY | Yes | DER-encoded private key |
| HEDERA_TOPIC_ID | No | HCS topic (auto-created if empty) |
| HEDERA_NFT_TOKEN_ID | No | NFT collection (auto-created if empty) |
| HEDERA_NETWORK | No | testnet (default) or mainnet |
| GEMINI_API_KEY | No | Enables AI-powered reviews (falls back to rules) |
| GITHUB_TOKEN | No | For future GitHub integration |

Get free testnet credentials: https://portal.hedera.com

## Hackathon Submissions

| Hackathon | Platform | Track | Status |
|-----------|----------|-------|--------|
| [Hedera Hello Future Apex 2026](https://hackathon.stackup.dev/web/events/hedera-hello-future-apex-hackathon-2026) | StackUp | AI & Agents | SUBMITTED (March 7, 2026) |

**Why this hackathon**: $250K prize pool, AI & Agents track. ProofMint was purpose-built for this — uses 3 Hedera services (HTS, HCS, Mirror Node) as structurally essential components.

**On-chain proof (testnet)**:
- NFT Collection: [0.0.8114539](https://hashscan.io/testnet/token/0.0.8114539)
- HCS Topic: [0.0.8114364](https://hashscan.io/testnet/topic/0.0.8114364)

**Live links**:
- Dashboard: [proofmint.vercel.app](https://proofmint.vercel.app)
- Demo Video: [youtu.be/iqDurB3gVp4](https://youtu.be/iqDurB3gVp4)

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **NFT metadata < 100 bytes** | HTS metadata has a hard limit. We store a compact pointer (`topic_id:seq_num:input_hash_prefix`) on the NFT, and full data on HCS. This keeps minting cheap while maintaining the complete audit trail on-chain. |
| **HCS before HTS** | Audit message published to HCS first, then NFT minted referencing the HCS sequence number. If HCS publish fails, no NFT is minted — ensures every certificate has a backing audit record. |
| **Rule-based AI fallback** | AI code reviewer uses rules first, Gemini API second. Ensures the system works without API keys and keeps costs at zero for basic reviews. |
| **SQLite + on-chain verification** | Local DB for fast reads; on-chain data as source of truth. The `/verify` endpoint cross-checks DB hashes against Mirror Node — if DB is tampered with, verification fails. |
| **hiero-sdk-python over REST API** | Native SDK provides proper transaction signing, receipt confirmation, and retry logic. REST API would require manual cryptographic signing. |
| **Separate HCS topic per deployment** | Each ProofMint instance creates its own HCS topic. Keeps audit trails isolated per organization. |

## Hedera Network Impact

Every AI task generates **3 Hedera transactions**: 1 HCS publish + 1 NFT mint + 1 Mirror Node query. AI agents run 24/7, making this a high-frequency use case that drives continuous TPS and account growth on Hedera. At $0.001/mint, per-task certification is only economically viable on Hedera — Ethereum would cost $2-50+ per mint.
