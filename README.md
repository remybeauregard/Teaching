# Teaching Materials

Course materials for UC Davis Economics courses. All documents are authored in [Quarto](https://quarto.org/) and must comply with **WCAG 2.1 Level AA** in accordance with UC accessibility policy.

## Repository Structure

Each course lives in its own directory:

| Directory | Course |
|---|---|
| `ECN 102 SS1 2026/` | Analysis of Economics Data — Summer Session 1 2026 |
| `ECN 101-B Cloyne/` | Intermediate Macroeconomic Theory — Section B |
| `Reading Group/` | ECN 099 Reading Group |

Each directory contains `.qmd` source files alongside their pre-rendered HTML and PDF outputs. Both source and rendered outputs are committed to the repository. After editing a `.qmd`, re-render and commit both.

**Document types:**
- **Syllabi** — HTML (`cosmo` theme) + PDF; include term/year in filename (e.g. `ECN 102 Syllabus SS1 2026.html`)
- **Slides** — Reveal.js HTML + Beamer PDF + plain HTML fallback; omit term/year from filename (e.g. `ECN 102 Lecture 1.html`)

## Rendering

```bash
# Render a single file
quarto render path/to/file.qmd

# Render everything
quarto render

# Preview with live reload
quarto preview path/to/file.qmd
```

## Converting R Markdown Slides

This repository includes a Claude Code skill that converts legacy Beamer/R Markdown (`.Rmd`) slide decks into fully WCAG-compliant Quarto `.qmd` files. To use it, open Claude Code in this directory and run:

```
/Rmd2Qmd-WCAG
```

The skill will ask for the source `.Rmd` file and target filename, then handle YAML front matter, LaTeX-to-Markdown conversion, heading structure, image alt text, and the full WCAG 2.1 AA checklist automatically.

## Contributing

See [CLAUDE.md](CLAUDE.md) for the full authoring conventions, accessibility rules, and math rendering guidance that apply to all documents in this repository.
