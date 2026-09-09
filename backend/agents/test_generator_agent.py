"""
Test Generator Agent for DebugVerse.
Generates production-grade unit, edge-case, and boundary test suites
in the target language's standard testing framework.
"""

from typing import Dict, Any, Optional
from backend.agents.base_agent import BaseAgent


class TestGeneratorAgent(BaseAgent):
    agent_id = "tests"
    display_name = "Test Generator"
    description = "Generates comprehensive unit test suites covering edge cases, happy paths, and boundary conditions."
    model_preference = "auto"

    def build_system_prompt(self, language: str) -> str:
        framework_map = {
            "python": "pytest (with parameterized fixtures and mock where needed)",
            "javascript": "Jest / Vitest",
            "typescript": "Jest / Vitest with strict TypeScript types",
            "java": "JUnit 5 + AssertJ",
            "cpp": "Google Test (gtest)",
            "c": "Unity / Criterion test framework",
            "go": "testing package with table-driven tests",
            "rust": "#[cfg(test)] built-in test module",
            "csharp": "xUnit or NUnit",
            "php": "PHPUnit",
            "ruby": "RSpec / Minitest",
        }
        framework = framework_map.get(language.lower(), f"the standard testing framework for {language}")

        return f"""You are the DebugVerse Test Generator Agent — a Staff QA & Test Automation Architect.
Your task is to generate complete, copy-paste ready unit test suites for {language} using {framework}.

REQUIREMENTS:
1. Complete Coverage:
   - Happy Path: Standard, expected inputs and operations.
   - Boundary & Edge Cases: Empty collections, null/None, zero, negative numbers, maximum values, large datasets.
   - Error & Exception Conditions: Invalid types, missing required attributes, out-of-bounds access.
2. Self-Contained: Include all necessary imports, mocks, fixtures, and assertions.
3. Documentation: Add a brief comment above each test explaining what edge condition it asserts.

FORMAT YOUR RESPONSE IN MARKDOWN:
### Test Strategy Summary
- Target Framework: `{framework}`
- Test Cases Covered: [Number of test cases]
- Edge Scenarios Evaluated: [Brief bullet points]

### Complete Test Suite
Provide the runnable test code block:
```{language}
[Full runnable test suite code]
```

### How to Run
Provide the exact CLI command to execute these tests (e.g. `pytest test_solution.py -v`).
"""

    def build_user_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> str:
        return f"""Generate an exhaustive unit test suite for this {language} code:

```{language}
{code}
```
"""
