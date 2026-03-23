Convert the R Markdown slide deck provided by the user into a fully WCAG 2.1 Level AA compliant Quarto `.qmd` file. Follow every step below completely before writing the output file.

---

## Step 1 — Gather context

1. Ask the user for the target filename and folder if not already specified.
2. Read any existing `.qmd` slide files in the same project folder to confirm conventions (YAML structure, theme, output-file naming pattern, etc.).
3. Read `CLAUDE.md` if present for project-specific accessibility rules.

---

## Step 2 — Build the YAML front matter

Use this exact structure:

```yaml
---
title: "..."
subtitle: "..."          # include if the Rmd had one
author: "..."
lang: en                 # WCAG 3.1.1 — always required
format:
  revealjs:
    output-file: "..."   # see naming rule below
    slide-level: 2
    theme: simple
    transition: none
    smaller: true
    include-in-header:
      text: |
        <meta name="description" content="...">   # WCAG 2.4.2
  beamer:
    output-file: "..."
  html:
    output-file: "... Plain.html"
    include-in-header:
      text: |
        <meta name="description" content="...">   # WCAG 2.4.2 — same text as revealjs
execute:
  echo: false
---
```

**Output-file naming rule:**
- Do NOT include the term/year in output filenames when the file lives inside a dated folder (e.g. `ECN 102 SS1 2026/`). The folder already date-stamps the files.
- Exception: syllabi always include the date stamp because they are posted externally.
- `L#` files → `"ECN ### Lecture #.html"` / `"ECN ### Lecture #.pdf"` / `"ECN ### Lecture # Plain.html"`
- `S#` files → `"ECN ### Section #.html"` / etc.

**Meta description text:**
- `L#` files → `"Lecture slides # for ECN ###."`
- `S#` files → `"Discussion slides # for ECN ###."`

---

## Step 3 — Convert the setup chunk

Replace the R setup chunk with Quarto `#|` option style and keep only what is needed:

```r
```{r}
#| label: setup
#| include: false
require("Statamarkdown")   # only if Stata chunks are present
```
```

---

## Step 4 — Convert all LaTeX commands

**Content fidelity rule:** Convert only what is present in the original. Do not add, remove, invent, or restructure slide content. Every slide in the output must correspond 1-to-1 with a slide in the source — no more, no fewer. Removing spacing commands (`\vspace`, `\vfill`) and LaTeX font commands is permitted, but the remaining prose, math, and code must be preserved verbatim.

Apply every substitution below throughout the entire document:

| LaTeX | Quarto/Markdown |
|---|---|
| `\textit{text}` | `*text*` |
| `\textbf{text}` | `**text**` |
| `\underline{text}` | `**text**` — underline on non-link text is **prohibited** (WCAG 1.4.1) |
| `\emph{text}` | `*text*` |
| `\textsuperscript{th}` | `^th^` |
| `\textsuperscript{st}` | `^st^` |
| `\footnote{text}` | `^[text]` |
| `\onslide<1->{...}` + `\onslide<2->{...}` | first block, then `. . .` on its own line, then second block |
| `\vfill` | remove |
| `\vspace{...}` | remove |
| `\hspace{...}` | remove |
| `\footnotesize`, `\small`, `\normalsize`, `\large` | remove |
| `\Rightarrow` in prose | `$\Rightarrow$` |
| `25\%` | `25%` |
| `\&` | `&` |
| `\includegraphics[...]{file}` | `![Caption](file){width=100% fig-alt="..."}` — see Step 5 |
| `---` (LaTeX em-dash) | `—` |

For code chunk options, convert from comma-separated header style to `#|` YAML style:
- `results=F` / `results=FALSE` → `#| results: false`
- `include=FALSE` → `#| include: false`
- `collectcode=T` / `collectcode=TRUE` → `#| collectcode: true`
- `echo=F` / `echo=FALSE` → handled globally by `execute: echo: false`; omit from individual chunks unless overriding

---

## Step 5 — Add descriptive alt text to every image (WCAG 1.1.1)

Every image must have a `fig-alt` attribute. **Never use an empty `fig-alt`** unless the image is purely decorative (which is rare in academic slides).

Write alt text that:
- Describes what the image *shows*, not just what it *is* (e.g. "Histogram of income data showing right skew, with mean marked in red at 12.3 and median in blue at 5.0" not "histogram")
- For charts: mention the variable, axis labels, any marked reference lines, and the overall shape or takeaway
- For diagrams: describe the structure and any labeled components
- For illustrative figures (e.g. skewness diagrams): describe each panel and what it depicts

Format:
```markdown
![Short visible caption.](filename.png){width=100% fig-alt="Full descriptive alt text."}
```

---

## Step 6 — Fix all heading issues (WCAG 2.4.6 + 1.3.1)

1. **No skipped levels:** use only `#` (section slides) and `##` (content slides). Never use `###` or deeper unless there is already a `##` parent on the same slide — and avoid it entirely in slides.
2. **No duplicate headings:** Every `##` slide title must be unique and descriptive of its specific content. Where the original Rmd repeats a generic title (e.g. `## Summary statistics` for every slide in a section), replace each with a specific title such as:
   - `## Central Tendency: Mean`
   - `## Spread: Sample Variance and Std Dev`
   - `## Skewness: Mean vs. Median`
   - `## Example: Mean vs. Median`
   - `## Frequency Table: Example`
   - etc.
3. **Do not use bold or italic as a substitute for a heading.**
4. **Global font size:** add `smaller: true` under the `revealjs:` format block to reduce font size on all slides by default.
5. **Per-slide overrides:** for slides whose content overflows (common with code/Stata output), add heading attributes:
   - RevealJS only: `## Slide Title {.smaller}`
   - Beamer only: `## Slide Title {shrink=20}` — **`shrink` requires an integer (1–100)**, not `true`; it is the minimum shrink percentage Beamer may apply
   - Both formats: `## Slide Title {.smaller shrink=20}`
6. **Automatically apply `{.smaller shrink=20}`** to any slide that displays Stata summary statistics or regression output — specifically any `{stata}` chunk (without `#| results: false`) containing `su`/`summarize` or `reg`/`regress` commands. These commands reliably produce wide, multi-line output that overflows Beamer slides.

---

## Step 7 — Additional WCAG checks

Work through this checklist and fix anything that fails:

- [ ] **WCAG 1.1.1** — Every non-decorative image has a non-empty `fig-alt`
- [ ] **WCAG 1.3.1** — No layout tables; no heading levels skipped
- [ ] **WCAG 1.4.1** — No underline on non-link text; color is never the *sole* means of conveying information (e.g. chart lines distinguished only by color should also be labeled or use different line styles)
- [ ] **WCAG 1.4.3** — `simple` theme used (verified contrast); do not override theme colors without checking contrast ratio
- [ ] **WCAG 2.4.2** — `<meta name="description">` present in both `revealjs` and `html` format blocks
- [ ] **WCAG 2.4.4** — No link text reading "click here", "here", or a bare URL
- [ ] **WCAG 2.4.5** — No `toc` in slides (toc is for syllabi only)
- [ ] **WCAG 2.4.6** — All headings are unique and descriptive
- [ ] **WCAG 3.1.1** — `lang: en` in YAML front matter
- [ ] **Content fidelity** — Slide count matches the original exactly; no content has been added, removed, or invented beyond formatting conversions

---

## Step 8 — Write the output file

Write the completed `.qmd` to the target filename and folder. After writing, perform a final self-review pass:
- Re-read the output file
- Confirm every item in the Step 7 checklist passes
- Report any remaining issues to the user
