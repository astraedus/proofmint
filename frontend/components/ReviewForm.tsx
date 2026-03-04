"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { submitReview } from "@/lib/api";

const LANGUAGES = ["python", "javascript", "typescript", "go", "rust", "java", "c", "cpp", "ruby", "php", "other"];

interface Props {
  onClose: () => void;
}

const PROGRESS_MESSAGES = [
  "Analyzing code structure...",
  "Running AI agent review...",
  "Publishing to HCS topic...",
  "Minting NFT certificate...",
  "Finalizing on Hedera...",
];

export default function ReviewForm({ onClose }: Props) {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [repo, setRepo] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progressIdx, setProgressIdx] = useState(0);

  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setProgressIdx((i) => Math.min(i + 1, PROGRESS_MESSAGES.length - 1));
    }, 3000);
    return () => clearInterval(interval);
  }, [loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) {
      setError("Please paste some code to review.");
      return;
    }
    setError("");
    setLoading(true);
    setProgressIdx(0);

    try {
      const payload: { code: string; language: string; repo?: string; pr_number?: number } = {
        code: code.trim(),
        language,
      };
      if (repo.trim()) payload.repo = repo.trim();
      if (prNumber.trim()) payload.pr_number = parseInt(prNumber, 10);

      const cert = await submitReview(payload);
      router.push(`/certificates/${cert.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed. Is the backend running?");
      setLoading(false);
    }
  }

  // Prevent scroll behind modal
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={!loading ? onClose : undefined}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-black/60 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-semibold text-white">New Code Review</h2>
            <p className="text-sm text-slate-400 mt-0.5">AI agent reviews your code, mints an NFT certificate on Hedera</p>
          </div>
          {!loading && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Body */}
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-16 px-6">
            {/* Spinner */}
            <div className="relative w-16 h-16 mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-slate-800" />
              <div className="absolute inset-0 rounded-full border-4 border-t-[#00D4AA] animate-spin" />
            </div>
            <p className="text-white font-medium text-center mb-2">Processing your review...</p>
            <p className="text-slate-400 text-sm text-center min-h-[1.5rem] transition-all">
              {PROGRESS_MESSAGES[progressIdx]}
            </p>
            <p className="text-slate-600 text-xs mt-4">This takes ~10-15 seconds while Hedera confirms</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[#00D4AA]/50 focus:border-[#00D4AA]/50 transition"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </div>

              {/* Code */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Code</label>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Paste your code here..."
                  rows={12}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#00D4AA]/50 focus:border-[#00D4AA]/50 transition resize-none"
                  required
                />
              </div>

              {/* Optional fields */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Repo <span className="text-slate-600 font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                    placeholder="my-org/my-repo"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#00D4AA]/50 focus:border-[#00D4AA]/50 transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    PR # <span className="text-slate-600 font-normal">(optional)</span>
                  </label>
                  <input
                    type="number"
                    value={prNumber}
                    onChange={(e) => setPrNumber(e.target.value)}
                    placeholder="42"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#00D4AA]/50 focus:border-[#00D4AA]/50 transition"
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 text-sm font-semibold bg-[#00D4AA] hover:bg-[#00efc0] text-slate-950 rounded-lg transition-colors"
              >
                Submit Review
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
