#!/usr/bin/env python3
"""
All-in-one mentoring report generator.
Discovers business files, calls Claude Code, and renders HTML report.

Usage: uv run generate_mentoring_report.py <directory_path>
"""

import sys
import json
import subprocess
import re
import base64
from pathlib import Path
from datetime import datetime
from jinja2 import Template
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


def discover_business_files(directory: Path) -> list[Path]:
    """Discover all business document files in directory."""
    extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.jpeg', '.jpg', '.png']
    files = []

    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"**/*{ext}"))

    return sorted(set(files))


def load_prompt_template(template_path: Path) -> str:
    """Load mentoring prompt template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def ensure_plugin_installed():
    """Ensure anthropic-agent-skills marketplace is added and document-skills plugin is installed."""

    try:
        # Step 1: Check if marketplace is configured
        result = subprocess.run(
            ['claude', 'plugin', 'marketplace', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if 'anthropic-agent-skills' not in result.stdout:
            console.print("  Adding anthropic-agent-skills marketplace...")
            result = subprocess.run(
                ['claude', 'plugin', 'marketplace', 'add', 'anthropics/skills'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                console.print(f"  [yellow]Warning:[/yellow] Could not add marketplace: {result.stderr}")
            else:
                console.print("  Marketplace added")

        # Step 2: Install document-skills plugin (idempotent - won't fail if already installed)
        console.print("  Installing document-skills plugin...")
        result = subprocess.run(
            ['claude', 'plugin', 'install', 'document-skills@anthropic-agent-skills'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0 and 'already installed' not in result.stderr.lower():
            console.print(f"  [yellow]Warning:[/yellow] Plugin install output: {result.stderr}")

        console.print("  Plugin ready")

    except subprocess.TimeoutExpired:
        console.print("  [yellow]Warning:[/yellow] Plugin setup timed out, continuing anyway...")
    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Plugin setup error: {e}")


def call_claude_code(directory: Path, prompt_template: str, files: list[Path]) -> dict:
    """
    Call Claude Code CLI to analyze business files.
    Returns parsed JSON response.
    """
    # Build file context
    file_list = "\n".join([f"- {f.name}" for f in files])
    files_context = f"Business files to analyze:\n{file_list}\n\nAnalyze ALL these files thoroughly."

    # Prepare full prompt
    full_prompt = prompt_template.replace("{files_context}", files_context)
    full_prompt = full_prompt.replace("{analysis_approach}",
        "Read each file using document-skills (xlsx, pdf, docx). Extract all financial data, credit scores, and business information.")
    full_prompt = full_prompt.replace("{additional_instructions}",
        "\n\nIMPORTANT: Output ONLY valid JSON following the schema. Do not include explanations before or after the JSON.")

    # Call Claude Code CLI with --print flag for non-interactive output
    # Use stdin to pass the prompt (avoids command line length limits)
    result = subprocess.run(
        [
            'claude',
            '--print',
            '--output-format', 'text',
            '--allowedTools', 'Skill(pdf) Skill(xlsx) Read Write Edit WebSearch Bash(python:*)',
            '--permission-mode', 'acceptEdits'
        ],
        input=full_prompt,
        capture_output=True,
        text=True,
        timeout=600,  # 10 minute timeout
        cwd=str(directory)
    )

    if result.returncode != 0:
        console.print(f"[red]Claude Code error:[/red] {result.stderr}")
        raise RuntimeError(f"Claude Code failed with code {result.returncode}")

    # Parse JSON from output (handle markdown code blocks)
    output = result.stdout
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("Could not find JSON in Claude output")

    return json.loads(json_str)


def render_html_report(data: dict, template_path: Path, logo_path: Path, output_path: Path):
    """Render final HTML report from JSON data."""
    # Load template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())

    # Load logo
    logo_base64 = ""
    if logo_path.exists():
        with open(logo_path, 'rb') as f:
            logo_base64 = base64.b64encode(f.read()).decode()

    # Add metadata
    data['generated_date'] = datetime.now().strftime("%d/%m/%Y")
    data['logo_base64'] = logo_base64

    # Render
    html = template.render(**data)

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_output_filename(data: dict, directory: Path) -> Path:
    """Generate output filename from AFM or fallback to timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Try to extract AFM
    afm = data.get('company_afm', '').strip()
    if afm:
        # Clean AFM (remove non-alphanumeric)
        afm_clean = re.sub(r'[^A-Za-z0-9]', '', afm)
        filename = f"mentoring_report_{afm_clean}_{timestamp}.html"
    else:
        filename = f"mentoring_report_{timestamp}.html"

    return directory / filename


def main():
    if len(sys.argv) < 2:
        console.print("[red]Error:[/red] Directory path required")
        console.print("Usage: uv run generate_mentoring_report.py <directory_path>")
        sys.exit(1)

    directory = Path(sys.argv[1]).resolve()
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Error:[/red] Directory not found: {directory}")
        sys.exit(1)

    script_dir = Path(__file__).parent
    template_dir = script_dir
    prompt_template_path = template_dir / "mentoring_prompt.md"
    html_template_path = template_dir / "mentoring_report_template.html"
    logo_path = template_dir / "microsmart logo.jpeg"

    # Validate templates exist
    if not prompt_template_path.exists():
        console.print(f"[red]Error:[/red] Prompt template not found: {prompt_template_path}")
        sys.exit(1)
    if not html_template_path.exists():
        console.print(f"[red]Error:[/red] HTML template not found: {html_template_path}")
        sys.exit(1)

    console.print(f"\n[bold cyan]Mentoring Report Generator[/bold cyan]")
    console.print(f"Directory: {directory}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:

        # Step 1: Discover files
        task1 = progress.add_task("Discovering business files...", total=100)
        files = discover_business_files(directory)
        progress.update(task1, completed=100)
        console.print(f"  Found {len(files)} files\n")

        if not files:
            console.print("[yellow]Warning:[/yellow] No business files found in directory")
            sys.exit(1)

        # Step 2: Load prompt
        task2 = progress.add_task("Loading prompt template...", total=100)
        prompt_template = load_prompt_template(prompt_template_path)
        progress.update(task2, completed=100)
        console.print("  Prompt template loaded\n")

        # Step 3: Ensure plugin installed
        task3 = progress.add_task("Ensuring document-skills plugin available...", total=100)
        ensure_plugin_installed()
        progress.update(task3, completed=100)
        console.print("  Plugin configured\n")

        # Step 4: Call Claude Code
        task4 = progress.add_task("Analyzing with Claude Code (this may take 5-10 minutes)...", total=None)
        try:
            json_data = call_claude_code(directory, prompt_template, files)
            progress.update(task4, completed=100)
            console.print("  Analysis complete\n")
        except Exception as e:
            progress.stop()
            console.print(f"[red]Error during Claude analysis:[/red] {e}")
            sys.exit(1)

        # Step 5: Save intermediate JSON
        task5 = progress.add_task("Saving intermediate JSON...", total=100)
        json_output_path = directory / "mentoring_analysis.json"
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        progress.update(task5, completed=100)
        console.print(f"  Saved: {json_output_path}\n")

        # Step 6: Render HTML
        task6 = progress.add_task("Rendering HTML report...", total=100)
        output_path = generate_output_filename(json_data, directory)
        render_html_report(json_data, html_template_path, logo_path, output_path)
        progress.update(task6, completed=100)

    console.print(f"\n[bold green]Success![/bold green]")
    console.print(f"Report generated: [cyan]{output_path}[/cyan]")
    console.print(f"JSON output saved: [cyan]{json_output_path}[/cyan]\n")


if __name__ == "__main__":
    main()
