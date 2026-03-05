# ProofMint Demo Narration
# Voice: en-US-JennyNeural (female)
# Target: 2-3 minutes
# Focus: Hedera HTS + HCS + Mirror Node deep integration

---

## Segments

| # | Name | Duration | Text |
|---|------|----------|------|
| 00 | hook | ~12s | Hook: AI trust problem |
| 01 | solution | ~12s | What ProofMint does |
| 02 | demo_review | ~20s | Show code review + certificate minting |
| 03 | nft_mint | ~15s | Show NFT on Hashscan |
| 04 | hcs_audit | ~15s | Show HCS audit trail |
| 05 | verify | ~15s | Show verification flow |
| 06 | why_hedera | ~20s | Why Hedera is essential |
| 07 | close | ~12s | Closing + tech credits |

---

## NARRATION TEXT

### 00_hook
"AI agents are writing code, reviewing pull requests, and making decisions. But how do you prove what an AI agent actually did? A database can be edited. Logs can be deleted. You need cryptographic proof."

### 01_solution
"ProofMint mints an NFT certificate on Hedera for every AI agent task. The full work details go to Hedera Consensus Service. The NFT references the audit trail. Anyone can verify the certificate independently."

### 02_demo_review
"Watch it in action. We submit code with a hardcoded password and an eval call. The AI agent analyzes the code, finds three critical security issues, and generates a structured review. Now the interesting part happens."

### 03_nft_mint
"The review is published to a Hedera HCS topic as a JSON message with hashes, verdict, and timestamp. Then an NFT is minted in our ProofMint collection. The NFT metadata points directly to the HCS message. This is now permanently on the Hedera network."

### 04_hcs_audit
"On Hashscan, Hedera's block explorer, we can see the NFT in our collection. Serial number six, owned by our operator account. The metadata links to HCS topic zero point zero point eight one one four three six four, sequence number ten."

### 05_verify
"The verification endpoint cross-references everything. It fetches the NFT from the Mirror Node, fetches the HCS message, and compares the hashes. If anyone edits the database, the on-chain record will not match. Tamper-proof verification."

### 06_why_hedera
"ProofMint uses three Hedera services together. HTS for NFT certificates, each one a permanent proof of work. HCS for the full audit trail, ordered and timestamped by consensus. And the Mirror Node API for independent verification. NFT minting costs fractions of a cent. This would not be economically viable on Ethereum."

### 07_close
"ProofMint. Verifiable AI agent certificates on Hedera. Built with hiero SDK for Python, FastAPI, and Next.js. Every task certified. Every certificate verifiable. Every proof permanent."
