#!/usr/bin/env python3
"""
wcag_alt_text.py — Auto-generate and apply alt text to images in an unpacked PPTX.

Usage:
    python wcag_alt_text.py /path/to/unpacked/

For each <p:pic> element missing a descr attribute (or with descr=""), this script:
  1. Resolves the image file from the slide's .rels
  2. Sends the image to Claude via the Anthropic API for a concise accessibility description
  3. Writes the description into descr="" on the <p:cNvPr> element
  4. Prints a summary of every image found and what alt text was applied

Decorative images (those explicitly marked with both descr="" AND title="") are left alone.

Requires: requests or the anthropic SDK — uses raw fetch via urllib to avoid extra deps.
"""

import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

# Slide title for context
def get_slide_title(raw):
    m = re.search(r'<p:ph[^>]*type="(?:title|ctrTitle)"[^>]*/?>.*?</p:txBody>', raw, re.DOTALL)
    if m:
        texts = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', m.group(0))
        return ' '.join(t.strip() for t in texts if t.strip()) or None
    return None


def get_slide_prose(raw):
    """Extract visible prose text from slide for context."""
    texts = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', raw)
    return ' '.join(t.strip() for t in texts if t.strip())[:400]


def resolve_image_path(slide_num, rel_id, unpacked_dir):
    """Find the media file path for a given relationship ID in a slide."""
    rels_path = os.path.join(
        unpacked_dir, 'ppt', 'slides', '_rels', f'slide{slide_num}.xml.rels'
    )
    if not os.path.exists(rels_path):
        return None
    with open(rels_path, encoding='utf-8') as f:
        rels_content = f.read()
    # Find Target for this rId
    m = re.search(rf'Id="{re.escape(rel_id)}"[^>]*Target="([^"]+)"', rels_content)
    if not m:
        return None
    target = m.group(1)
    # Target is relative to ppt/slides/; resolve to absolute
    if target.startswith('../'):
        target = target[3:]  # strip '../' -> relative to ppt/
        abs_path = os.path.join(unpacked_dir, 'ppt', target)
    else:
        abs_path = os.path.join(unpacked_dir, 'ppt', 'slides', target)
    return abs_path if os.path.exists(abs_path) else None


def image_to_base64(path):
    with open(path, 'rb') as f:
        data = f.read()
    ext = os.path.splitext(path)[1].lower()
    media_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
    }
    media_type = media_types.get(ext, 'image/png')
    return base64.standard_b64encode(data).decode('utf-8'), media_type


def generate_alt_text(image_path, slide_title, slide_prose):
    """Call Claude API to generate a concise alt text for the image."""
    b64, media_type = image_to_base64(image_path)

    system = (
        "You write concise, accurate alt text for images in educational PowerPoint slides. "
        "Alt text should describe what the image shows in plain English, be under 125 characters "
        "where possible, and convey the same information a sighted reader would get. "
        "Do not start with 'Image of' or 'Picture of'. "
        "If the image is a chart or graph, describe the data trend or key finding. "
        "If it is a diagram, describe the structure and relationships shown. "
        "If it is decorative (purely visual with no informational content), respond with exactly: DECORATIVE"
    )

    context = f"Slide title: {slide_title or 'unknown'}. Slide text: {slide_prose or 'none'}."

    payload = {
        "model": MODEL,
        "max_tokens": 200,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"{context}\n\nWrite alt text for this image.",
                    },
                ],
            }
        ],
    }

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['content'][0]['text'].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f"API error {e.code}: {body}")


def find_pics(raw):
    """
    Find all <p:pic> elements and return list of dicts with:
      - xml: the full <p:pic>...</p:pic> string
      - start, end: positions in raw
      - cNvPr_tag: the <p:cNvPr .../> tag string
      - rel_id: r:embed value (image relationship ID)
      - has_descr: whether descr attribute already present
      - descr_value: current descr value (may be empty string)
      - title_value: current title value
    """
    pics = []
    for m in re.finditer(r'<p:pic>.*?</p:pic>', raw, re.DOTALL):
        pic_xml = m.group(0)

        # Get cNvPr tag
        cnvpr_m = re.search(r'<p:cNvPr[^>]*/>', pic_xml)
        if not cnvpr_m:
            cnvpr_m = re.search(r'<p:cNvPr[^>]*>', pic_xml)
        if not cnvpr_m:
            continue

        cNvPr_tag = cnvpr_m.group(0)
        has_descr = 'descr=' in cNvPr_tag
        descr_value = ''
        title_value = ''

        if has_descr:
            dm = re.search(r'descr="([^"]*)"', cNvPr_tag)
            descr_value = dm.group(1) if dm else ''
        tm = re.search(r'title="([^"]*)"', cNvPr_tag)
        title_value = tm.group(1) if tm else ''

        # Get r:embed for the blip
        embed_m = re.search(r'r:embed="([^"]+)"', pic_xml)
        rel_id = embed_m.group(1) if embed_m else None

        pics.append({
            'pic_xml': pic_xml,
            'start': m.start(),
            'end': m.end(),
            'cNvPr_tag': cNvPr_tag,
            'rel_id': rel_id,
            'has_descr': has_descr,
            'descr_value': descr_value,
            'title_value': title_value,
        })
    return pics


