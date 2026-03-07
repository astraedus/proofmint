#!/usr/bin/env python3
"""
ProofMint Hedera demo video recorder.
Creates HTML slides focused on HTS NFT + HCS + Mirror Node, records with Playwright, adds edge-tts narration.
Usage: cd /home/astraedus/projects/proofmint && source venv/bin/activate && python3 hedera-submission/record.py
Output: /tmp/proofmint-demo/proofmint-demo.mp4
"""
import asyncio, subprocess, time, os, sys
from pathlib import Path

DEMO = Path("/tmp/proofmint-demo")
VDIR = DEMO / "video"
ADIR = DEMO / "audio"
OUT = DEMO / "proofmint-demo.mp4"

for d in [VDIR, ADIR, DEMO]:
    d.mkdir(parents=True, exist_ok=True)

VOICE = "en-US-JennyNeural"

NARRATION = [
    ("00_hook",
     "AI agents are writing code, reviewing pull requests, and making decisions. "
     "But how do you prove what an AI agent actually did? "
     "A database can be edited. Logs can be deleted. "
     "You need cryptographic proof."),
    ("01_solution",
     "ProofMint mints an NFT certificate on Hedera for every AI agent task. "
     "The full work details go to Hedera Consensus Service. "
     "The NFT references the audit trail. "
     "Anyone can verify the certificate independently."),
    ("02_demo_review",
     "Watch it in action. We submit code with a hardcoded password and an eval call. "
     "The AI agent analyzes the code, finds three critical security issues, "
     "and generates a structured review. Now the interesting part happens."),
    ("03_nft_mint",
     "The review is published to a Hedera HCS topic as a JSON message with hashes, verdict, and timestamp. "
     "Then an NFT is minted in our ProofMint collection. "
     "The NFT metadata points directly to the HCS message. "
     "This is now permanently on the Hedera network."),
    ("04_hcs_audit",
     "On Hashscan, Hedera's block explorer, we can see the NFT in our collection. "
     "Serial number six, owned by our operator account. "
     "The metadata links to HCS topic zero point zero point eight one one four three six four, "
     "sequence number ten."),
    ("05_verify",
     "The verification endpoint cross-references everything. "
     "It fetches the NFT from the Mirror Node, fetches the HCS message, and compares the hashes. "
     "If anyone edits the database, the on-chain record will not match. "
     "Tamper-proof verification."),
    ("05b_tamper",
     "Now the key test. We corrupt the database. "
     "The output hash is changed to a fake value. "
     "Verification fetches the original hash from Hedera and compares. "
     "Mismatch detected. Status: tampered. "
     "Then we restore the original hash and verify again. Status: verified. "
     "The blockchain is the source of truth."),
    ("06_why_hedera",
     "ProofMint uses three Hedera services together. "
     "HTS for NFT certificates, each one a permanent proof of work. "
     "HCS for the full audit trail, ordered and timestamped by consensus. "
     "And the Mirror Node API for independent verification. "
     "NFT minting costs fractions of a cent. "
     "This would not be economically viable on Ethereum."),
    ("07_close",
     "ProofMint. Verifiable AI agent certificates on Hedera. "
     "Built with hiero SDK for Python, FastAPI, and Next.js. "
     "Every task certified. Every certificate verifiable. Every proof permanent."),
]

