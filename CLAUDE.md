# Daily Goods / JAYSTATION Story Scout Arcade

## Project Overview

A single-page retro arcade-styled web app for radio show prep. Hosts browse auto-extracted story rundowns, build a "loadout" of stories for their show, and generate prep sheets. Deployed via GitHub Pages from `main` branch.

**Live site**: `jasonroti-pixel.github.io/daily-goods-rundowns/app.html`

## Architecture

- **`app.html`** (~1200 lines) — The entire SPA. All HTML, CSS, and JS in one file. Uses `Press Start 2P` retro pixel font, CSS custom properties for night/day theming, and localStorage for state.
- **`extract_stories.py`** — Python script using PyMuPDF (fitz) to extract stories from PDF rundowns into `stories.json`. Has multi-line title continuation logic, angle/bullet parsing, category detection, and backup story flagging.
- **`stories.json`** — Auto-generated structured data from all PDFs. ~1900+ stories. Sorted newest-first.
- **`index.html`** — Redirect/landing page that points to `app.html`.
- **`pdfs/`** — Source PDF rundowns. Filename format: `YYYY-MM-DD-slot.pdf` (slot = `am` or `pm`).
- **`.github/workflows/extract-stories.yml`** — GitHub Action that auto-extracts stories when new PDFs are pushed to `pdfs/` on `main`.

## Key Features

### Brand Switcher
- Toggle between "THE DAILY GOODS" (default) and "JAYSTATION" brands on the intro screen
- `currentBrand` variable + `localStorage('jaystation-brand')` persists choice
- `DG_IMG.logo` = base64-embedded Daily Goods logo; `NICO_IMG` object = pixel art sprites for Jaystation
- Functions: `loadBrand()`, `saveBrand()`, `getBrandImg(key)`, `toggleBrand()`, `applyBrand()`
- Brand switcher button sits above START in intro menu
- Day/night theme works independently of brand

### Night/Day Theme
- CSS custom properties on `:root` (night default) and `[data-theme="day"]`
- Moon/sun toggle in topbar

### Custom Stories
- "Add Story" form with: Title, URL, Summary/Thoughts (textarea), Talking Points (textarea, one per line)
- Custom stories saved to localStorage, appear alongside extracted stories

### Story Extraction (`extract_stories.py`)
- Parses Roman-numeral-prefixed titles (I, II, III, IV, V, etc.)
- Multi-line title continuation: grabs subsequent lines until hitting a known field marker (The Angle:, G bullet, URL:, source line, category header, etc.)
- Strips trailing Roman numeral PDF artifacts from titles
- Skips: "I THE DAILY GOODS", "I Breakout potential", FRANCHISE BANK, SOURCES SKIPPED sections
- Category detection: THE LIST, CANADIAN NEWS, ENTERTAINMENT, LIFESTYLE CHAT, CLOSER, TECH, SPORTS, FLEX, BREAKOUT WATCH

## Development

- **Feature branch**: `claude/retro-game-radio-prep-8yptxn`
- Always push completed work to `main` for live deployment
- The GitHub Action auto-commits `stories.json` when PDFs change on `main`
- When editing `app.html`, beware of the ~71KB base64 DG_IMG logo — use Python scripts for large transformations rather than inline Edit operations
- The `apply_brand.py` script in the scratchpad was used to add brand switching; reference it for the pattern of modifying app.html programmatically

## Gotchas

- `app.html` is large (~270KB). Direct Edit tool works for small changes; for sweeping changes across many lines, a Python transform script is safer.
- PDF text extraction via PyMuPDF splits lines at visual line breaks, so headlines wrap across multiple lines. The continuation logic in `extract_stories.py` handles this.
- Some PDFs use the headline as both the title and the angle (angle is a repeat). This is expected for certain PDF formats.
- The GitHub Action can push to main while you're working — always `git pull --rebase` before pushing.
- Escaped quotes in JS string concatenation inside app.html (e.g., slot tab icons) require line-based replacement in Python scripts rather than exact string matching.