def apply_alt_text(cNvPr_tag, alt_text, is_decorative=False):
    """Return updated cNvPr tag with descr (and title if decorative) set."""
    if is_decorative:
        # Mark as decorative: descr="" title=""
        tag = re.sub(r'\s*descr="[^"]*"', '', cNvPr_tag)
        tag = re.sub(r'\s*title="[^"]*"', '', tag)
        tag = tag.replace('<p:cNvPr', '<p:cNvPr descr="" title=""', 1)
        return tag
    else:
        escaped = alt_text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        if 'descr=' in cNvPr_tag:
            tag = re.sub(r'descr="[^"]*"', f'descr="{escaped}"', cNvPr_tag)
        else:
            tag = cNvPr_tag.replace('<p:cNvPr', f'<p:cNvPr descr="{escaped}"', 1)
        return tag


def process_slide(slide_num, unpacked_dir, results):
    path = os.path.join(unpacked_dir, 'ppt', 'slides', f'slide{slide_num}.xml')
    if not os.path.exists(path):
        return

    with open(path, encoding='utf-8') as f:
        raw = f.read()

    pics = find_pics(raw)
    if not pics:
        return

    slide_title = get_slide_title(raw)
    slide_prose = get_slide_prose(raw)
    modified = False

    # Process in reverse order so string positions stay valid
    for pic in reversed(pics):
        # Skip if explicitly marked decorative (descr="" AND title="")
        if pic['has_descr'] and pic['descr_value'] == '' and pic['title_value'] == '':
            results.append({
                'slide': slide_num,
                'title': slide_title,
                'status': 'skipped_decorative',
                'alt_text': None,
            })
            continue

        # Skip if already has meaningful alt text
        if pic['has_descr'] and pic['descr_value'].strip():
            results.append({
                'slide': slide_num,
                'title': slide_title,
                'status': 'already_present',
                'alt_text': pic['descr_value'],
            })
            continue

        # Resolve image file
        if not pic['rel_id']:
            results.append({
                'slide': slide_num,
                'title': slide_title,
                'status': 'error',
                'alt_text': None,
                'error': 'Could not find r:embed relationship ID',
            })
            continue

        image_path = resolve_image_path(slide_num, pic['rel_id'], unpacked_dir)
        if not image_path:
            results.append({
                'slide': slide_num,
                'title': slide_title,
                'status': 'error',
                'alt_text': None,
                'error': f'Image file not found for rel {pic["rel_id"]}',
            })
            continue

        # Generate alt text via Claude API
        try:
            alt_text = generate_alt_text(image_path, slide_title, slide_prose)
        except Exception as e:
            results.append({
                'slide': slide_num,
                'title': slide_title,
                'status': 'error',
                'alt_text': None,
                'error': str(e),
            })
            continue

        is_decorative = alt_text.strip().upper() == 'DECORATIVE'
        new_cNvPr = apply_alt_text(pic['cNvPr_tag'], alt_text, is_decorative)
        new_pic_xml = pic['pic_xml'].replace(pic['cNvPr_tag'], new_cNvPr, 1)
        raw = raw[:pic['start']] + new_pic_xml + raw[pic['end']:]
        modified = True

        results.append({
            'slide': slide_num,
            'title': slide_title,
            'status': 'decorative' if is_decorative else 'applied',
            'alt_text': None if is_decorative else alt_text,
            'image_path': os.path.basename(image_path),
        })

    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(raw)


def print_summary(results):
    if not results:
        print("  No images found in any slide.")
        return

    for r in results:
        slide_label = f"Slide {r['slide']}" + (f" — {r['title']}" if r['title'] else "")
        if r['status'] == 'applied':
            print(f"  [{slide_label}] Applied: \"{r['alt_text']}\"")
        elif r['status'] == 'decorative':
            print(f"  [{slide_label}] Marked decorative (descr=\"\" title=\"\")")
        elif r['status'] == 'already_present':
            print(f"  [{slide_label}] Already had alt text: \"{r['alt_text']}\"")
        elif r['status'] == 'skipped_decorative':
            print(f"  [{slide_label}] Already marked decorative — skipped")
        elif r['status'] == 'error':
            print(f"  [{slide_label}] ERROR: {r.get('error', 'unknown')}")


def main(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    slide_files = sorted(
        [f for f in os.listdir(slides_dir) if f.endswith('.xml') and not f.startswith('_')],
        key=lambda x: int(re.search(r'\d+', x).group())
    )

    print(f"\n{'='*60}")
    print("ALT TEXT — IMAGE ACCESSIBILITY (WCAG 1.1.1)")
    print(f"{'='*60}")

    results = []
    for fname in slide_files:
        slide_num = int(re.search(r'\d+', fname).group())
        process_slide(slide_num, unpacked_dir, results)

    print_summary(results)

    applied = [r for r in results if r['status'] == 'applied']
    decorative = [r for r in results if r['status'] == 'decorative']
    errors = [r for r in results if r['status'] == 'error']

    print(f"\nSummary: {len(applied)} alt text(s) applied, "
          f"{len(decorative)} decorative, "
          f"{len(errors)} error(s).")

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wcag_alt_text.py /path/to/unpacked/")
        sys.exit(1)
    main(sys.argv[1])
