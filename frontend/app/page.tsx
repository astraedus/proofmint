"use client";

import { useState, useEffect } from "react";
import { getCertificates, Certificate } from "@/lib/api";
import CertificateCard from "@/components/CertificateCard";
import ReviewForm from "@/components/ReviewForm";

export default function HomePage() {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  async function load() {
    try {
      setLoading(true);
      const data = await getCertificates();
      // newest first
      setCertificates([...data].reverse());
      setError("");
    } catch {
      setError("Could not connect to backend. Make sure the API is running on port 8001.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function handleFormClose() {
    setShowForm(false);
    // Reload certs in case new one was created (user didn't submit)
    load();
  }

  return (
    <>
      {/* Hero */}
      <section className="mb-10">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#00D4AA]/10 border border-[#00D4AA]/20 text-[#00D4AA] text-xs font-medium mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D4AA] animate-pulse" />
              Live on Hedera Testnet
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              ProofMint
            </h1>
            <p className="mt-2 text-slate-400 text-lg">
              Verifiable AI Agent Certificates on Hedera
            </p>
            <p className="mt-1.5 text-slate-500 text-sm max-w-lg">
              Every code review is published to HCS and minted as an NFT — creating a tamper-proof audit trail you can verify on-chain.
            </p>
          </div>

          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#00D4AA] hover:bg-[#00efc0] text-slate-950 font-semibold text-sm rounded-xl transition-colors shadow-lg shadow-[#00D4AA]/20 flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Review
          </button>
        </div>

        {/* Stats bar */}
        {!loading && !error && (
          <div className="flex items-center gap-6 mt-6 pt-6 border-t border-slate-800">
            <div>
              <span className="text-2xl font-bold text-white">{certificates.length}</span>
              <span className="ml-2 text-sm text-slate-400">Certificates</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-emerald-400">
                {certificates.filter((c) => c.verdict === "approve").length}
              </span>
              <span className="ml-2 text-sm text-slate-400">Approved</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-red-400">
                {certificates.filter((c) => c.verdict === "reject").length}
              </span>
              <span className="ml-2 text-sm text-slate-400">Rejected</span>
            </div>
            <div>
              <span className="text-2xl font-bold text-[#00D4AA]">
                {certificates.filter((c) => c.verification_status === "verified").length}
              </span>
              <span className="ml-2 text-sm text-slate-400">Verified On-Chain</span>
            </div>
          </div>
        )}
      </section>

      {/* Content */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 rounded-full border-4 border-slate-800" />
            <div className="absolute inset-0 rounded-full border-4 border-t-[#00D4AA] animate-spin" />
          </div>
          <p className="text-slate-500 text-sm">Loading certificates...</p>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400">
          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <div>
            <p className="font-medium">Backend unreachable</p>
            <p className="text-sm mt-0.5 text-red-400/70">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && certificates.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.745 3.745 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.745 3.745 0 013.296-1.043A3.745 3.745 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.745 3.745 0 013.296 1.043 3.745 3.745 0 011.043 3.296A3.745 3.745 0 0121 12z" />
            </svg>
          </div>
          <div>
            <p className="text-white font-medium">No certificates yet</p>
            <p className="text-slate-500 text-sm mt-1">Submit your first code review to mint an NFT certificate</p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 px-5 py-2.5 bg-[#00D4AA] hover:bg-[#00efc0] text-slate-950 font-semibold text-sm rounded-xl transition-colors"
          >
            Submit First Review
          </button>
        </div>
      )}

      {!loading && !error && certificates.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {certificates.map((cert) => (
            <CertificateCard key={cert.id} cert={cert} />
          ))}
        </div>
      )}

      {showForm && <ReviewForm onClose={handleFormClose} />}
    </>
  );
}
