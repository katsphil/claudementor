# Mentoring Report Generator

Simple setup for generating comprehensive business mentoring reports using Claude Code.

## Prerequisites

- Claude Code installed with document-skills plugin (xlsx, docx, pptx, pdf)
- Python 3.11+ with uv package manager

## Setup

```bash
cd "mentoring templates"
uv sync
```

## Quick Start (One Command)

```bash
uv run generate_mentoring_report.py /path/to/business/files
```

This single command:
- Discovers all business files (PDF, Excel, DOCX, etc.)
- Calls Claude Code to analyze using mentoring_prompt.md
- Generates comprehensive 11-section mentoring analysis
- Renders professional HTML report
- Saves both JSON and HTML output

Output files:
- `mentoring_report_AFM_YYYYMMDD_HHMMSS.html` - Final report
- `mentoring_analysis.json` - Intermediate JSON (for editing if needed)

## Alternative: Manual Workflow

If you prefer step-by-step control:

### 1. Prepare Business Files
Organize all business documents in a directory:
- Business plans (PDF/DOCX)
- Financial statements (E1, E3, Excel)
- Credit reports (Teiresias)
- Tax documents
- Any other relevant files

### 2. Generate Analysis with Claude Code

Start Claude Code and provide this prompt:

```
Analyze all business files in this directory using the mentoring_prompt.md template.
Generate structured JSON output following the schema at the end of the prompt.
Save the output as output.json
```

### 3. Render HTML Report

```bash
uv run render_report.py output.json report.html
```

### 4. Review and Deliver

Open `report.html` in browser, review the mentoring recommendations, and deliver to client.

## Files

- `generate_mentoring_report.py` - All-in-one script (automated workflow)
- `render_report.py` - Standalone JSON to HTML renderer (manual workflow)
- `mentoring_prompt.md` - Comprehensive prompt template with JSON schema
- `mentoring_report_template.html` - Jinja2 HTML template
- `pyproject.toml` - Python dependencies (jinja2, anthropic, rich)
- `microsmart logo.jpeg` - Company logo (embedded in reports)

## Tips

- Keep all business files in one directory for easier analysis
- Claude Code can process multiple file formats simultaneously
- The prompt emphasizes verbose, mentoring-style guidance (not just analysis)
- Generated JSON can be edited manually before rendering if needed
- Each report takes ~5-10 minutes to generate depending on file complexity
