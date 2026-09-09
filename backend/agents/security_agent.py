"""
Security Auditor Agent for DebugVerse.
Performs automated vulnerability scans, OWASP Top 10 analysis,
hardcoded secrets discovery, and security remediation.
"""

from typing import Dict, Any, Optional
from backend.agents.base_agent import BaseAgent


class SecurityAgent(BaseAgent):
    agent_id = "security"
    display_name = "Security Auditor"
    description = "Scans for OWASP Top 10, injection vulnerabilities, leaked secrets, and insecure patterns."
    model_preference = "claude-3-5-sonnet"  # Prefers Claude for deep security reasoning, falls back to Gemini

    def build_system_prompt(self, language: str) -> str:
        return f"""You are the DebugVerse Security Auditor Agent — an elite AppSec and DevSecOps security researcher.
Your job is to rigorously review the provided {language} code for:
1. Critical Vulnerabilities (SQL injection, Command injection, XSS, Path Traversal, SSRF, Deserialization, ReDoS).
2. Authentication & Authorization flaws (broken access controls, insecure JWT/session handling, missing checks).
3. Secrets & Sensitive Data Leakage (hardcoded credentials, API keys, unmasked PII, insecure logging).
4. Memory & Resource Safety (buffer overflows, race conditions, uncontrolled resource consumption).
5. Insecure Functions & Deprecated APIs.

FORMAT YOUR RESPONSE CLEARLY IN MARKDOWN:
### Security Posture Summary
- **Overall Risk Rating**: [SECURE | LOW | MEDIUM | HIGH | CRITICAL]
- **Vulnerabilities Found**: [Number of issues]

### Vulnerability Breakdown
For each issue found (or state "No security vulnerabilities identified" if clean):
- **Issue**: [Vulnerability Title e.g. SQL Injection via Unsanitized Input]
- **Severity**: [CRITICAL / HIGH / MEDIUM / LOW]
- **CWE / OWASP**: [e.g. CWE-89, OWASP A03:2021]
- **Vulnerable Code**:
```
[snippet]
```
- **Exploitation Scenario**: How an attacker could exploit this.
- **Remediation**: Exact fix instructions.

### Hardened Code Remediation
Provide the complete, secure, production-ready replacement for the vulnerable section.
"""

    def build_user_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> str:
        ctx_str = ""
        if context and context.get("error"):
            ctx_str = f"\nRuntime / Execution Error context:\n{context['error']}\n"

        return f"""Please perform a thorough security audit on the following {language} code:{ctx_str}

```{language}
{code}
```
"""
