# DebugVerse Agent Guidelines & Workspace Customizations

## Project Overview
DebugVerse is an AI-powered code debugger & sandboxed executor built with FastAPI (Python) and React.

## UI/UX Pro Max Design Intelligence
This workspace has the **UI/UX Pro Max** suite installed under `.agents/skills/` and rules under `.agents/rules/`.

When working on any frontend, UI/UX, styling, or design system components:
1. **Consult Skills**:
   - `ui-ux-pro-max`: Core design intelligence with 84 styles, 192 color palettes, 74 font pairings, 98 UX guidelines, and 25 chart types.
   - `design-system`: Design tokens, MASTER.md generation, component structure.
   - `ui-styling`: CSS rules, micro-interactions, responsive guidelines.
   - `design`: General UX workflows, information architecture, wireframing.
   - `brand`, `banner-design`, `slides`: Branding and visual assets.

2. **Search Utility**:
   Run search queries on demand to get instant recommendations:
   ```bash
   python3 .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" [--domain <domain>] [--stack react]
   ```

3. **Follow Rules**:
   - Adhere to the guidelines defined in `.agents/rules/ui-ux.md`.
   - Ensure WCAG AA compliance (contrast >= 4.5:1, touch target >= 44×44px, no emoji icons, keyboard accessibility).
