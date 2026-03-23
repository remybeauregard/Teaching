# WCAG 2.1 AA Audit & Remediation for R Markdown PPTX Slides

Audits and remediates a PowerPoint (`.pptx`) file compiled from R Markdown for WCAG 2.1 Level AA compliance. Use this command when a user provides a `.pptx` slide deck produced by R Markdown (`output: powerpoint_presentation`) that needs to meet UC accessibility standards.

---

## Setup

Ask the user for the path to their `.pptx` file if not already provided. Set:

```bash
PPTX_INPUT="<path to .pptx>"
PPTX_BASENAME=$(basename "$PPTX_INPUT" .pptx)
UNPACKED="/tmp/wcag-pptx-unpacked"
PPTX_OUTPUT="/tmp/${PPTX_BASENAME}-accessible.pptx"
SCRIPTS_DIR="$(git -C "$(dirname "$PPTX_INPUT")" rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/wcag-pptx-rmarkdown/scripts"
```

Unpack the `.pptx` (it is a zip archive):

```bash
rm -rf "$UNPACKED" && mkdir -p "$UNPACKED"
python3 -c "
import zipfile, sys
zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])
print('Unpacked to', sys.argv[2])
" "$PPTX_INPUT" "$UNPACKED"
```

---

## Step 1: Extract Slide Text

```bash
pip install "markitdown[pptx]" -q
python3 -m markitdown "$PPTX_INPUT"
```

Read the output to understand the content of the deck before proceeding.

---

## Step 2: Run the Audit

```bash
python3 "$SCRIPTS_DIR/wcag_audit.py" "$UNPACKED"
```

Read the full output. Issues marked `[MANUAL]` require your attention before running the fix script — especially **image-only math fallbacks** (slides where the R Markdown fallback is a bitmap render of the math rather than readable text).

---

## Step 3: Apply Auto-Fixes

```bash
python3 "$SCRIPTS_DIR/wcag_fix.py" "$UNPACKED"
```

The fix script prints warnings for any image-only math fallbacks it cannot fix automatically. For each such slide, **write a plain-English math description** and update the `mc:Fallback` XML manually before packing. See the math description guidance in `.claude/wcag-pptx-rmarkdown.skill` (or the Claude Desktop skill) for examples.

---

## Step 3b: Generate Image Alt Text

This step requires an Anthropic API key in the environment (`ANTHROPIC_API_KEY`). If not set, skip and flag images for manual review.

```bash
python3 "$SCRIPTS_DIR/wcag_alt_text.py" "$UNPACKED"
```

The script calls the Claude API for each image missing alt text and writes descriptions back into the XML. Review every generated description — the report in Step 5 will list them all.

---

## Step 4: Pack the Remediated File

```bash
python3 -c "
import zipfile, os, sys

unpacked = sys.argv[1]
output = sys.argv[2]

with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(unpacked):
        for file in files:
            abs_path = os.path.join(root, file)
            arc_name = os.path.relpath(abs_path, unpacked)
            zf.write(abs_path, arc_name)

print('Packed to', output)
" "$UNPACKED" "$PPTX_OUTPUT"
```

---

## Step 5: Review All Accessibility Text

```bash
python3 "$SCRIPTS_DIR/wcag_report_fallbacks.py" "$UNPACKED"
```

Print the full output in the conversation. This shows every `mc:Fallback` block (math screen-reader text) and every image alt text, labeled by slide. Confirm with the user that all descriptions are accurate before delivering. If any `[WARNING]` lines appear, stop and resolve them first.

---

## Step 6: Deliver

Tell the user the output file is at `$PPTX_OUTPUT` and provide a plain-language audit report using this format:

```
## WCAG 2.1 AA Audit Report
**File:** [original filename]
**Date:** [today]
**Standard:** WCAG 2.1 Level AA (UC April 2026 compliance)

### Issues Fixed Automatically
- [Issue type] — Slide [N]: [description]

### Issues Requiring Manual Review
- [Issue type] — Slide [N]: [description and action required]

### Issues Not Found
- [List of criteria checked and found clean]

### Notes on R Markdown-Specific Risks
[Caveats, especially re: math fallback accuracy and image alt text]
```

---

## WCAG Issues Specific to R Markdown PPTX

### What PowerPoint's built-in checker misses

| Issue | WCAG | Severity | Fix |
|-------|------|----------|-----|
| Missing `mc:Fallback` | 1.3.1 | Critical | Auto |
| Image-only math fallback | 1.3.1 | Critical | Manual |
| Subtitle contrast (~1.6:1) | 1.4.3 | Critical | Auto |
| Missing language tags on text | 3.1.1 | Moderate | Auto |
| Missing image alt text | 1.1.1 | Serious | Auto (Claude API) |
| Non-descriptive hyperlink text | 2.4.4 | Moderate | Manual |
| Missing slide titles | 2.4.2 | Serious | Manual |

For full details on each issue, math description examples, and the `mc:Fallback` XML template, see `.claude/wcag-pptx-rmarkdown.skill`.

---

## Dependencies

- Python 3 (stdlib only for audit/fix/report; `urllib` for alt text)
- `pip install "markitdown[pptx]"` — for extracting slide text in Step 1
- `ANTHROPIC_API_KEY` — for Step 3b (image alt text generation)
