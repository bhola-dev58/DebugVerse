---
description: "UI/UX design standards, styling intelligence, and quality guidelines for DebugVerse frontend development"
globs: "frontend/**/*"
---

# UI/UX Pro Max Guidelines for DebugVerse

When building, modifying, or reviewing frontend components in DebugVerse, follow the UI/UX Pro Max design intelligence principles below.

## 1. Product Identity & Design Direction
DebugVerse is a developer tool (AI-powered code debugger & sandboxed executor).
- **Core Aesthetic**: Dark Mode (OLED / Deep Slate) + Minimalist Glassmorphism + Bento Box grid layout + Terminal/IDE aesthetic.
- **Palette**: Deep slate background (`#090d16` / `#0f172a`), crisp syntax highlights (emerald, cyan, amber, rose), subtle borders (`rgba(255, 255, 255, 0.08)`), and focused accents.
- **Typography**:
  - UI Text: Modern sans-serif (`Inter`, `Plus Jakarta Sans`, `system-ui`).
  - Code & Execution Output: High-legibility monospaced fonts (`JetBrains Mono`, `Fira Code`, `ui-monospace`).

## 2. Using Local Design Intelligence
Consult the local UI/UX Pro Max search engine when choosing styles, palettes, icons, or UX patterns:

```bash
# Query product styles & guidelines
python3 .agents/skills/ui-ux-pro-max/scripts/search.py "developer tool ide terminal" --domain product

# Query color palettes
python3 .agents/skills/ui-ux-pro-max/scripts/search.py "dark mode syntax" --domain color

# Query UX rules & best practices
python3 .agents/skills/ui-ux-pro-max/scripts/search.py "code editor layout" --domain ux

# Query chart/analytics types
python3 .agents/skills/ui-ux-pro-max/scripts/search.py "execution metrics" --domain chart
```

## 3. Critical UX Checks (Must Follow)
1. **Accessibility (WCAG 2.1 AA)**:
   - Text contrast >= 4.5:1 against its background.
   - Interactive elements must retain visible focus indicators.
   - Never use raw emojis as UI icons; always use crisp SVG icons (e.g., Lucide React).
2. **Touch & Click Targets**:
   - Interactive elements must have a minimum target size of 44×44px (including padding).
   - Space buttons and action triggers with at least 8px gap.
3. **Execution & AI Feedback States**:
   - Every async action (running code, analyzing with Gemini) must display immediate feedback: spinners, pulse badges, or skeleton loaders.
   - Provide clear error boundaries and actionable error banners when execution times out or fails.
4. **Motion & Transitions**:
   - Use subtle micro-interactions (150ms–250ms duration, ease-out curve) on hover, active, and modal transitions.
   - Avoid jarring layout shifts (CLS < 0.1); reserve fixed heights for execution outputs and terminal streams.
