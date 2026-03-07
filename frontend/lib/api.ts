const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface Certificate {
  id: number;
  task_type: string;
  task_input_hash: string;
  task_output_hash: string;
  agent_id: string;
  verdict: "approved" | "changes_requested" | "needs_review";
  summary: string;
  hcs_topic_id: string;
  hcs_sequence_number: string;
  nft_token_id: string;
  nft_serial_number: number;
  issues_json: string | null;
  created_at: string;
  verified_at: string | null;
  verification_status: "verified" | "tampered" | "pending" | null;
}

export interface VerifyResult {
  verified: boolean;
  status: string;
  details?: string;
  input_hash_match?: boolean;
  output_hash_match?: boolean;
  nft_found?: boolean;
  hcs_found?: boolean;
}

export interface ReviewPayload {
  code: string;
  language: string;
  repo?: string;
  pr_number?: number;
}

export async function getCertificates(): Promise<Certificate[]> {
  const res = await fetch(`${API_BASE}/api/certificates`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch certificates");
  return res.json();
}

export async function getCertificate(id: number): Promise<Certificate> {
  const res = await fetch(`${API_BASE}/api/certificates/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch certificate");
  return res.json();
}

export async function verifyCertificate(id: number): Promise<VerifyResult> {
  const res = await fetch(`${API_BASE}/api/certificates/${id}/verify`);
  if (!res.ok) throw new Error("Failed to verify certificate");
  return res.json();
}

export interface TamperResult {
  cert_id: number;
  status: string;
  original_hash: string;
  tampered_hash: string;
}

export async function tamperCertificate(id: number): Promise<TamperResult> {
  const res = await fetch(`${API_BASE}/api/certificates/${id}/tamper`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to tamper certificate");
  return res.json();
}

export async function restoreCertificate(id: number): Promise<{ cert_id: number; status: string; restored_hash: string }> {
  const res = await fetch(`${API_BASE}/api/certificates/${id}/restore`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to restore certificate");
  return res.json();
}

export async function submitReview(data: ReviewPayload): Promise<Certificate> {
  const res = await fetch(`${API_BASE}/api/tasks/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit review");
  return res.json();
}
