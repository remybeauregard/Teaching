# Teaching Repository — Claude Instructions

## Accessibility — WCAG 2.1 Level AA

All HTML output in this repository must comply with [WCAG 2.1 Level AA](https://www.w3.org/TR/WCAG21/) in accordance with UC policy. Apply the following rules to every Quarto document created or edited:

### Language and metadata
- Always set `lang: en` in the YAML front matter (WCAG 3.1.1).
- Always include a `<meta name="description">` tag via `include-in-header` for documents distributed to students (WCAG 2.4.2).

### Headings and structure
- Use a strict heading hierarchy (`##` → `###` → `####`); never skip levels (WCAG 1.3.1, 2.4.6).
- Do not use bold or italic text as a visual substitute for a heading.

### Links
- All hyperlink text must be descriptive on its own — never use "click here", "here", or bare URLs as link text (WCAG 2.4.4).

### Tables
- Use tables only for tabular data, never for layout (WCAG 1.3.1).
- Every HTML table must have a header row (`<th>` elements or a Pandoc pipe table with a non-empty header row).
- For label/value course-info blocks, use a `<dl>` definition list with `aria-label` instead of a layout table (see `ECN 102 SS1 2026/syllabus.qmd` for the canonical pattern).

### Emphasis
- Use `**bold**` for emphasis, not `[text]{.underline}`. Underline on non-link text is prohibited — it causes confusion with hyperlinks (WCAG 1.4.1).
- Italic (`*text*`) is acceptable for titles, terminology, and light emphasis.

### Color and contrast
- Do not rely on color alone to convey information (WCAG 1.4.1).
- Use themes (e.g. `cosmo`) that meet the 4.5:1 contrast ratio for normal text (WCAG 1.4.3). Do not override theme colors unless you have verified the new contrast ratio.

### Table of contents
- **Syllabi:** always include `toc: true` and `toc-title: "Contents"` (WCAG 2.4.5) — students need to jump directly to specific policies.
- **All other documents** (slides, exams, homework, etc.): omit `toc` entirely.

### Images and figures
- Every image or figure must have descriptive `fig-alt` text (WCAG 1.1.1). Never use an empty `fig-alt` unless the image is purely decorative.

### PDFs
- PDF accessibility is handled through the LaTeX/Pandoc pipeline. The HTML version is the primary accessible output; ensure it is complete and correct.

---

## Math Rendering

All Quarto documents in this repository use **MathJax** for math rendering (set in `_quarto.yml`).

- **Why MathJax, not MathML or KaTeX?** MathJax renders `\partial`, prime (`′`), and other symbols conventionally, while also generating hidden MathML for screen readers. This satisfies UC WCAG 2.1 accessibility requirements for math content. KaTeX is not recommended here due to weaker screen reader support.
- **Do not** add `html-math-method` overrides to individual `.qmd` files unless you need to deviate from MathJax for a specific document. The default is inherited from `_quarto.yml`.
- **Beamer output** uses LaTeX natively and is unaffected by `html-math-method`.
