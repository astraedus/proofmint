"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { getCertificate, verifyCertificate, tamperCertificate, restoreCertificate, Certificate, VerifyResult, TamperResult } from "@/lib/api";
import VerificationBadge from "@/components/VerificationBadge";
import HashscanLink from "@/components/HashscanLink";

function formatDate(dateStr: string) {
  const d = new Date(dateStr.replace(" ", "T") + "Z");
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function InfoRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 py-3 border-b border-slate-800 last:border-0">
      <span className="text-sm text-slate-500 sm:w-44 flex-shrink-0">{label}</span>
      <span className={`text-sm text-slate-200 break-all ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}

export default function CertificatePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [cert, setCert] = useState<Certificate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [verifyError, setVerifyError] = useState("");
  const [tampering, setTampering] = useState(false);
  const [tamperResult, setTamperResult] = useState<TamperResult | null>(null);
  const [restoring, setRestoring] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getCertificate(Number(id));
        setCert(data);
      } catch {
        setError("Certificate not found.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function handleVerify() {
    setVerifying(true);
    setVerifyError("");
    setVerifyResult(null);
    try {
      const result = await verifyCertificate(Number(id));
      setVerifyResult(result);
      // Update cert verification status
      if (cert) {
        setCert({
          ...cert,
          verification_status: result.verified ? "verified" : "tampered",
          verified_at: new Date().toISOString(),
        });
      }
    } catch {
      setVerifyError("Verification failed. The Hedera Mirror Node may take 30-60 seconds to index new transactions.");
    } finally {
      setVerifying(false);
    }
  }

  async function handleTamper() {
    setTampering(true);
    setVerifyResult(null);
    setVerifyError("");
    try {
      const result = await tamperCertificate(Number(id));
      setTamperResult(result);
      // Update displayed hash
      if (cert) {
        setCert({ ...cert, task_output_hash: result.tampered_hash, verification_status: "pending" });
      }
      // Auto-verify after 1.5s to show mismatch
      setTimeout(() => handleVerify(), 1500);
    } catch {
      setVerifyError("Tamper simulation failed.");
    } finally {
      setTampering(false);
    }
  }

  async function handleRestore() {
    setRestoring(true);
    setVerifyResult(null);
    setVerifyError("");
    try {
      const result = await restoreCertificate(Number(id));
      setTamperResult(null);
      if (cert) {
        setCert({ ...cert, task_output_hash: result.restored_hash, verification_status: "pending" });
      }
      // Auto-verify after 1s to confirm restored
      setTimeout(() => handleVerify(), 1000);
    } catch {
      setVerifyError("Restore failed.");
    } finally {
      setRestoring(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="relative w-10 h-10">
          <div className="absolute inset-0 rounded-full border-4 border-slate-800" />
          <div className="absolute inset-0 rounded-full border-4 border-t-[#00D4AA] animate-spin" />
        </div>
        <p className="text-slate-500 text-sm">Loading certificate...</p>
      </div>
    );
  }

  if (error || !cert) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
        <p className="text-red-400 font-medium">{error || "Certificate not found"}</p>
        <Link href="/" className="text-sm text-[#00D4AA] hover:underline">
          Back to gallery
        </Link>
      </div>
    );
  }

  const isApprove = cert.verdict === "approved";

  return (
    <div className="max-w-3xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link href="/" className="hover:text-white transition-colors">Certificates</Link>
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
        <span className="text-slate-400">Certificate #{cert.id}</span>
      </div>

      {/* Header card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap mb-3">
              {/* Verdict badge */}
              <span
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold border ${
                  isApprove
                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                    : "bg-red-500/15 border-red-500/30 text-red-400"
                }`}
              >
                {isApprove ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                {isApprove ? "Approved" : "Changes Requested"}
              </span>

              {/* NFT badge */}
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-500/15 border border-violet-500/30 text-violet-400 text-sm font-medium">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
                NFT #{cert.nft_serial_number}
              </span>

              <VerificationBadge status={cert.verification_status} size="md" />
            </div>

            <p className="text-slate-300 text-base leading-relaxed">{cert.summary}</p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-slate-500 block text-xs uppercase tracking-wider mb-1">Task Type</span>
            <span className="text-slate-200 font-medium">{cert.task_type.replace(/_/g, " ")}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs uppercase tracking-wider mb-1">Agent</span>
            <span className="text-slate-200 font-mono text-xs">{cert.agent_id}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs uppercase tracking-wider mb-1">Submitted</span>
            <span className="text-slate-200">{formatDate(cert.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Issues */}
      {cert.issues_json && JSON.parse(cert.issues_json).length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-4">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-white">Issues Found</h2>
          </div>
          <div className="space-y-2">
            {JSON.parse(cert.issues_json).map((issue: { severity: string; category: string; description: string }, i: number) => {
              const colors: Record<string, string> = {
                critical: "border-red-500/30 bg-red-500/10 text-red-400",
                major: "border-orange-500/30 bg-orange-500/10 text-orange-400",
                minor: "border-yellow-500/30 bg-yellow-500/10 text-yellow-400",
                suggestion: "border-blue-500/30 bg-blue-500/10 text-blue-400",
              };
              const color = colors[issue.severity] || colors.minor;
              return (
                <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${color}`}>
                  <span className="text-xs font-bold uppercase tracking-wider mt-0.5 flex-shrink-0 w-16">
                    {issue.severity}
                  </span>
                  <div className="flex-1">
                    <span className="text-xs text-slate-500 uppercase tracking-wider">{issue.category}</span>
                    <p className="text-sm mt-0.5">{issue.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Hedera Proof */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-4">
        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg bg-[#00D4AA]/15 flex items-center justify-center">
            <svg className="w-4 h-4 text-[#00D4AA]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-white">Hedera Proof</h2>
        </div>

        <div className="space-y-0">
          <InfoRow
            label="NFT Token"
            value={
              <HashscanLink
                href={`https://hashscan.io/testnet/token/${cert.nft_token_id}/${cert.nft_serial_number}`}
                label={`${cert.nft_token_id} / Serial #${cert.nft_serial_number}`}
              />
            }
          />
          <InfoRow
            label="HCS Topic"
            value={
              <HashscanLink
                href={`https://hashscan.io/testnet/topic/${cert.hcs_topic_id}`}
                label={`${cert.hcs_topic_id} / Seq ${cert.hcs_sequence_number}`}
              />
            }
          />
          <InfoRow label="Input Hash" value={cert.task_input_hash} mono />
          <InfoRow label="Output Hash" value={cert.task_output_hash} mono />
          {cert.verified_at && (
            <InfoRow label="Verified At" value={formatDate(cert.verified_at)} />
          )}
        </div>
      </div>

      {/* Tamper Simulation */}
      <div className="bg-slate-900 border border-red-500/30 rounded-2xl p-6 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-white">Tamper Detection Demo</h2>
          </div>

          <div className="flex gap-2">
            {!tamperResult ? (
              <button
                onClick={handleTamper}
                disabled={tampering}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-red-600 hover:bg-red-500 disabled:bg-red-800 disabled:opacity-60 text-white rounded-lg transition-colors"
              >
                {tampering ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Tampering...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Simulate Tamper
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleRestore}
                disabled={restoring}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 disabled:opacity-60 text-white rounded-lg transition-colors"
              >
                {restoring ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Restoring...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                    </svg>
                    Restore Original
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        <p className="text-sm text-slate-400 mb-4">
          Corrupt the database hash to simulate a tampered record. Then verify on-chain to see ProofMint detect the mismatch.
        </p>

        {tamperResult && (
          <div className="space-y-2 text-sm">
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/25">
              <span className="text-xs text-emerald-400 font-medium uppercase tracking-wider">Original Hash (on Hedera)</span>
              <span className="font-mono text-emerald-300 text-xs break-all">{tamperResult.original_hash}</span>
            </div>
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-red-500/10 border border-red-500/25">
              <span className="text-xs text-red-400 font-medium uppercase tracking-wider">Corrupted Hash (in DB)</span>
              <span className="font-mono text-red-300 text-xs break-all">{tamperResult.tampered_hash}</span>
            </div>
          </div>
        )}
      </div>

      {/* Verify On-Chain */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-violet-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75l-2.489-2.489m0 0a3.375 3.375 0 10-4.773-4.773 3.375 3.375 0 004.774 4.774zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-white">On-Chain Verification</h2>
          </div>

          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800 disabled:opacity-60 text-white rounded-lg transition-colors"
          >
            {verifying ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Verify On-Chain
              </>
            )}
          </button>
        </div>

        <p className="text-sm text-slate-400 mb-4">
          Cross-check the NFT metadata against the HCS audit record via the Hedera Mirror Node.
          {" "}
          <span className="text-slate-500">Note: new certificates may take 30-60 seconds to index.</span>
        </p>

        {verifyError && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
            <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            {verifyError}
          </div>
        )}

        {verifyResult && (
          <div
            className={`p-4 rounded-xl border ${
              verifyResult.verified
                ? "bg-emerald-500/10 border-emerald-500/25"
                : "bg-red-500/10 border-red-500/25"
            }`}
          >
            <div className="flex items-center gap-2 mb-3">
              {verifyResult.verified ? (
                <>
                  <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-emerald-400 font-semibold">Certificate Verified</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-red-400 font-semibold">Verification Failed</span>
                </>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {[
                { label: "NFT Found", value: verifyResult.nft_found },
                { label: "HCS Found", value: verifyResult.hcs_found },
                { label: "Input Hash", value: verifyResult.input_hash_match },
                { label: "Output Hash", value: verifyResult.output_hash_match },
              ].map(({ label, value }) => (
                <div key={label} className="flex flex-col gap-1">
                  <span className="text-slate-500">{label}</span>
                  {value === undefined ? (
                    <span className="text-slate-600">—</span>
                  ) : value ? (
                    <span className="text-emerald-400 font-medium">Match</span>
                  ) : (
                    <span className="text-red-400 font-medium">Mismatch</span>
                  )}
                </div>
              ))}
            </div>

            {verifyResult.details && (
              <p className="mt-3 text-xs text-slate-400 border-t border-slate-700 pt-3">
                {verifyResult.details}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Back link */}
      <div className="mt-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to gallery
        </Link>
      </div>
    </div>
  );
}
