#!/usr/bin/env python3
"""Extract stories from Daily Goods Story Scout PDF rundowns into structured JSON."""
import json
import re
import os
import sys

try:
    import pymupdf as fitz
except ImportError:
    import fitz

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stories.json")

CATEGORY_PATTERNS = [
    r"^THE LIST\b",
    r"^CANADIAN NEWS\b",
    r"^ENTERTAINMENT\b",
    r"^LIFESTYLE CHAT\b",
    r"^CLOSER:",
    r"^TECH\b",
    r"^SPORTS\b",
    r"^FLEX\b",
    r"^BREAKOUT WATCH\b",
]

SKIP_SECTIONS = [
    r"^FRANCHISE BANK",
    r"^SOURCES SKIPPED",
    r"^Scout Report Generated",
    r"^FLEX \(cap check",
    r"^\(no flex-slot",
]

def parse_date_slot(filename):
    base = os.path.splitext(filename)[0]
    parts = base.split("-")
    if len(parts) == 4:
        return f"{parts[0]}-{parts[1]}-{parts[2]}", parts[3]
    elif len(parts) == 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}", "full"
    return base, "full"

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def clean_line(line):
    return line.strip()

def parse_stories(text, date, slot):
    lines = text.split("\n")
    stories = []
    current_category = "THE LIST"
    current_story = None
    in_skip_section = False
    in_backup = False

    i = 0
    while i < len(lines):
        line = clean_line(lines[i])
        i += 1

        if not line:
            continue

        if any(re.match(p, line) for p in SKIP_SECTIONS):
            in_skip_section = True
            if current_story:
                stories.append(current_story)
                current_story = None
            continue

        if in_skip_section:
            if any(re.match(p, line) for p in CATEGORY_PATTERNS):
                in_skip_section = False
            else:
                continue

        cat_match = False
        for p in CATEGORY_PATTERNS:
            if re.match(p, line):
                cat_match = True
                if current_story:
                    stories.append(current_story)
                    current_story = None
                in_backup = False
                cat_line = line
                if "(" in cat_line:
                    cat_line = cat_line.split("(")[0].strip()
                current_category = cat_line
                break
        if cat_match:
            continue

        if re.match(r"^Backup options:", line, re.IGNORECASE):
            if current_story:
                stories.append(current_story)
                current_story = None
            in_backup = True
            continue

        title_match = re.match(r"^[IVX]+\s+(.+)", line)
        if title_match and not line.startswith("ICE ") or (
            title_match and line.startswith("I ") and len(line) > 3 and line[2].isupper()
        ):
            real_title = None
            if re.match(r"^I\s+THE DAILY GOODS", line):
                continue
            if re.match(r"^I\s+Breakout potential", line):
                continue

            raw = line
            rm = re.match(r"^[IVX]+\s+(.*)", raw)
            if rm:
                real_title = rm.group(1).strip()

            if real_title and len(real_title) > 5:
                if current_story:
                    stories.append(current_story)

                current_story = {
                    "date": date,
                    "slot": slot,
                    "category": current_category,
                    "title": real_title,
                    "angle": "",
                    "bullets": [],
                    "debate": "",
                    "source": "",
                    "url": "",
                    "score": "",
                    "is_backup": in_backup,
                }
                continue

        if not current_story:
            continue

        if line.startswith("The Angle:"):
            current_story["angle"] = line.replace("The Angle:", "").strip()
            while i < len(lines):
                next_line = clean_line(lines[i])
                if not next_line or next_line.startswith("G") or re.match(r"^(The |URL:|Reddit|www\.|MacRumors|nypost)", next_line):
                    break
                current_story["angle"] += " " + next_line
                i += 1
            continue

        if line.startswith("G ") or line == "G":
            bullet = line[2:].strip() if len(line) > 2 else ""
            while i < len(lines):
                next_line = clean_line(lines[i])
                if not next_line or next_line.startswith("G") or next_line.startswith("The ") or next_line.startswith("URL:") or re.match(r"^(Reddit|www\.|MacRumors|nypost)", next_line):
                    break
                bullet += " " + next_line
                i += 1
            if bullet:
                current_story["bullets"].append(bullet)
            continue

        debate_match = re.match(r"^(The Debate Starter|The Panic Check|The Gross-Out|The Feel-Good|The Check-In|The Gut-Check|The Reality Check|The Travel Chaos|ON-AIR BIT)", line)
        if debate_match:
            continue

        if line.startswith("G ") and "?" in line:
            current_story["debate"] = line[2:].strip()
            continue

        if "?" in line and len(line) > 15 and not line.startswith("URL"):
            if not current_story["debate"]:
                current_story["debate"] = line
            continue

        url_match = re.match(r"^URL:\s*(https?://\S+)", line)
        if url_match:
            current_story["url"] = url_match.group(1)
            continue

        source_match = re.match(r"^(Reddit|www\.|MacRumors|nypost|Entertainment Weekly|People|variety|Kotaku)", line)
        if source_match:
            current_story["source"] = line
            score_match = re.search(r"Score:\s*(\d+/\d+)", line)
            if score_match:
                current_story["score"] = score_match.group(1)
            continue

    if current_story:
        stories.append(current_story)

    return stories


def main():
    all_stories = []
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])

    for pdf_file in pdf_files:
        date, slot = parse_date_slot(pdf_file)
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        try:
            text = extract_text(pdf_path)
            stories = parse_stories(text, date, slot)
            all_stories.extend(stories)
            print(f"  {pdf_file}: {len(stories)} stories", file=sys.stderr)
        except Exception as e:
            print(f"  {pdf_file}: ERROR - {e}", file=sys.stderr)

    all_stories.sort(key=lambda s: (s["date"], s["slot"]), reverse=True)

    print(f"\nTotal: {len(all_stories)} stories from {len(pdf_files)} PDFs", file=sys.stderr)

    with open(OUTPUT, "w") as f:
        json.dump(all_stories, f, indent=2)
    print(f"Written to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
