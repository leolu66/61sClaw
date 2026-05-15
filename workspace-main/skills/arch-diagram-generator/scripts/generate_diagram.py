#!/usr/bin/env python3
"""
Architecture Diagram Generator - HTML assembler
Takes an SVG diagram and summary cards, assembles into the dark-theme template.
"""
import sys
import io
import json
import re
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

TEMPLATE = Path(__file__).parent.parent / "assets" / "template.html"

def sanitize_filename(name: str) -> str:
    """Remove Windows-illegal characters from filename."""
    name = re.sub(r'[\\/:*?"<>|]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')
    return name[:200] if len(name) > 200 else name

def load_template():
    if not TEMPLATE.exists():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)
    return TEMPLATE.read_text(encoding='utf-8')

def assemble_html(title: str, svg_content: str, cards: list, legend: list, output_path: str = None):
    """Assemble the full HTML from template + generated content."""
    html = load_template()

    # Replace placeholders
    html = html.replace('{{TITLE}}', title)
    html = html.replace('{{TIMESTAMP}}', datetime.now().strftime('%Y-%m-%d %H:%M'))

    # Build legend HTML
    if legend:
        legend_html = '\n'.join(
            f'    <div class="legend-item"><span class="legend-dot" style="background:{c};"></span>{l}</div>'
            for c, l in legend
        )
    else:
        legend_html = ''
    html = html.replace('<!-- LEGEND_PLACEHOLDER -->', legend_html)

    # Insert SVG
    html = html.replace('<!-- DIAGRAM_PLACEHOLDER -->', svg_content)

    # Build cards HTML
    if cards:
        cards_html = '\n'.join(
            f'''    <div class="summary-card">
      <div class="card-icon">{c.get('icon', '📋')}</div>
      <h3>{c.get('title', 'Untitled')}</h3>
      <p>{c.get('desc', '')}</p>
      <div class="card-tags">{"".join(f'<span class="card-tag">{t}</span>' for t in c.get('tags', []))}</div>
    </div>'''
            for c in cards
        )
    else:
        cards_html = ''
    html = html.replace('<!-- CARDS_PLACEHOLDER -->', cards_html)

    # Determine output path
    if not output_path:
        fname = sanitize_filename(title) + '.html'
        output_path = str(Path(__file__).parent.parent / "output" / fname)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f"✅ Architecture diagram saved to: {out}")
    return str(out)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_diagram.py '<json_input>'  OR  python generate_diagram.py --file <path>")
        print("  JSON keys: title, svg, cards, legend, output")
        sys.exit(0)

    if sys.argv[1] == '--file' and len(sys.argv) > 2:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(sys.argv[1])
    assemble_html(
        title=data.get('title', 'Architecture Diagram'),
        svg_content=data.get('svg', ''),
        cards=data.get('cards', []),
        legend=data.get('legend', []),
        output_path=data.get('output')
    )
