#!/usr/bin/env python3
"""
wcag_audit.py — WCAG 2.1 AA audit for R Markdown-compiled PPTX files.

Usage:
    python wcag_audit.py /path/to/unpacked/

Prints a structured list of issues found per slide.
"""

import os
import re
import sys

HIGH_TINT_THRESHOLD = 70000  # tint val >= 70000 on dark theme color -> fails 4.5:1 on white

GENERIC_LINK_TEXT = {'here', 'click here', 'link', 'this', 'more', 'click', 'read more', 'learn more'}


def parse_slide(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _has_meaningful_text_fallback(fallback_block):
    """Return True if the fallback contains real prose text (not just an image or whitespace)."""
    has_image = 'a:blipFill' in fallback_block
    text_runs = [
        t.strip()
        for t in re.findall(r'<a:t[^>]*>([^<]+)</a:t>', fallback_block)
        if t.strip() and t.strip() != '\xa0'
    ]
    return (not has_image) and len(text_runs) > 0


def _has_math_content(choice_block):
    """Return True if the mc:Choice block contains OMML math atoms."""
    return bool(re.search(r'<m:t[^>]*>', choice_block))


# ─── Checks ───────────────────────────────────────────────────────────────────

def check_fallback(raw, slide_num):
    """
    WCAG 1.3.1 — mc:AlternateContent issues:
      (a) Missing mc:Fallback entirely.
      (b) Fallback is image-only (R Markdown default bitmap render) with no readable text.
          This is the critical gap for math-heavy slides: R Markdown bakes in a bitmap render
          of the math as the fallback, which is inaccessible to screen readers.
    """
    issues = []
    parts = raw.split('<mc:AlternateContent')
    for part in parts[1:]:
        end = part.find('</mc:AlternateContent>') + len('</mc:AlternateContent>')
        block = '<mc:AlternateContent' + part[:end]

        # (a) No fallback at all
        if '<mc:Fallback' not in block:
            issues.append({
                'slide': slide_num,
                'wcag': '1.3.1',
                'severity': 'CRITICAL',
                'auto_fix': True,
                'description': (
                    'mc:AlternateContent block has no mc:Fallback. '
                    'Screen readers and non-OOXML renderers see a blank slide body. '
                    'R Markdown wraps all body content in this block when math is present.'
                ),
            })
            break

        # (b) Fallback exists but is image-only (no readable text)
        fb_match = re.search(r'<mc:Fallback[^>]*>(.*?)</mc:Fallback>', block, re.DOTALL)
        if fb_match:
            choice_match = re.search(r'<mc:Choice[^>]*>(.*?)</mc:Choice>', block, re.DOTALL)
            has_math = _has_math_content(choice_match.group(1)) if choice_match else False
            if has_math and not _has_meaningful_text_fallback(fb_match.group(1)):
                issues.append({
                    'slide': slide_num,
                    'wcag': '1.3.1',
                    'severity': 'CRITICAL',
                    'auto_fix': False,
                    'description': (
                        'mc:Fallback exists but contains only an image (R Markdown default bitmap render). '
                        'Screen readers cannot read image-only fallbacks. '
                        'MANUAL FIX REQUIRED: Replace the image fallback with a plain-English text '
                        'description of all math expressions on this slide. '
                        'Example: "d/dx[x^n] = n times x^(n minus 1)". '
                        'The fallback is only seen by non-Microsoft renderers and assistive technology; '
                        'PowerPoint users are unaffected.'
                    ),
                })
            break

    return issues


def check_lang_tags(raw, slide_num):
    """
    WCAG 3.1.1 — a:rPr elements missing lang attribute.
    Note: only flags tags outside mc:Choice (OMML math) blocks —
    mathematical notation atoms inside OMML are not natural-language text
    and do not require language tagging.
    """
    issues = []
    rpr_matches = list(re.finditer(r'<a:rPr(?:[^/]|/(?!>))*?(?:/>|>)', raw))
    missing_outside_omml = 0
    for m in rpr_matches:
        if 'lang=' in m.group(0):
            continue
        pos = m.start()
        preceding = raw[:pos]
        choice_opens = preceding.count('<mc:Choice')
        choice_closes = preceding.count('</mc:Choice>')
        in_omml = choice_opens > choice_closes
        if not in_omml:
            missing_outside_omml += 1

    if missing_outside_omml:
        issues.append({
            'slide': slide_num,
            'wcag': '3.1.1',
            'severity': 'MODERATE',
            'auto_fix': True,
            'description': (
                f'{missing_outside_omml} prose text run(s) missing lang="en-US" on <a:rPr>. '
                'Screen readers may mis-identify content language. '
                '(OMML math atoms are excluded — they do not require language tagging.)'
            ),
        })
    return issues


def check_subtitle_contrast(raw, slide_num, layout_raw=None):
    """
    WCAG 1.4.3 — subtitle tint likely fails 4.5:1 on white background.
    Only flags if no run-level solidFill override is already present on the slide.
    Searches full <p:sp> blocks (not from the <p:ph> tag) to capture txBody content.
    """
    issues = []

    # Find the full <p:sp> block that contains the subtitle placeholder
    sp_blocks = re.findall(r'<p:sp>.*?</p:sp>', raw, re.DOTALL)
    subtitle_sp = None
    for sp in sp_blocks:
        if re.search(r'<p:ph[^>]*(?:type="subTitle"|type="subtitle")', sp, re.IGNORECASE):
            subtitle_sp = sp
            break
    if not subtitle_sp and slide_num == 1:
        for sp in sp_blocks:
            if re.search(r'<p:ph[^>]*idx="1"', sp):
                subtitle_sp = sp
                break

    if subtitle_sp:
        has_override = 'srgbClr' in subtitle_sp and 'solidFill' in subtitle_sp
        if has_override:
            return issues  # run-level color override is present; contrast is fine

    # Look for high tint in slide or layout
    sources = [raw]
    if layout_raw:
        sources.append(layout_raw)
    for src in sources:
        tints = re.findall(r'<a:tint val="(\d+)"', src)
        for t in tints:
            if int(t) >= HIGH_TINT_THRESHOLD:
                issues.append({
                    'slide': slide_num,
                    'wcag': '1.4.3',
                    'severity': 'CRITICAL',
                    'auto_fix': True,
                    'description': (
                        f'Subtitle/author text uses tint val={t} (~{int(t)//1000}% opacity) '
                        'on dark theme color against white background. '
                        'Likely contrast ratio ~1.6:1; required 4.5:1. '
                        'Fix: override run color to #404040 (gives 10:1 ratio).'
                    ),
                })
                break
        if issues:
            break
    return issues


def check_slide_title(raw, slide_num):
    """WCAG 2.4.2 — slide must have a non-empty title placeholder."""
    issues = []
    has_title_ph = bool(re.search(r'<p:ph[^>]*type="(?:title|ctrTitle)"', raw))
    if not has_title_ph:
        issues.append({
            'slide': slide_num,
            'wcag': '2.4.2',
            'severity': 'SERIOUS',
            'auto_fix': False,
            'description': (
                'Slide has no title placeholder (<p:ph type="title"> or "ctrTitle"). '
                'Screen readers cannot identify slide topic. '
                'Manual fix: add a meaningful title in the title placeholder.'
            ),
        })
        return issues

    title_block = re.search(
        r'<p:ph[^>]*type="(?:title|ctrTitle)".*?</p:txBody>',
        raw, re.DOTALL
    )
    if title_block:
        texts = re.findall(r'<a:t>([^<]+)</a:t>', title_block.group(0))
        if not ''.join(texts).strip():
            issues.append({
                'slide': slide_num,
                'wcag': '2.4.2',
                'severity': 'SERIOUS',
                'auto_fix': False,
                'description': 'Title placeholder exists but is empty. Manual fix: add a descriptive title.',
            })
    return issues


def check_images(raw, slide_num):
    """WCAG 1.1.1 — images need alt text (descr attribute on cNvPr)."""
    issues = []
    pic_blocks = re.findall(r'<p:pic>.*?</p:pic>', raw, re.DOTALL)
    for pic in pic_blocks:
        cnvpr = re.search(r'<p:cNvPr[^>]*/>', pic) or re.search(r'<p:cNvPr[^>]*>', pic)
        if cnvpr:
            tag = cnvpr.group(0)
            if 'descr=' not in tag or re.search(r'descr=""', tag):
                issues.append({
                    'slide': slide_num,
                    'wcag': '1.1.1',
                    'severity': 'SERIOUS',
                    'auto_fix': False,
                    'description': (
                        'Image found with missing or empty alt text (descr attribute on <p:cNvPr>). '
                        'Manual fix: add descr="meaningful description", or for decorative images '
                        'set both descr="" and title="".'
                    ),
                })
    return issues


def check_reading_order(raw, slide_num):
    """WCAG 1.3.2 — title placeholder should appear before body in spTree."""
    issues = []
    title_pos = None
    body_pos = None
    for i, m in enumerate(re.finditer(r'<p:sp>', raw)):
        chunk = raw[m.start():m.start() + 500]
        if re.search(r'<p:ph[^>]*type="(?:title|ctrTitle)"', chunk):
            title_pos = i
        elif re.search(r'<p:ph[^>]*idx="1"', chunk) and title_pos is None:
            body_pos = i
    if title_pos is not None and body_pos is not None and body_pos < title_pos:
        issues.append({
            'slide': slide_num,
            'wcag': '1.3.2',
            'severity': 'MODERATE',
            'auto_fix': False,
            'description': (
                'Content placeholder appears before title in XML reading order. '
                'Screen readers may read body content before the slide title. '
                'Manual fix: reorder <p:sp> elements so title comes first in <p:spTree>.'
            ),
        })
    return issues


def check_hyperlinks(raw, slide_num):
    """WCAG 2.4.4 — link text must be descriptive out of context."""
    issues = []
    link_blocks = re.finditer(
        r'<a:rPr[^>]*>.*?<a:hlinkClick[^/]*/?>.*?</a:rPr>.*?<a:t>([^<]*)</a:t>',
        raw, re.DOTALL
    )
    for m in link_blocks:
        text = m.group(1).strip().lower()
        if text in GENERIC_LINK_TEXT or (text.startswith('http') and len(text) > 60):
            issues.append({
                'slide': slide_num,
                'wcag': '2.4.4',
                'severity': 'MODERATE',
                'auto_fix': False,
                'description': (
                    f'Hyperlink with non-descriptive text: "{m.group(1).strip()}". '
                    'Manual fix: rewrite link text to describe the destination.'
                ),
            })
    return issues


# ─── Main audit ───────────────────────────────────────────────────────────────

def audit_slides(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    layouts_dir = os.path.join(unpacked_dir, 'ppt', 'slideLayouts')

    layout1_raw = None
    layout1_path = os.path.join(layouts_dir, 'slideLayout1.xml')
    if os.path.exists(layout1_path):
        with open(layout1_path, encoding='utf-8') as f:
            layout1_raw = f.read()

    all_issues = []
    slide_files = sorted(
        [f for f in os.listdir(slides_dir) if f.endswith('.xml') and not f.startswith('_')],
        key=lambda x: int(re.search(r'\d+', x).group())
    )

    for fname in slide_files:
        slide_num = int(re.search(r'\d+', fname).group())
        path = os.path.join(slides_dir, fname)
        raw = parse_slide(path)

        issues = []
        issues += check_fallback(raw, slide_num)
        issues += check_lang_tags(raw, slide_num)
        issues += check_slide_title(raw, slide_num)
        issues += check_images(raw, slide_num)
        issues += check_reading_order(raw, slide_num)
        issues += check_hyperlinks(raw, slide_num)
        if slide_num == 1:
            issues += check_subtitle_contrast(raw, slide_num, layout1_raw)

        all_issues.extend(issues)

    return all_issues


def print_report(issues):
    if not issues:
        print("\nNo WCAG issues found. All checks passed.")
        return

    by_slide = {}
    for issue in issues:
        by_slide.setdefault(issue['slide'], []).append(issue)

    auto_fixable = [i for i in issues if i['auto_fix']]
    manual = [i for i in issues if not i['auto_fix']]

    print(f"\n{'='*60}")
    print("WCAG 2.1 AA AUDIT RESULTS")
    print(f"{'='*60}")
    print(f"Total issues: {len(issues)}")
    print(f"  Auto-fixable:          {len(auto_fixable)}")
    print(f"  Require manual review: {len(manual)}")
    print()

    for slide_num in sorted(by_slide.keys()):
        print(f"--- Slide {slide_num} ---")
        for issue in by_slide[slide_num]:
            fix_label = "[AUTO-FIX]" if issue['auto_fix'] else "[MANUAL]  "
            print(f"  {fix_label} WCAG {issue['wcag']} [{issue['severity']}]")
            print(f"    {issue['description']}")
        print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wcag_audit.py /path/to/unpacked/")
        sys.exit(1)
    issues = audit_slides(sys.argv[1])
    print_report(issues)
