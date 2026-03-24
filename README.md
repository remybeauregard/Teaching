# Teaching Materials

Course materials for UC Davis Economics courses. All documents are authored in [Quarto](https://quarto.org/) and must comply with **[WCAG 2.1 Level AA](https://www.w3.org/TR/WCAG21/)** in accordance with UC accessibility policy.

## Repository Structure

Each course lives in its own directory:

| Directory | Course |
|---|---|
| `ECN 102 SS1 2026/` | Analysis of Economics Data — Summer Session 1 2026 |
| `ECN 101-B Cloyne/` | Intermediate Macroeconomic Theory — Section B |
| `ECN 099 Reading Group/` | ECN 099 Undergraduate Reading Group |

Each directory contains `.qmd` source files alongside their pre-rendered HTML and PDF outputs. Both source and rendered outputs are committed to the repository. After editing a `.qmd`, re-render and commit both.

**Document types:**
- **Syllabi** — HTML (`cosmo` theme) + PDF; include term/year in filename (e.g. `ECN 102 Syllabus SS1 2026.html`)
- **Slides** — Reveal.js HTML + Beamer PDF + plain HTML fallback; omit term/year from filename (e.g. `ECN 102 Lecture 1.html`)
- **Homework / assignments** — HTML (`cosmo` theme) + PDF; omit term/year from filename. Answer-key files append `AK` (e.g. `ECN 102 Homework 1 AK.html`). Code and output are shown (`echo: true`).

## Rendering

```bash
# Render a single file
quarto render path/to/file.qmd

# Render everything
quarto render

# Preview with live reload
quarto preview path/to/file.qmd
```

## Math Rendering

All HTML and Reveal.js outputs use **MathJax**, configured globally in [_quarto.yml](_quarto.yml). MathJax is preferred over alternatives (e.g. KaTeX) for two reasons: it handles a wider range of LaTeX constructs reliably in presentations, and it generates hidden MathML alongside rendered math, which screen readers can use to satisfy WCAG 2.1 accessibility requirements. Do not override `html-math-method` in individual `.qmd` files without a specific reason.

## Converting R Markdown Slides

This repository includes a Claude Code skill that converts legacy Beamer/R Markdown (`.Rmd`) slide decks into fully WCAG-compliant Quarto `.qmd` files. To use it, open Claude Code in this directory and run:

```
/Rmd2Qmd-WCAG
```

The skill will ask for the source `.Rmd` file and target filename, then handle YAML front matter, LaTeX-to-Markdown conversion, heading structure, image alt text, and the full WCAG 2.1 AA checklist automatically.

## Creating Illustrative Graphs in Slides

This repository includes a Claude Code skill that guides the creation of WCAG-compliant illustrative ggplot2 figures for Quarto slide decks. It checks color contrast, estimates Beamer fit, and enforces alt text, captions, and multi-group accessibility. To use it, open Claude Code in this directory and run:

```
/qmd-graph
```

The skill will read the target slide for context, verify all colors against WCAG contrast thresholds, estimate whether the figure fits on a Beamer slide alongside surrounding text and equations, and produce a complete R code chunk with `fig-alt`, `fig-cap`, direct `annotate()` labels, and a final WCAG checklist.

## WCAG Audit for PowerPoint Slides (Legacy)

For slide decks written in R Markdown and compiled to PowerPoint (`.pptx`), this repository includes a legacy tool that runs the same WCAG 2.1 AA accessibility checks and flags any areas of concern. This is an alternative to the Quarto workflow above, provided for instructors who have not yet migrated their materials to Quarto. The tool is no longer actively used in this repository but is maintained here for others.

**Claude Desktop (skill):** Copy `.claude/wcag-pptx-rmarkdown.skill` into your Claude Desktop skills directory and invoke it by uploading or referencing a `.pptx` file.

**VS Code / Claude Code (command):** Open Claude Code in this directory and run:

```
/wcag-pptx-rmarkdown
```

Claude will ask for the path to your `.pptx` file and step through the full audit and remediation workflow. The audit scripts are in [.claude/wcag-pptx-rmarkdown/scripts/](.claude/wcag-pptx-rmarkdown/scripts/).

## Contributing

See [CLAUDE.md](CLAUDE.md) for the full authoring conventions, accessibility rules, and math rendering guidance that apply to all documents in this repository.
