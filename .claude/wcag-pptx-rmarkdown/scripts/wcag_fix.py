#!/usr/bin/env python3
"""
wcag_fix.py — Applies all auto-fixable WCAG 2.1 AA remediations to an unpacked PPTX.

Usage:
    python wcag_fix.py /path/to/unpacked/

After running, pack with:
    python /mnt/skills/public/pptx/scripts/clean.py /path/to/unpacked/
    python /mnt/skills/public/pptx/scripts/office/pack.py /path/to/unpacked/ output.pptx --original original.pptx

Auto-fixes applied:
    1. Add mc:Fallback to mc:AlternateContent blocks with no fallback (WCAG 1.3.1)
    2. Add lang="en-US" to prose <a:rPr> elements (WCAG 3.1.1) — skips OMML math atoms
    3. Fix subtitle contrast on slide 1 (WCAG 1.4.3)

NOT auto-fixed (flagged for manual action):
    - Image-only fallbacks on math slides: R Markdown bakes in a bitmap render of math
      as the default fallback. These require a human-authored plain-English description.
      The script prints the math content to help you write the description.

Known safe usage:
    - Process one slide file at a time (fixes are applied per-file, not across files)
    - The lang-tag fix uses positional context within each file to avoid OMML atoms
    - The fallback insertion targets the last </mc:AlternateContent> in each file
"""

import os
import re
import sys

SUBTITLE_CONTRAST_COLOR = "404040"  # ~10:1 contrast ratio on white
LANG = "en-US"


# ─── Fix 1: Language tags (prose only, per-file) ──────────────────────────────

def fix_lang_tags(content, lang=LANG):
    """
    Add lang attribute to <a:rPr> elements in prose content only.
    Skips runs inside mc:Choice (OMML math) — math atoms are not natural-language
    text and screen readers handle them differently.

    Processes character by character to track nesting depth accurately within
    a single file's content string. Never concatenates files.
    """
    result = []
    pos = 0
    for m in re.finditer(r'<a:rPr(?:[^/]|/(?!>))*?(?:/>|>)', content):
        tag = m.group(0)
        tag_start = m.start()

        # Track mc:Choice open/close depth up to this point in THIS file only
        preceding = content[:tag_start]
        in_omml = preceding.count('<mc:Choice') > preceding.count('</mc:Choice>')

        result.append(content[pos:tag_start])

        if 'lang=' not in tag and not in_omml:
            # Insert lang= after <a:rPr with a guaranteed space separator
            result.append(tag.replace('<a:rPr', f'<a:rPr lang="{lang}"', 1))
        else:
            result.append(tag)
        pos = m.end()

    result.append(content[pos:])
    return ''.join(result)


# ─── Fix 2: Subtitle contrast ─────────────────────────────────────────────────

def fix_subtitle_contrast(content, slide_num):
    """Override subtitle run color to dark gray on slide 1 to meet WCAG 1.4.3."""
    if slide_num != 1:
        return content

    # Find the full <p:sp> block containing the subtitle placeholder
    sp_blocks = list(re.finditer(r'<p:sp>.*?</p:sp>', content, re.DOTALL))
    subtitle_sp = None
    subtitle_span = None
    for m in sp_blocks:
        sp = m.group(0)
        if re.search(r'<p:ph[^>]*(?:type="subTitle"|type="subtitle")', sp, re.IGNORECASE):
            subtitle_sp = sp
            subtitle_span = (m.start(), m.end())
            break
    if not subtitle_sp:
        for m in sp_blocks:
            if re.search(r'<p:ph[^>]*idx="1"', m.group(0)):
                subtitle_sp = m.group(0)
                subtitle_span = (m.start(), m.end())
                break

    if not subtitle_sp or subtitle_span is None:
        return content

    # Skip if color override already present
    if 'srgbClr' in subtitle_sp and 'solidFill' in subtitle_sp:
        return content

    def patch_rpr(m):
        rpr = m.group(0)
        if 'solidFill' in rpr or 'srgbClr' in rpr:
            return rpr
        if rpr.endswith('/>'):
            attrs = rpr[6:-2].strip()  # strip '<a:rPr' (6 chars) and '/>', strip whitespace
            sep = ' ' if attrs else ''
            return (
                f'<a:rPr{sep}{attrs}>'
                f'<a:solidFill><a:srgbClr val="{SUBTITLE_CONTRAST_COLOR}"/></a:solidFill>'
                f'</a:rPr>'
            )
        else:
            return rpr + f'<a:solidFill><a:srgbClr val="{SUBTITLE_CONTRAST_COLOR}"/></a:solidFill>'

    patched_sp = re.sub(r'<a:rPr(?:[^/]|/(?!>))*?(?:/>|>)', patch_rpr, subtitle_sp)
    start, end = subtitle_span
    return content[:start] + patched_sp + content[end:]


