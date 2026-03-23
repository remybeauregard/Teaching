#!/usr/bin/env python3
"""
wcag_report_fallbacks.py — Print all accessibility text from an unpacked PPTX:
  1. mc:Fallback text (for math/OMML slides — what screen readers see instead of equations)
  2. Image alt text (descr attribute on <p:cNvPr> elements within <p:pic> blocks)

Usage:
    python wcag_report_fallbacks.py /path/to/unpacked/

Run this after wcag_fix.py and wcag_alt_text.py, and before delivering the file,
so all accessibility descriptions can be reviewed for accuracy in one place.
"""

import os
import re
import sys


def get_slide_title(raw):
    m = re.search(
        r'<p:ph[^>]*type="(?:title|ctrTitle)"[^>]*/?>.*?</p:txBody>',
        raw, re.DOTALL
    )
    if m:
        texts = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', m.group(0))
        return ' '.join(t.strip() for t in texts if t.strip()) or None
    return None


def get_fallback_lines(fb_block):
    return [
        t.strip()
        for t in re.findall(r'<a:t[^>]*>([^<]+)</a:t>', fb_block)
        if t.strip() and t.strip() != '\xa0'
    ]


def get_image_alt_texts(raw):
    """
    Return list of dicts for each <p:pic> element:
      { descr, title, is_decorative, rel_id }
    """
    images = []
    for pic in re.finditer(r'<p:pic>.*?</p:pic>', raw, re.DOTALL):
        pic_xml = pic.group(0)
        cnvpr = re.search(r'<p:cNvPr[^>]*/>', pic_xml) or re.search(r'<p:cNvPr[^>]*>', pic_xml)
        if not cnvpr:
            continue
        tag = cnvpr.group(0)
        dm = re.search(r'descr="([^"]*)"', tag)
        tm = re.search(r'title="([^"]*)"', tag)
        embed_m = re.search(r'r:embed="([^"]+)"', pic_xml)

        descr = dm.group(1) if dm else None
        title = tm.group(1) if tm else None
        rel_id = embed_m.group(1) if embed_m else '?'

        is_decorative = (descr == '' and title == '')
        images.append({
            'descr': descr,
            'title': title,
            'is_decorative': is_decorative,
            'rel_id': rel_id,
        })
    return images


def report(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    slide_files = sorted(
        [f for f in os.listdir(slides_dir) if f.endswith('.xml') and not f.startswith('_')],
        key=lambda x: int(re.search(r'\d+', x).group())
    )

    has_fallbacks = False
    has_images = False

    fallback_sections = []
    image_sections = []

    for fname in slide_files:
        slide_num = int(re.search(r'\d+', fname).group())
        with open(os.path.join(slides_dir, fname), encoding='utf-8') as f:
            raw = f.read()

        title = get_slide_title(raw)
        label = f"Slide {slide_num}" + (f" — {title}" if title else "")

        # ── Fallbacks ──────────────────────────────────────────────────────
        if '<mc:AlternateContent' in raw:
            parts = raw.split('<mc:AlternateContent')
            for part in parts[1:]:
                end = part.find('</mc:AlternateContent>') + len('</mc:AlternateContent>')
                block = '<mc:AlternateContent' + part[:end]
                fb = re.search(r'<mc:Fallback[^>]*>(.*?)</mc:Fallback>', block, re.DOTALL)

                if not fb:
                    fallback_sections.append((label, '[WARNING] No mc:Fallback present — screen readers see nothing.', True))
                    has_fallbacks = True
                    continue

                has_image_fb = 'blipFill' in fb.group(1)
                lines = get_fallback_lines(fb.group(1))

                if has_image_fb and not lines:
                    fallback_sections.append((label, '[WARNING] Fallback is image-only — screen readers cannot read this.', True))
                    has_fallbacks = True
                elif lines:
                    fallback_sections.append((label, lines, False))
                    has_fallbacks = True

        # ── Images ─────────────────────────────────────────────────────────
        images = get_image_alt_texts(raw)
        if images:
            has_images = True
            image_sections.append((label, images))

    # ── Print fallback section ──────────────────────────────────────────────
    print()
    print('=' * 60)
    print('FALLBACK TEXT (screen reader / non-OOXML view of math slides)')
    print('=' * 60)

    if not has_fallbacks:
        print('\n  No slides with mc:AlternateContent blocks found.')
    else:
        for label, content, is_warning in fallback_sections:
            print(f'\n{label}:')
            if is_warning:
                print(f'  {content}')
            else:
                for line in content:
                    print(f'  - "{line}"')

    # ── Print alt text section ──────────────────────────────────────────────
    print()
    print('=' * 60)
    print('IMAGE ALT TEXT (WCAG 1.1.1)')
    print('=' * 60)

    if not has_images:
        print('\n  No images found in any slide.')
    else:
        for label, images in image_sections:
            print(f'\n{label}:')
            for img in images:
                if img['is_decorative']:
                    print(f'  - [Decorative] (marked with descr="" title="" — screen readers skip)')
                elif img['descr'] and img['descr'].strip():
                    print(f'  - "{img["descr"]}"')
                elif img['descr'] == '':
                    print(f'  - [WARNING] Empty alt text (descr="") — image is inaccessible')
                else:
                    print(f'  - [WARNING] No alt text set for image {img["rel_id"]}')

    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wcag_report_fallbacks.py /path/to/unpacked/")
        sys.exit(1)
    report(sys.argv[1])