# --- HTML Slides ---
HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    width: 1280px; height: 720px; overflow: hidden;
    background: #020817;
    font-family: 'Segoe UI', system-ui, sans-serif;
    color: #e2e8f0;
  }
  .slide {
    position: absolute; top:0; left:0;
    width: 1280px; height: 720px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px;
    opacity: 0; transition: opacity 0.6s ease;
  }
  .slide.active { opacity: 1; }
  .accent { color: #8b5cf6; }
  .hedera { color: #00d4aa; }
  .dim { color: #718096; }

  /* Slide 0: Title */
  #s0 { background: linear-gradient(135deg, #020817 0%, #1a0a2e 50%, #0a1a2e 100%); }
  #s0 .logo {
    font-size: 80px; font-weight: 800; letter-spacing: -3px;
    background: linear-gradient(135deg, #8b5cf6, #00d4aa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
  }
  #s0 .tagline { font-size: 24px; color: #94a3b8; font-weight: 300; margin-bottom: 40px; }
  #s0 .badges { display: flex; gap: 12px; }
  #s0 .badge {
    padding: 8px 18px; border-radius: 20px; font-size: 13px; letter-spacing: 0.5px;
    border: 1px solid rgba(255,255,255,0.12);
  }
  .badge-hedera { background: rgba(0,212,170,0.15); border-color: #00d4aa; color: #00d4aa; }
  .badge-nft { background: rgba(139,92,246,0.15); border-color: #8b5cf6; color: #8b5cf6; }
  .badge-ai { background: rgba(59,130,246,0.15); border-color: #3b82f6; color: #3b82f6; }

  /* Slide 1: Problem */
  #s1 { background: #020817; }
  #s1 h2 { font-size: 42px; font-weight: 700; margin-bottom: 40px; }
  .problem-cards { display: flex; gap: 24px; }
  .pcard {
    flex: 1; background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 28px; text-align: center;
  }
  .pcard-icon { font-size: 40px; margin-bottom: 12px; }
  .pcard-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
  .pcard-desc { font-size: 14px; color: #94a3b8; line-height: 1.5; }

  /* Slide 2: How It Works */
  #s2 { background: #020817; }
  #s2 h2 { font-size: 38px; font-weight: 700; margin-bottom: 36px; }
  .flow { display: flex; align-items: center; gap: 10px; }
  .flow-step {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 20px 14px; text-align: center; flex: 1;
  }
  .flow-num {
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #8b5cf6, #00d4aa);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; margin: 0 auto 10px;
  }
  .flow-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
  .flow-desc { font-size: 11px; color: #94a3b8; }
  .flow-arrow { color: #4a5568; font-size: 20px; }

  /* Slide 3: NFT + HCS */
  #s3 { background: #020817; align-items: flex-start; padding: 40px 60px; }
  #s3 h2 { font-size: 32px; font-weight: 700; margin-bottom: 20px; width: 100%; }
  .dual-box { display: flex; gap: 20px; width: 100%; }
  .json-box {
    flex: 1; background: #0d1117; border-radius: 10px;
    border: 1px solid #30363d; overflow: hidden;
  }
  .json-bar {
    background: #161b22; padding: 10px 16px;
    display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #30363d;
  }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .dot-r { background: #ff5f57; } .dot-y { background: #febc2e; } .dot-g { background: #28c840; }
  .json-title { margin-left: 8px; font-size: 12px; color: #6e7681; }
  .json-body { padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.7; }
  .j-key { color: #79c0ff; } .j-str { color: #a5d6ff; } .j-num { color: #d2a8ff; }
  .j-brace { color: #6e7681; }
  .hcs-badge {
    display: inline-block; padding: 4px 12px; border-radius: 12px;
    background: rgba(0,212,170,0.15); color: #00d4aa; font-size: 12px; font-weight: 600;
    margin-left: 8px; vertical-align: middle;
  }
  .nft-badge {
    display: inline-block; padding: 4px 12px; border-radius: 12px;
    background: rgba(139,92,246,0.15); color: #8b5cf6; font-size: 12px; font-weight: 600;
    margin-left: 8px; vertical-align: middle;
  }

  /* Slide 4: Hashscan NFT */
  #s4 { background: #020817; }
  #s4 h2 { font-size: 38px; font-weight: 700; margin-bottom: 30px; }
  .hashscan-mock {
    width: 90%; background: #0d1117; border-radius: 10px;
    border: 1px solid #30363d; padding: 28px; text-align: left;
  }
  .hs-header { font-size: 14px; color: #00d4aa; font-weight: 600; margin-bottom: 16px; letter-spacing: 0.5px; }
  .hs-row { display: flex; padding: 10px 0; border-bottom: 1px solid #21262d; }
  .hs-label { width: 160px; color: #6e7681; font-size: 13px; }
  .hs-value { color: #e6edf3; font-size: 13px; font-family: monospace; }
  .hs-link { color: #58a6ff; text-decoration: underline; }
  .hs-nft { color: #8b5cf6; }

  /* Slide 5: Verification */
  #s5 { background: #020817; }
  #s5 h2 { font-size: 38px; font-weight: 700; margin-bottom: 30px; }
  .verify-box {
    width: 85%; background: #0d1117; border-radius: 10px;
    border: 1px solid #30363d; padding: 28px;
  }
  .verify-row { display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #21262d; }
  .verify-icon { width: 40px; font-size: 22px; text-align: center; }
  .verify-check { color: #3fb950; }
  .verify-label { flex: 1; font-size: 14px; }
  .verify-status { font-size: 13px; font-weight: 600; }
  .status-ok { color: #3fb950; }
  .status-match { color: #00d4aa; }

  /* Slide 5b: Tamper Detection */
  #s5b { background: #020817; align-items: flex-start; padding: 40px 60px; }
  #s5b h2 { font-size: 32px; font-weight: 700; margin-bottom: 20px; width: 100%; }
  .tamper-split { display: flex; gap: 20px; width: 100%; margin-bottom: 16px; }
  .tamper-box {
    flex: 1; border-radius: 10px; padding: 20px;
    border: 1px solid #30363d; background: #0d1117;
  }
  .tamper-box-bad { border-color: #f85149; background: rgba(248,81,73,0.08); }
  .tamper-box-good { border-color: #3fb950; background: rgba(63,185,80,0.08); }
  .tamper-label {
    font-size: 11px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; margin-bottom: 8px;
  }
  .tamper-label-bad { color: #f85149; }
  .tamper-label-good { color: #3fb950; }
  .tamper-hash { font-family: monospace; font-size: 13px; word-break: break-all; line-height: 1.6; }
  .tamper-result {
    width: 100%; text-align: center; padding: 16px;
    border-radius: 10px; font-size: 18px; font-weight: 700;
  }
  .tamper-result-bad { background: rgba(248,81,73,0.12); border: 1px solid #f85149; color: #f85149; }
  .tamper-result-good { background: rgba(0,212,170,0.12); border: 1px solid #00d4aa; color: #00d4aa; }
  .tamper-arrow { text-align: center; font-size: 24px; color: #6e7681; margin: 8px 0; }

  /* Slide 6: Why Hedera */
  #s6 { background: #020817; }
  #s6 h2 { font-size: 38px; font-weight: 700; margin-bottom: 36px; }
  .why-cards { display: flex; gap: 16px; }
  .wcard {
    flex: 1; background: rgba(0,212,170,0.05);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 12px; padding: 24px; text-align: center;
  }
  .wcard-title { font-size: 15px; font-weight: 600; color: #00d4aa; margin-bottom: 8px; }
  .wcard-desc { font-size: 12px; color: #94a3b8; line-height: 1.5; }
  .wcard-nft { border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.05); }
  .wcard-nft .wcard-title { color: #8b5cf6; }

  /* Slide 7: Close */
  #s7 { background: linear-gradient(135deg, #020817 0%, #1a0a2e 50%, #0a1a2e 100%); }
  #s7 .big {
    font-size: 64px; font-weight: 800;
    background: linear-gradient(135deg, #8b5cf6, #00d4aa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
  }
  #s7 .sub { font-size: 20px; color: #94a3b8; margin-bottom: 36px; }
  .pills { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
  .pill {
    padding: 8px 18px; border-radius: 20px; font-size: 13px; font-weight: 600;
    border: 1px solid rgba(255,255,255,0.12); color: #94a3b8;
  }
  .pill-h { background: rgba(0,212,170,0.15); border-color: #00d4aa; color: #00d4aa; }
  .pill-n { background: rgba(139,92,246,0.15); border-color: #8b5cf6; color: #8b5cf6; }
</style>
</head>
<body>

<!-- Slide 0: Title -->
<div class="slide active" id="s0">
  <div class="logo">ProofMint</div>
  <div class="tagline">Verifiable AI Agent Certificates on Hedera</div>
  <div class="badges">
    <div class="badge badge-nft">NFT CERTIFICATES</div>
    <div class="badge badge-hedera">HEDERA HCS + HTS</div>
    <div class="badge badge-ai">AI AGENTS</div>
  </div>
</div>

<!-- Slide 1: Problem -->
<div class="slide" id="s1">
  <h2>The <span class="accent">AI Trust</span> Problem</h2>
  <div class="problem-cards">
    <div class="pcard">
      <div class="pcard-icon">?</div>
      <div class="pcard-title">No Proof of Work</div>
      <div class="pcard-desc">AI agents do tasks but leave no verifiable record. Did the review actually happen? What exactly was analyzed?</div>
    </div>
    <div class="pcard">
      <div class="pcard-icon">!</div>
      <div class="pcard-title">Mutable Records</div>
      <div class="pcard-desc">Database entries can be edited. Logs can be deleted. Nothing proves an AI agent did what it claims.</div>
    </div>
    <div class="pcard">
      <div class="pcard-icon">$</div>
      <div class="pcard-title">No Accountability</div>
      <div class="pcard-desc">As AI makes more decisions, we need auditable proof. Compliance teams need evidence they can trust.</div>
    </div>
  </div>
</div>

<!-- Slide 2: How It Works -->
<div class="slide" id="s2">
  <h2>How <span class="hedera">ProofMint</span> Works</h2>
  <div class="flow">
    <div class="flow-step">
      <div class="flow-num">1</div>
      <div class="flow-title">Submit Code</div>
      <div class="flow-desc">Code or PR to review</div>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <div class="flow-num">2</div>
      <div class="flow-title">AI Reviews</div>
      <div class="flow-desc">Security + quality scan</div>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <div class="flow-num">3</div>
      <div class="flow-title">HCS Publish</div>
      <div class="flow-desc">Full details on-chain</div>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <div class="flow-num">4</div>
      <div class="flow-title">NFT Minted</div>
      <div class="flow-desc">Certificate on HTS</div>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <div class="flow-num">5</div>
      <div class="flow-title">Verify</div>
      <div class="flow-desc">Mirror Node proof</div>
    </div>
  </div>
</div>

<!-- Slide 3: HCS + NFT Messages -->
<div class="slide" id="s3">
  <h2>On-Chain Record <span class="hcs-badge">HCS</span> <span class="nft-badge">NFT</span></h2>
  <div class="dual-box">
    <div class="json-box">
      <div class="json-bar">
        <div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div>
        <div class="json-title">HCS Message (Topic 0.0.8114364)</div>
      </div>
      <div class="json-body">
        <span class="j-brace">{</span><br>
        &nbsp;&nbsp;<span class="j-key">"type"</span>: <span class="j-str">"code_review"</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"verdict"</span>: <span class="j-str">"changes_requested"</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"input_hash"</span>: <span class="j-str">"d7a86d..."</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"output_hash"</span>: <span class="j-str">"97999..."</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"issues_count"</span>: <span class="j-num">3</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"timestamp"</span>: <span class="j-str">"2026-03-07"</span><br>
        <span class="j-brace">}</span>
      </div>
    </div>
    <div class="json-box">
      <div class="json-bar">
        <div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div>
        <div class="json-title">NFT Metadata (Token 0.0.8114539)</div>
      </div>
      <div class="json-body">
        <span class="j-brace">{</span><br>
        &nbsp;&nbsp;<span class="j-key">"v"</span>: <span class="j-str">"chan"</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"t"</span>: <span class="j-str">"0.0.8114364"</span>,<br>
        &nbsp;&nbsp;<span class="j-key">"s"</span>: <span class="j-str">"10"</span><br>
        <span class="j-brace">}</span><br><br>
        <span class="dim" style="font-size:11px">NFT points to HCS topic + sequence.<br>Full data lives on HCS.</span>
      </div>
    </div>
  </div>
</div>

<!-- Slide 4: Hashscan NFT -->
<div class="slide" id="s4">
  <h2>Verify on <span class="hedera">Hashscan</span></h2>
  <div class="hashscan-mock">
    <div class="hs-header">HASHSCAN.IO / TESTNET / TOKEN / 0.0.8114539</div>
    <div class="hs-row"><div class="hs-label">Collection</div><div class="hs-value hs-nft">ProofMint Certificates (PROOF)</div></div>
    <div class="hs-row"><div class="hs-label">Type</div><div class="hs-value">NON_FUNGIBLE_UNIQUE</div></div>
    <div class="hs-row"><div class="hs-label">Serial #6</div><div class="hs-value">Owner: 0.0.8112540</div></div>
    <div class="hs-row"><div class="hs-label">Metadata</div><div class="hs-value">{"v":"chan","t":"0.0.8114364","s":"10"}</div></div>
    <div class="hs-row"><div class="hs-label">HCS Topic</div><div class="hs-value hs-link">0.0.8114364 (10 messages)</div></div>
    <div class="hs-row"><div class="hs-label">Supply Key</div><div class="hs-value">ECDSA_SECP256K1 (operator-controlled)</div></div>
  </div>
</div>

<!-- Slide 5: Verification -->
<div class="slide" id="s5">
  <h2>On-Chain <span class="hedera">Verification</span></h2>
  <div class="verify-box">
    <div class="verify-row">
      <div class="verify-icon verify-check">&#10003;</div>
      <div class="verify-label">NFT exists on Hedera Token Service</div>
      <div class="verify-status status-ok">CONFIRMED</div>
    </div>
    <div class="verify-row">
      <div class="verify-icon verify-check">&#10003;</div>
      <div class="verify-label">HCS message found at sequence #10</div>
      <div class="verify-status status-ok">CONFIRMED</div>
    </div>
    <div class="verify-row">
      <div class="verify-icon verify-check">&#10003;</div>
      <div class="verify-label">Input hash matches on-chain record</div>
      <div class="verify-status status-match">MATCH</div>
    </div>
    <div class="verify-row">
      <div class="verify-icon verify-check">&#10003;</div>
      <div class="verify-label">Output hash matches on-chain record</div>
      <div class="verify-status status-match">MATCH</div>
    </div>
    <div class="verify-row">
      <div class="verify-icon verify-check">&#10003;</div>
      <div class="verify-label">NFT metadata references correct HCS message</div>
      <div class="verify-status status-match">LINKED</div>
    </div>
    <div class="verify-row" style="border:none">
      <div class="verify-icon" style="font-size:28px; color:#00d4aa">&#9733;</div>
      <div class="verify-label" style="font-size:18px; font-weight:700; color:#00d4aa">Certificate VERIFIED</div>
      <div class="verify-status" style="font-size:15px; color:#00d4aa">TAMPER-PROOF</div>
    </div>
  </div>
</div>

<!-- Slide 5b: Tamper Detection -->
<div class="slide" id="s5b">
  <h2>Tamper <span style="color:#f85149">Detection</span> Demo</h2>
  <div class="tamper-split">
    <div class="tamper-box tamper-box-bad">
      <div class="tamper-label tamper-label-bad">Corrupted Database Hash</div>
      <div class="tamper-hash" style="color:#f85149">TAMPERED_493d4546<br>46af45515e96d442<br>60e50dee48a41852</div>
    </div>
    <div class="tamper-box tamper-box-good">
      <div class="tamper-label tamper-label-good">Original Hash on Hedera (HCS)</div>
      <div class="tamper-hash" style="color:#3fb950">493d454646af4551<br>5e96d44260e50dee<br>48a41852861b9034</div>
    </div>
  </div>
  <div class="tamper-result tamper-result-bad" style="margin-bottom: 12px;">
    HASHES DON'T MATCH &mdash; TAMPERING DETECTED
  </div>
  <div class="tamper-arrow">&darr; Restore original hash &darr;</div>
  <div class="tamper-result tamper-result-good">
    HASHES MATCH &mdash; CERTIFICATE VERIFIED
  </div>
</div>

<!-- Slide 6: Why Hedera -->
<div class="slide" id="s6">
  <h2>Three <span class="hedera">Hedera</span> Services, One System</h2>
  <div class="why-cards">
    <div class="wcard wcard-nft">
      <div class="wcard-title">HTS - NFT Certificates</div>
      <div class="wcard-desc">Each task mints a unique NFT. Permanent, transferable proof of AI agent work. $0.001 per mint.</div>
    </div>
    <div class="wcard">
      <div class="wcard-title">HCS - Audit Trail</div>
      <div class="wcard-desc">Full task details published as ordered, timestamped messages. Immutable by consensus.</div>
    </div>
    <div class="wcard">
      <div class="wcard-title">Mirror Node - Verification</div>
      <div class="wcard-desc">REST API to query NFTs and HCS messages. Anyone can independently verify certificates.</div>
    </div>
  </div>
</div>

<!-- Slide 7: Close -->
<div class="slide" id="s7">
  <div class="big">ProofMint</div>
  <div class="sub">Every task certified. Every certificate verifiable. Every proof permanent.</div>
  <div class="pills">
    <div class="pill pill-h">Hedera HTS</div>
    <div class="pill pill-h">Hedera HCS</div>
    <div class="pill pill-h">Mirror Node API</div>
    <div class="pill pill-n">hiero-sdk-python</div>
    <div class="pill">FastAPI</div>
    <div class="pill">Next.js</div>
    <div class="pill">AI Agents</div>
  </div>
</div>

<script>
const TIMINGS = [
  { id: 's0', start: 0,   end: 12  },
  { id: 's1', start: 12,  end: 24  },
  { id: 's2', start: 24,  end: 44  },
  { id: 's3', start: 44,  end: 59  },
  { id: 's4', start: 59,  end: 74  },
  { id: 's5', start: 74,  end: 89  },
  { id: 's5b', start: 89,  end: 109 },
  { id: 's6', start: 109, end: 129 },
  { id: 's7', start: 129, end: 145 },
];
let start = Date.now();
function tick() {
  let elapsed = (Date.now() - start) / 1000;
  TIMINGS.forEach(t => {
    let el = document.getElementById(t.id);
    if (elapsed >= t.start && elapsed < t.end) el.classList.add('active');
    else el.classList.remove('active');
  });
  requestAnimationFrame(tick);
}
tick();
</script>
</body>
</html>"""


async def gen_audio():
    import edge_tts
    for name, text in NARRATION:
        path = ADIR / f"{name}.mp3"
        if path.exists():
            print(f"  skip {name}")
            continue
        await edge_tts.Communicate(text, VOICE).save(str(path))
        print(f"  ok   {name}")


def duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def record():
    from playwright.sync_api import sync_playwright

    html_path = DEMO / "slides.html"
    html_path.write_text(HTML)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VDIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = ctx.new_page()
        page.goto(f"file://{html_path}", wait_until="domcontentloaded")
        time.sleep(1)

        total = 150
        print(f"  recording {total}s of slides...")
        time.sleep(total)

        vid = page.video.path()
        ctx.close()
        browser.close()
        print(f"  raw video: {vid}")
        return vid


def combine(raw_video):
    list_f = DEMO / "audio_list.txt"
    audios = [ADIR / f"{name}.mp3" for name, _ in NARRATION]
    list_f.write_text("".join(f"file '{a}'\n" for a in audios))

    narration = DEMO / "narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_f), "-c", "copy", str(narration)],
        check=True, capture_output=True)

    adur = duration(narration)
    vdur = duration(raw_video)
    print(f"  audio: {adur:.1f}s  video: {vdur:.1f}s")

    speed = vdur / adur
    print(f"  speed factor: {speed:.3f}x")

    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", str(narration),
        "-filter:v", f"setpts={1/speed:.4f}*PTS",
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        str(OUT)
    ], check=True)

    mb = OUT.stat().st_size / 1024 / 1024
    dur = duration(OUT)
    print(f"\n  {OUT}  ({mb:.1f} MB, {dur:.0f}s)")


async def main():
    print("=== ProofMint Demo Recorder ===\n")

    print("[1/3] Generating narration audio...")
    await gen_audio()

    print("\n[2/3] Recording slides...")
    raw = await asyncio.get_event_loop().run_in_executor(None, record)

    print("\n[3/3] Combining audio + video...")
    combine(raw)
    print("\nDone!")

asyncio.run(main())
