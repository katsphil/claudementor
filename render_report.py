#!/usr/bin/env python3
"""
Simple script to render mentoring report from Claude JSON output to HTML.
Usage: uv run render_report.py <input.json> [output.html]
"""

import sys
import json
from pathlib import Path
from jinja2 import Template
from datetime import datetime
import base64


def load_logo(logo_path: Path) -> str:
    """Load logo and convert to base64 for embedding."""
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def render_report(json_path: Path, output_path: Path, template_path: Path, logo_path: Path):
    """Render mentoring report from JSON to HTML."""

    # Load JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    # Load logo
    logo_base64 = load_logo(logo_path)

    # Add metadata
    data["generated_date"] = datetime.now().strftime("%d/%m/%Y")
    data["logo_base64"] = logo_base64

    # Render
    html = template.render(**data)

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run render_report.py <input.json> [output.html]")
        sys.exit(1)

    script_dir = Path(__file__).parent
    json_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else json_path.with_suffix(".html")
    template_path = script_dir / "mentoring_report_template.html"
    logo_path = script_dir / "microsmart logo.jpeg"

    if not json_path.exists():
        print(f"Error: Input file not found: {json_path}")
        sys.exit(1)

    if not template_path.exists():
        print(f"Error: Template not found: {template_path}")
        sys.exit(1)

    render_report(json_path, output_path, template_path, logo_path)


if __name__ == "__main__":
    main()