# ─── Fix 3: mc:Fallback ───────────────────────────────────────────────────────

def _has_math_content(choice_block):
    return bool(re.search(r'<m:t[^>]*>', choice_block))


def _has_meaningful_text_fallback(fallback_block):
    has_image = 'a:blipFill' in fallback_block
    text_runs = [
        t.strip()
        for t in re.findall(r'<a:t[^>]*>([^<]+)</a:t>', fallback_block)
        if t.strip() and t.strip() != '\xa0'
    ]
    return (not has_image) and len(text_runs) > 0


def _make_auto_fallback_text(choice_block):
    """Naive linearization of an OMML block — always review for math slides."""
    paras_raw = re.findall(r'<a:p>(.*?)</a:p>', choice_block, re.DOTALL)
    para_texts = []
    for p in paras_raw:
        runs = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', p)
        math = re.findall(r'<m:t[^>]*>([^<]+)</m:t>', p)
        text = ' '.join(runs + math).strip()
        if text:
            para_texts.append(text)
    if not para_texts:
        a_t = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', choice_block)
        m_t = re.findall(r'<m:t[^>]*>([^<]+)</m:t>', choice_block)
        combined = ' '.join(a_t + m_t).strip()
        para_texts = [combined] if combined else ['[Content requires Microsoft Office to display]']
    return para_texts


def _make_fallback_xml(paragraphs, lang=LANG):
    p_els = []
    for para in paragraphs:
        escaped = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        p_els.append(
            f'        <a:p>\n'
            f'          <a:pPr lvl="0" indent="0" marL="0"><a:buNone/></a:pPr>\n'
            f'          <a:r><a:rPr lang="{lang}"/>'
            f'<a:t xml:space="preserve">{escaped}</a:t></a:r>\n'
            f'        </a:p>'
        )
    body = '\n'.join(p_els)
    return (
        '    <mc:Fallback>\n'
        '      <p:sp>\n'
        '        <p:nvSpPr>\n'
        '          <p:cNvPr id="999" name="Content Placeholder Fallback"/>\n'
        '          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>\n'
        '          <p:nvPr><p:ph idx="1"/></p:nvPr>\n'
        '        </p:nvSpPr>\n'
        '        <p:spPr/>\n'
        '        <p:txBody>\n'
        '          <a:bodyPr/>\n'
        '          <a:lstStyle/>\n'
        f'{body}\n'
        '        </p:txBody>\n'
        '      </p:sp>\n'
        '    </mc:Fallback>'
    )


