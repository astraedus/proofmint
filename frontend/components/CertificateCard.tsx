import Link from "next/link";
import { Certificate } from "@/lib/api";
import VerificationBadge from "./VerificationBadge";

interface Props {
  cert: Certificate;
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const isApprove = verdict === "approved";
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${
        isApprove
          ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400"
          : "bg-red-500/10 border-red-500/25 text-red-400"
      }`}
    >
      {isApprove ? (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
        </svg>
      ) : (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      {isApprove ? "Approved" : "Changes Requested"}
    </span>
  );
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr.replace(" ", "T") + "Z");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default function CertificateCard({ cert }: Props) {
  return (
    <Link href={`/certificates/${cert.id}`} className="block group">
      <div className="relative bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-600 transition-all duration-200 hover:shadow-lg hover:shadow-black/40 hover:-translate-y-0.5">
        {/* NFT Badge */}
        <div className="absolute top-4 right-4">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/30 text-violet-400 text-xs font-medium">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm0 14a6 6 0 110-12 6 6 0 010 12z"/>
            </svg>
            #{cert.nft_serial_number}
          </span>
        </div>

        {/* Task type */}
        <div className="mb-3">
          <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">
            {cert.task_type.replace(/_/g, " ")}
          </span>
        </div>

        {/* Summary */}
        <p className="text-slate-300 text-sm leading-relaxed mb-4 line-clamp-2 pr-12">
          {cert.summary || "No summary available"}
        </p>

        {/* Bottom row */}
        <div className="flex items-center justify-between mt-auto">
          <div className="flex items-center gap-2">
            <VerdictBadge verdict={cert.verdict} />
            <VerificationBadge status={cert.verification_status} />
          </div>
          <span className="text-xs text-slate-600 tabular-nums">
            {formatDate(cert.created_at)}
          </span>
        </div>

        {/* Token ID */}
        <div className="mt-3 pt-3 border-t border-slate-800">
          <span className="text-xs font-mono text-slate-600">
            {cert.nft_token_id} · seq {cert.hcs_sequence_number}
          </span>
        </div>
      </div>
    </Link>
  );
}
