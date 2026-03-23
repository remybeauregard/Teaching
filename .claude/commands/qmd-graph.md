Create or audit an illustrative R ggplot2 figure for a Quarto `.qmd` slide deck. Work through every step below before writing the final code chunk.

---

## Step 1 — Understand the context

1. Read the target `.qmd` file (or the relevant slide section if already open) to confirm:
   - The slide's heading and surrounding prose, so the graph matches the teaching objective.
   - Whether the slide already has substantial text, bullet points, a display equation, or other figures that will compete for vertical space.
   - Whether the graph goes in a two-column layout (`.columns`) or takes the full slide width.
2. Note the color palette already in use in the file (typically `#003087` blue and `#ac47be` purple). Reuse these unless a third color is needed — see Step 3.
3. Read `CLAUDE.md` for any project-specific conventions not covered here.

---

## Step 2 — Plan the graph

Answer these questions before writing any code:

- **What concept does the graph illustrate?** State it in one sentence.
- **What variables / distributions / data does it require?** Keep it minimal and synthetic (no external datasets unless the slide content demands it).
- **What visual elements are needed?** Lines, points, density curves, arrows, text annotations, reference lines, etc.
- **How many visual groups need to be distinguished?** If more than one, plan to distinguish them by *both* color *and* line type or shape (WCAG 1.4.1 — never color alone).
- **What text labels or annotations are needed inside the plot?** Plan their positions now so they do not overlap with data.

---

## Step 3 — Verify color contrast (WCAG 1.4.3 / 1.4.11)

For every color used against the plot background (typically white `#ffffff`), compute the WCAG relative luminance and contrast ratio using this Python snippet (run it via Bash):

```python
def linearize(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(r, g, b):
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast(hex1, hex2):
    def parse(h):
        h = h.lstrip("#")
        return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    L1 = luminance(*parse(hex1)); L2 = luminance(*parse(hex2))
    hi, lo = max(L1,L2), min(L1,L2)
    return (hi + 0.05) / (lo + 0.05)
```

**Requirements:**
- Graphical elements (lines, points, bars): contrast ≥ **3:1** against adjacent background (WCAG 1.4.11).
- In-figure text annotations: contrast ≥ **4.5:1** against their background (WCAG 1.4.3).
- If a color fails, replace it with a darker/lighter variant and re-check before proceeding.

**Pre-verified palette for white backgrounds:**

| Color | Hex | Contrast vs white | Use |
|---|---|---|---|
| Dark blue | `#003087` | 11.9:1 ✓ | Primary lines, regression lines |
| Purple | `#ac47be` | 4.8:1 ✓ | Data points, secondary curves |
| Dark red | `#c0392b` | 5.4:1 ✓ | Third group if needed |
| Dark gray (text) | `#333333` | 12.6:1 ✓ | Axis annotations, reference labels |

> Do **not** use light or mid-tone colors (e.g. `#aaaaaa`, `#ffcc00`) for any data element without first verifying contrast.

---

## Step 4 — Check Beamer fit

Beamer slides (128 mm × 96 mm, ~10 mm margins, ~8 mm title bar) leave a content area of roughly **108 mm wide × 68 mm tall** (≈ 4.25" × 2.68").

Use this formula to estimate the displayed figure height on a Beamer slide:

```
displayed_height_inches = fig_height_in × (4.25 / fig_width_in)
```

Then estimate the total content height on the slide:

| Element | Approximate height |
|---|---|
| One line of body text | 0.22" |
| One display equation (`$$...$$`) | 0.35–0.45" |
| Slide title | already subtracted above |
| Figure caption (`fig-cap`) | 0.20" |
| Vertical padding between elements | 0.10" per gap |

**The sum of all elements must be ≤ 2.68".**

**Practical defaults by slide content:**

| What else is on the slide | Recommended `fig-height` | Recommended `fig-width` |
|---|---|---|
| Full-width figure, no other content | 3.2 | 5.5 |
| Full-width figure + one line of text | 2.8 | 5.5 |
| Full-width figure + text + equation | 2.1–2.3 | 5.0 |
| Half-width column figure | 3.0 | 4.5 |
| Half-width column + text above | 2.4 | 4.5 |

If the figure is in a two-column layout, apply the half-width column row. Each column uses approximately half the textwidth, so Beamer scales `fig-width` against ~54 mm rather than 108 mm.

---

## Step 5 — Write the code chunk

Use this template, filling in every field:

````markdown
```{r}
#| label: fig-<short-slug>          # unique, lowercase, hyphenated
#| fig-height: <from Step 4>
#| fig-width:  <from Step 4>
#| fig-cap: "<Short visible caption — plain text, no math notation>"
#| fig-alt: "<Full descriptive alt text — see requirements below>"
library(ggplot2)

# ... R code ...
```
````

**`fig-alt` requirements (WCAG 1.1.1):**
- Describe what the graph *shows*, not just what type of chart it is.
- For density/distribution plots: name each curve, its center, width, and what it represents.
- For scatter plots: describe the pattern, any regression line, and what the axes represent.
- For multi-panel or annotated plots: describe each annotated element (arrows, labels, reference lines).
- For conceptual illustrative graphs (no real data): make clear the graph is schematic and describe what the visual is intended to convey.
- Never leave `fig-alt` empty unless the image is purely decorative (rare in slides).

**Code style rules:**
- Set a `set.seed()` if the graph uses any random data, so it is reproducible.
- Use `theme_classic()` as the base theme.
- Remove tick labels with `axis.text = element_blank()` and `axis.ticks = element_blank()` for purely illustrative graphs where numeric values are not meaningful.
- Always include `labs(x = "...", y = "...")` with descriptive axis labels (even if blank-valued).
- Remove the ggplot2 legend with `legend.position = "none"` and use direct `annotate("text", ...)` labels instead — legends are harder to read at small sizes and take extra space.
- When distinguishing multiple groups, map both `color` and `linetype` (or `shape`) to the grouping variable.
- Annotation font sizes: use `size = 2.8–3.2` for in-figure text at half-column width, `size = 3.0–3.5` for full-width figures.
- Use `expression()` for math labels inside `annotate()`, e.g. `expression(italic(b)[2]*", small "*italic(n))`. Never concatenate `expression(...)` with a string using `~` outside of `expression()`.

---

## Step 6 — Final checklist

Before delivering the code chunk, verify every item:

- [ ] **WCAG 1.1.1** — `fig-alt` is present, non-empty, and fully descriptive
- [ ] **WCAG 1.4.1** — Groups are distinguished by color **and** line type or shape, not color alone
- [ ] **WCAG 1.4.3 / 1.4.11** — All colors contrast ≥ 4.5:1 for annotation text, ≥ 3:1 for graphical elements, against the background
- [ ] **WCAG 2.4.2** — `fig-cap` is present and written in plain text (no LaTeX or Unicode math)
- [ ] **Beamer fit** — Sum of text + equation + displayed figure height + caption ≤ 2.68"
- [ ] **Reproducibility** — `set.seed()` is set if any random data is generated
- [ ] **No bare legend** — Groups labeled with direct `annotate()` calls, not a ggplot2 legend
- [ ] **Axis labels** — `labs(x = ..., y = ...)` present with meaningful text
- [ ] **`theme_classic()`** — Used as base theme

Report any item that cannot be fully resolved and explain why.
