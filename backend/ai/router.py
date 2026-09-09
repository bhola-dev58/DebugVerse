"""
Intelligent Model Router for DebugVerse.
Classifies code complexity and latency sensitivity to optimize
cost and accuracy across available AI providers.
"""

from typing import Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

COMPLEX_INDICATORS = [
    r"\bthread\b", r"\basyncio\b", r"\bmutex\b", r"\block\b", r"\bpointer\b",
    r"\brecursive\b", r"\bdp\b", r"\bdynamic programming\b", r"\bmemory leak\b",
    r"\brace condition\b", r"\bsegmentation fault\b", r"\bdeadlock\b",
    r"\bconcurrency\b", r"\bgenerics\b", r"\btemplate\b", r"\balloc\b",
]


class ModelRouter:
    @staticmethod
    def classify_complexity(code: str, language: str) -> Dict[str, Any]:
        """
        Heuristically classifies problem complexity into 'simple', 'moderate', or 'complex'.
        """
        line_count = len(code.strip().splitlines())
        code_lower = code.lower()

        is_complex = False
        matched_indicators = []
        for pattern in COMPLEX_INDICATORS:
            if re.search(pattern, code_lower):
                is_complex = True
                matched_indicators.append(pattern.replace(r"\b", ""))

        if is_complex or line_count > 45:
            tier = "complex"
            recommended_model = "claude-3-5-sonnet"
            reason = f"Identified complex patterns ({', '.join(matched_indicators[:3]) if matched_indicators else 'long codebase'})"
        elif line_count <= 8:
            tier = "simple"
            recommended_model = "gemini-2-5-flash"
            reason = "Short code snippet ideal for high-speed triage"
        else:
            tier = "moderate"
            recommended_model = "auto"
            reason = "Standard algorithmic logic"

        return {
            "tier": tier,
            "recommended_model": recommended_model,
            "line_count": line_count,
            "reason": reason,
        }
