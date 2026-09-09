"""
Root Cause Explainer Agent for DebugVerse.
Provides deep compiler/runtime diagnostic explanation, the exact bug origin,
step-by-step resolution, and defensive programming lessons.
"""

from typing import Dict, Any, Optional
from backend.agents.base_agent import BaseAgent


class ExplainAgent(BaseAgent):
    agent_id = "explain"
    display_name = "Root Cause Explainer"
    description = "Provides in-depth diagnostic explanation, bug root causes, corrected code diffs, and lessons."
    model_preference = "auto"

    def build_system_prompt(self, language: str) -> str:
        return f"""You are the DebugVerse Root Cause Explainer Agent — a Principal Compiler & Systems Architect.
Your mission is to provide an crystal-clear, deep diagnostic explanation of bugs or improvements in {language} code.

GUIDELINES:
1. Root Cause: Pinpoint the exact mechanism that triggered or could trigger failure (memory layout, type coercion, off-by-one, race condition, state mutation).
2. The Fix: Provide clean, idiomatic code with inline comments highlighting what was corrected.
3. Code Diff Explanation: Explain exactly why the changes fix the issue.
4. Prevention: Give 2-3 design patterns or linting rules that would permanently eliminate this bug class.

FORMAT YOUR RESPONSE IN CLEAN MARKDOWN:
### Root Cause Diagnosis
Explain clearly what went wrong or what flaw exists, and why the language runtime/compiler handles it that way.

### Corrected Implementation
```{language}
[Clean, fully functional corrected code]
```

### Key Changes & Architectural Rationale
- Bulleted list of what was changed and why.

### Preventive Best Practices
- Tips and patterns to prevent this issue in production.
"""

    def build_user_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> str:
        error_context = ""
        if context and context.get("error"):
            error_context = f"\nObserved Error / Stack Trace:\n```\n{context['error']}\n```\n"

        return f"""Diagnose, explain, and fix the following {language} code:{error_context}

```{language}
{code}
```
"""
