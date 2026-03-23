# Teaching Repository — Claude Instructions

## Math Rendering

All Quarto documents in this repository use **MathJax** for math rendering (set in `_quarto.yml`).

- **Why MathJax, not MathML or KaTeX?** MathJax renders `\partial`, prime (`′`), and other symbols conventionally, while also generating hidden MathML for screen readers. This satisfies UC WCAG 2.1 accessibility requirements for math content. KaTeX is not recommended here due to weaker screen reader support.
- **Do not** add `html-math-method` overrides to individual `.qmd` files unless you need to deviate from MathJax for a specific document. The default is inherited from `_quarto.yml`.
- **Beamer output** uses LaTeX natively and is unaffected by `html-math-method`.