def fix_fallbacks(content, slide_num):
    """
    Process mc:AlternateContent blocks within a single file's content string.

    Splits by the literal string '<mc:AlternateContent' and processes each block
    independently — never operates across file boundaries.

    Returns (patched_content, warnings_list).
    """
    warnings = []

    if '<mc:AlternateContent' not in content:
        return content, warnings

    # Split into: [pre-first-block, block1_suffix, block2_suffix, ...]
    # Each block_suffix starts just after '<mc:AlternateContent' and includes
    # everything up to and including '</mc:AlternateContent>'
    parts = content.split('<mc:AlternateContent')
    result = [parts[0]]  # content before any AlternateContent block

    for part in parts[1:]:
        # Find the matching close tag within this part
        close_tag = '</mc:AlternateContent>'
        close_pos = part.find(close_tag)
        if close_pos == -1:
            # Malformed — leave untouched
            result.append('<mc:AlternateContent' + part)
            continue

        block = '<mc:AlternateContent' + part[:close_pos + len(close_tag)]
        after = part[close_pos + len(close_tag):]

        # (a) No fallback at all — add auto-generated one
        if '<mc:Fallback' not in block:
            choice_match = re.search(r'<mc:Choice[^>]*>(.*?)</mc:Choice>', block, re.DOTALL)
            paras = _make_auto_fallback_text(choice_match.group(1)) if choice_match else ['[Math content]']
            fallback_xml = _make_fallback_xml(paras)
            # Insert before the closing </mc:AlternateContent>
            block = block[:-len(close_tag)] + '\n' + fallback_xml + '\n  ' + close_tag

        else:
            # (b) Fallback exists — check if image-only on a math slide
            fb_match = re.search(r'<mc:Fallback[^>]*>(.*?)</mc:Fallback>', block, re.DOTALL)
            choice_match = re.search(r'<mc:Choice[^>]*>(.*?)</mc:Choice>', block, re.DOTALL)
            if fb_match and choice_match:
                has_math = _has_math_content(choice_match.group(1))
                if has_math and not _has_meaningful_text_fallback(fb_match.group(1)):
                    a_t = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', choice_match.group(1))
                    m_t = re.findall(r'<m:t[^>]*>([^<]+)</m:t>', choice_match.group(1))
                    warnings.append({'slide': slide_num, 'prose': a_t, 'math': m_t})

        result.append(block)
        result.append(after)

    return ''.join(result), warnings


# ─── Main ─────────────────────────────────────────────────────────────────────

def fix_slide(fname, content):
    slide_num = int(re.search(r'\d+', fname).group())
    content = fix_lang_tags(content)
    content, warnings = fix_fallbacks(content, slide_num)
    content = fix_subtitle_contrast(content, slide_num)
    return content, warnings


def main(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    slide_files = sorted(
        [f for f in os.listdir(slides_dir) if f.endswith('.xml') and not f.startswith('_')],
        key=lambda x: int(re.search(r'\d+', x).group())
    )

    all_warnings = []
    fixed = 0

    for fname in slide_files:
        path = os.path.join(slides_dir, fname)
        with open(path, encoding='utf-8') as f:
            original = f.read()

        patched, warnings = fix_slide(fname, original)
        all_warnings.extend(warnings)

        if patched != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(patched)
            print(f"  Fixed: {fname}")
            fixed += 1
        else:
            print(f"  No changes: {fname}")

    print(f"\nDone. {fixed}/{len(slide_files)} slides modified.")

    if all_warnings:
        print(f"\n{'='*60}")
        print("ACTION REQUIRED: Image-only math fallbacks detected")
        print(f"{'='*60}")
        print("The following slides have R Markdown image fallbacks for math content.")
        print("Screen readers cannot read these. Replace each with plain-English math descriptions.\n")
        for w in all_warnings:
            print(f"  Slide {w['slide']}:")
            if w['prose']:
                print(f"    Prose text: {w['prose']}")
            if w['math']:
                print(f"    Math atoms: {w['math']}")
            print(f"    -> Write a description like: \"[formula spelled out in words]\"")
            print()
        print("See SKILL.md for examples of good math descriptions.")
    else:
        print("\nAll fallbacks are text-based. No manual math descriptions needed.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wcag_fix.py /path/to/unpacked/")
        sys.exit(1)
    main(sys.argv[1])
