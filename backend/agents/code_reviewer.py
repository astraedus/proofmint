"""
AI code review agent with multi-tier model fallback.

Tier 1: Gemini (free, fast)
Tier 2: Simple rule-based analysis (always works, no API key required)

Returns a structured CodeReviewResult.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    severity: str       # "critical", "major", "minor", "suggestion"
    category: str       # "security", "correctness", "style", "performance"
    description: str
    line_hint: Optional[str] = None


@dataclass
class CodeReviewResult:
    verdict: str                          # "approved", "changes_requested", "needs_review"
    summary: str
    issues: list[CodeIssue] = field(default_factory=list)
    agent_id: str = "proofmint-code-reviewer-v1"
    model_used: str = "rule-based"

    def input_hash(self, code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    def output_hash(self) -> str:
        payload = f"{self.verdict}:{self.summary}:{len(self.issues)}"
        return hashlib.sha256(payload.encode()).hexdigest()


def _rule_based_review(code: str, language: str) -> CodeReviewResult:
    """
    Lightweight deterministic review — always available, no API key needed.
    Checks for common security and quality anti-patterns.
    """
    issues: list[CodeIssue] = []

    # Security patterns
    security_patterns = [
        (r"\beval\s*\(", "Use of eval() is dangerous — can execute arbitrary code"),
        (r"\bexec\s*\(", "Use of exec() is dangerous — can execute arbitrary code"),
        (r"os\.system\s*\(", "os.system() with unchecked input enables shell injection"),
        (r"subprocess\..*shell\s*=\s*True", "shell=True enables shell injection; prefer list args"),
        (r"md5\s*\(|hashlib\.md5", "MD5 is cryptographically broken; use SHA-256 or better"),
        (r"sha1\s*\(|hashlib\.sha1", "SHA-1 is cryptographically weak; use SHA-256 or better"),
        (r"random\.(random|randint|choice)\s*\(.*token|password|secret",
         "Use secrets module for security-sensitive random values"),
        (r"verify\s*=\s*False", "SSL verification disabled — MITM attacks possible"),
        (r"DEBUG\s*=\s*True", "Debug mode enabled — disable in production"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
    ]

    for pattern, description in security_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append(CodeIssue(
                severity="critical",
                category="security",
                description=description,
            ))

    # Quality patterns
    quality_patterns = [
        (r"except\s*:", "Bare except: catches all exceptions including SystemExit — be specific"),
        (r"except\s+Exception\s*:", "Catching Exception is too broad — narrow the exception type"),
        (r"print\s*\(", "Use logging instead of print() for production code"),
        (r"TODO|FIXME|HACK|XXX", "Unresolved TODO/FIXME comment in code"),
        (r"import \*", "Wildcard import pollutes namespace — use explicit imports"),
    ]

    for pattern, description in quality_patterns:
        if re.search(pattern, code):
            issues.append(CodeIssue(
                severity="minor",
                category="style",
                description=description,
            ))

    critical_count = sum(1 for i in issues if i.severity == "critical")
    major_count = sum(1 for i in issues if i.severity == "major")

    if critical_count > 0:
        verdict = "changes_requested"
        summary = (
            f"Found {critical_count} critical issue(s) that must be resolved before merge. "
            f"Total issues: {len(issues)}."
        )
    elif major_count > 0:
        verdict = "changes_requested"
        summary = (
            f"Found {major_count} major issue(s) requiring attention. "
            f"Total issues: {len(issues)}."
        )
    elif issues:
        verdict = "needs_review"
        summary = f"Minor issues found ({len(issues)}). Consider addressing before merge."
    else:
        verdict = "approved"
        summary = "No obvious issues detected by automated rule-based review."

    return CodeReviewResult(
        verdict=verdict,
        summary=summary,
        issues=issues,
        model_used="rule-based",
    )


async def _gemini_review(code: str, language: str, api_key: str) -> Optional[CodeReviewResult]:
    """
    AI-powered review via Gemini API (OpenAI-compatible endpoint).
    Returns None on failure so caller can fall back.
    """
    try:
        import httpx

        prompt = f"""You are a senior software engineer performing a code review.
Analyse the following {language} code for:
1. Security vulnerabilities (SQL injection, XSS, hardcoded secrets, etc.)
2. Correctness bugs
3. Code quality issues

Respond in this exact JSON format:
{{
  "verdict": "approved" | "changes_requested" | "needs_review",
  "summary": "one paragraph summary",
  "issues": [
    {{
      "severity": "critical" | "major" | "minor" | "suggestion",
      "category": "security" | "correctness" | "style" | "performance",
      "description": "clear description of the issue"
    }}
  ]
}}

Code to review:
```{language}
{code[:4000]}
```"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gemini-2.0-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1024,
                },
            )
            r.raise_for_status()
            data = r.json()

        import json
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        issues = [
            CodeIssue(
                severity=i.get("severity", "minor"),
                category=i.get("category", "style"),
                description=i.get("description", ""),
            )
            for i in parsed.get("issues", [])
        ]

        return CodeReviewResult(
            verdict=parsed.get("verdict", "needs_review"),
            summary=parsed.get("summary", ""),
            issues=issues,
            model_used="gemini-2.0-flash",
        )

    except Exception as exc:
        logger.warning("Gemini review failed: %s — falling back to rule-based", exc)
        return None


async def review_code(
    code: str,
    language: str = "python",
    gemini_api_key: str = "",
) -> CodeReviewResult:
    """
    Run a code review using the best available model.

    Args:
        code: Source code to review
        language: Programming language hint (e.g. "python", "javascript")
        gemini_api_key: Optional Gemini API key; if empty, skips AI tier

    Returns:
        CodeReviewResult with verdict, summary, and issues list
    """
    # Tier 1: Gemini AI
    if gemini_api_key:
        result = await _gemini_review(code, language, gemini_api_key)
        if result is not None:
            return result

    # Tier 2: Rule-based fallback
    logger.info("Using rule-based code review (no AI API key or AI unavailable)")
    return _rule_based_review(code, language)
