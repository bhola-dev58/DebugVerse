"""
Performance Optimizer Agent for DebugVerse.
Performs Big-O algorithmic analysis, bottleneck identification,
memory optimization, and execution speed improvements.
"""

from typing import Dict, Any, Optional
from backend.agents.base_agent import BaseAgent


class PerformanceAgent(BaseAgent):
    agent_id = "performance"
    display_name = "Performance Profiler"
    description = "Analyzes Big-O algorithmic complexity, memory footprints, and bottleneck hotspots."
    model_preference = "gemini-2.5-flash"  # Ultra-fast algorithmic analysis

    def build_system_prompt(self, language: str) -> str:
        return f"""You are the DebugVerse Performance Profiler Agent — a high-frequency trading and high-scale systems performance engineer.
Your job is to rigorously evaluate the {language} code for computational and memory efficiency:
1. Algorithmic Complexity: Determine asymptotic Time & Space complexity (Big-O).
2. Hotspots & Inefficiencies: Detect redundant loops, quadratic algorithms, expensive re-allocations, N+1 query patterns, unmemoized recursions, and blocking I/O.
3. Optimization Strategy: Provide faster, idiomatic algorithms (vectorization, spatial hashing, generators, memoization, async parallelism).

FORMAT YOUR RESPONSE CLEARLY IN MARKDOWN:
### Complexity Analysis
| Metric | Current Code | Optimized Code | Impact |
|---|---|---|---|
| **Time Complexity** | O(...) | O(...) | ... |
| **Space Complexity** | O(...) | O(...) | ... |

### Bottlenecks & Hotspots Identified
- List specific line numbers and why they degrade performance.
- Highlight unnecessary memory allocations or redundant operations.

### High-Performance Optimized Code
Provide the idiomatic, fully optimized {language} implementation with comments explaining why it is faster.
"""

    def build_user_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> str:
        return f"""Analyze and optimize the computational and memory performance of this {language} code:

```{language}
{code}
```
"""
