#!/usr/bin/env python3
"""
Automated Mentoring Report Generator

Generates comprehensive 11-section mentoring reports for Greek SMEs by:
1. Discovering and organizing business documents
2. Using Task agents to generate each section (800-1200 words)
3. Compiling into final JSON and rendering HTML

Usage:
    uv run generate_mentoring_report_auto.py <business_directory>

Example:
    uv run generate_mentoring_report_auto.py "ΤΟΣΙΟΣ ΚΩΝΣΤΑΝΤΙΝΟΣ - 071477247 - ΕΑΤ/mentoring"
"""

import sys
import json
import subprocess
import re
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

# Import render_report function
from src.render_report import render_report, load_logo
from src.section_prompts import get_section_prompt
from src.preprocess_documents import preprocess_directory
from src.classify_files_llm import classify_files_with_llm, prepare_file_summary

console = Console()


def discover_files(directory: Path) -> list[Path]:
    """Discover all business document files in directory."""
    extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.jpeg', '.jpg', '.png']
    files = []

    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"**/*{ext}"))

    return sorted(set(files))


def classify_files_by_section_llm(files: list[Path], directory: Path) -> tuple[dict, dict]:
    """
    Classify files using LLM-based content analysis.

    Returns:
        tuple: (classification_dict, detailed_results)
    """
    console.print("[yellow]Preprocessing files for intelligent classification...[/yellow]")

    # Preprocess all files to extract content samples
    preprocessed = preprocess_directory(directory)

    # Create mapping: filename -> preprocessed data
    preprocessed_map = {}
    for file_data in preprocessed["files"]:
        # Find the actual file path
        for file_path in files:
            if file_path.name == file_data["filename"]:
                preprocessed_map[str(file_path)] = file_data.get("structured_data", {})
                break

    console.print("[yellow]Classifying files with Claude API (content-based analysis)...[/yellow]")

    # Call LLM classification
    classification, detailed_results = classify_files_with_llm(files, preprocessed_map)

    return classification, detailed_results


def extract_company_metadata(directory: Path, files: list[Path]) -> dict:
    """Extract company name, AFM, KAD from files."""
    metadata = {
        "company_name": "",
        "company_afm": "",
        "company_kad": ""
    }

    # Try to extract from directory name first
    dir_name = directory.parent.name if directory.name == 'mentoring' else directory.name

    # Pattern: "NAME - AFM - something"
    parts = dir_name.split(' - ')
    if len(parts) >= 2:
        metadata['company_name'] = parts[0].strip()
        # Look for AFM pattern (9 digits)
        for part in parts:
            if re.match(r'^\d{9}$', part.strip()):
                metadata['company_afm'] = part.strip()
                break

    # KAD will be inferred by Claude from business documents (E1, E3, business plan)
    if not metadata['company_kad']:
        metadata['company_kad'] = ''

    return metadata


def generate_section_via_agent(section_num: int, company_info: dict, relevant_files: list[Path],
                                output_dir: Path) -> dict:
    """
    Generate a section using Claude Task agent - FULLY AUTOMATED.

    Returns the generated section dict.
    """
    start_time = datetime.now().strftime("%H:%M:%S")
    console.print(f"\n[bold cyan]Generating Section {section_num}... [dim]({start_time})[/dim][/bold cyan]")
    console.print(f"Relevant files: {len(relevant_files)}")

    # Get the prompt for this section
    prompt = get_section_prompt(section_num, company_info, relevant_files)

    # Save prompt for debugging
    prompt_file = output_dir / f"section_{section_num}_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    console.print(f"[yellow]Calling Claude Code CLI to generate section (2-5 minutes)...[/yellow]")

    try:
        # Call Claude Code CLI with the prompt
        result = subprocess.run(
            [
                'claude',
                '--print',  # Non-interactive mode
                '--output-format', 'text',
                '--model', 'sonnet',  # Use Sonnet for comprehensive analysis
                '--allowedTools', 'Skill(pdf) Skill(xlsx) Skill(docx) Read Grep Glob WebSearch',
                '--permission-mode', 'acceptEdits'
            ],
            input=prompt,
            capture_output=True,
            text=True,
            # No timeout - let complex sections take as long as needed
            cwd=str(output_dir)
        )

        if result.returncode != 0:
            console.print(f"[red]Error calling Claude:[/red] {result.stderr}")
            return None

        # First, check if Claude already wrote the file directly (most common case)
        section_file = output_dir / f"section_{section_num}_generated.json"
        if section_file.exists():
            try:
                with open(section_file, 'r', encoding='utf-8') as f:
                    section_data = json.load(f)
                console.print(f"[green]✓ Section {section_num} generated successfully[/green]")
                console.print(f"[dim]Saved to: {section_file}[/dim]")
                return section_data
            except Exception as e:
                console.print(f"[yellow]Warning: File exists but couldn't load it: {e}[/yellow]")
                # Fall through to stdout parsing

        # Parse JSON from Claude's output (fallback if file doesn't exist)
        output_text = result.stdout

        # Try to extract JSON (Claude might wrap it in markdown)
        json_match = re.search(r'```json\s*(.*?)\s*```', output_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*"number".*\}', output_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                console.print(f"[red]Could not extract JSON from output[/red]")
                # Save output for debugging
                debug_file = output_dir / f"section_{section_num}_output_debug.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                console.print(f"[dim]Raw output saved to: {debug_file}[/dim]")
                return None

        # Parse the JSON
        section_data = json.loads(json_str)

        # Save the generated section
        section_file = output_dir / f"section_{section_num}_generated.json"
        with open(section_file, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, ensure_ascii=False, indent=2)

        console.print(f"[green]✓ Section {section_num} generated successfully[/green]")
        console.print(f"[dim]Saved to: {section_file}[/dim]")

        return section_data

    except Exception as e:
        console.print(f"[red]Error generating section {section_num}:[/red] {e}")
        return None


def compile_final_report(sections: list[dict], company_info: dict, output_path: Path):
    """Compile all sections into final report JSON."""

    # Generate executive summary
    executive_summary = f"""
    <h2>Συνοπτική Παρουσίαση</h2>
    <p>Η παρούσα αναφορά παρέχει μια ολοκληρωμένη ανάλυση και στρατηγική καθοδήγηση για την
    <strong>{company_info['company_name']}</strong> (ΑΦΜ: {company_info['company_afm']}), με στόχο την ενίσχυση
    της ανταγωνιστικότητας, τη βελτίωση της οικονομικής απόδοσης και την ψηφιακή μετάβαση της επιχείρησης.</p>

    <h3>Βασικά Ευρήματα</h3>
    <ul>
      <li><strong>Επιχειρηματικό Προφίλ:</strong> Ανάλυση επιχειρηματικού μοντέλου και στρατηγικής θέσης</li>
      <li><strong>Οικονομική Υγεία:</strong> Αξιολόγηση οικονομικής απόδοσης και ευκαιρίες βελτίωσης</li>
      <li><strong>Ψηφιακή Ωριμότητα:</strong> Οδικός χάρτης ψηφιακού μετασχηματισμού</li>
      <li><strong>Ευκαιρίες Χρηματοδότησης:</strong> Διαθέσιμα προγράμματα ΕΣΠΑ και εναλλακτικές χρηματοδοτήσεις</li>
    </ul>

    <h3>Προτεινόμενες Στρατηγικές Προτεραιότητες</h3>
    <ol>
      <li>Ψηφιακή αναβάθμιση και online παρουσία</li>
      <li>Βελτίωση συστημάτων οικονομικής διαχείρισης</li>
      <li>Διαφοροποίηση υπηρεσιών/προϊόντων</li>
      <li>Αξιοποίηση χρηματοδότησης ΕΣΠΑ</li>
      <li>Υιοθέτηση τεχνολογιών καινοτομίας</li>
    </ol>
    """

    # Video recommendations (extract from Section 8 if available)
    video_recommendations = []
    for section in sections:
        if section and section.get('number') == 8:
            video_recommendations = section.get('video_recommendations', [])
            break

    # If no videos in Section 8, add defaults
    if not video_recommendations:
        video_recommendations = [
            {
                "title": "AI for Small Business: Complete Guide",
                "channel": "AI Business School",
                "url": "https://www.youtube.com/watch?v=example1",
                "duration": "15:30",
                "topic": "AI Tools for SMEs",
                "relevance": "Πρακτικά εργαλεία AI για μικρές επιχειρήσεις"
            },
            {
                "title": "Digital Marketing για Επαγγελματίες",
                "channel": "Marketing GR",
                "url": "https://www.youtube.com/watch?v=example2",
                "duration": "22:15",
                "topic": "Digital Marketing",
                "relevance": "Στρατηγικές online marketing για ελληνικές επιχειρήσεις"
            },
            {
                "title": "Οικονομική Διαχείριση ΜμΕ",
                "channel": "Small Business Finance GR",
                "url": "https://www.youtube.com/watch?v=example3",
                "duration": "18:45",
                "topic": "Financial Management",
                "relevance": "Οικονομική διαχείριση και προγραμματισμός"
            },
            {
                "title": "ΕΣΠΑ 2021-2027 - Οδηγός Χρηματοδότησης",
                "channel": "ΕΣΠΑ Info",
                "url": "https://www.youtube.com/watch?v=example4",
                "duration": "28:00",
                "topic": "ΕΣΠΑ Funding",
                "relevance": "Αξιοποίηση προγραμμάτων ΕΣΠΑ"
            },
            {
                "title": "Ψηφιακός Μετασχηματισμός Επιχειρήσεων",
                "channel": "Digital Transformation GR",
                "url": "https://www.youtube.com/watch?v=example5",
                "duration": "20:00",
                "topic": "Digital Transformation",
                "relevance": "Στρατηγική ψηφιακής αναβάθμισης"
            }
        ]

    report = {
        "company_name": company_info['company_name'],
        "company_afm": company_info['company_afm'],
        "company_kad": company_info['company_kad'],
        "report_title": f"Comprehensive Mentoring & Business Development Report - {company_info['company_name']}",
        "executive_summary": executive_summary,
        "sections": [s for s in sections if s is not None],
        "video_recommendations": video_recommendations,
        "legal_links": [
            {
                "title": "ΑΑΔΕ - Ανεξάρτητη Αρχή Δημοσίων Εσόδων",
                "url": "https://1521.aade.gr/",
                "description": "Πύλη φορολογικών υποθέσεων και δηλώσεων (Ε1, Ε3, ΦΠΑ, myDATA)"
            },
            {
                "title": "ΕΦΚΑ - Ηλεκτρονικές Υπηρεσίες",
                "url": "https://www.efka.gov.gr/",
                "description": "Ενιαίος Φορέας Κοινωνικής Ασφάλισης - Ασφαλιστικές εισφορές"
            },
            {
                "title": "ΓΕΜΗ - Γενικό Εμπορικό Μητρώο",
                "url": "https://www.businessportal.gr/",
                "description": "Υπηρεσίες Γ.Ε.ΜΗ. και επιχειρηματικότητας"
            },
            {
                "title": "ΕΣΠΑ 2021-2027",
                "url": "https://www.espa.gr/",
                "description": "Προγράμματα χρηματοδότησης για επιχειρήσεις"
            }
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def main():
    if len(sys.argv) < 2:
        console.print("[red]Error:[/red] Business directory path required")
        console.print("Usage: uv run generate_mentoring_report_auto.py <directory_path>")
        sys.exit(1)

    directory = Path(sys.argv[1]).resolve()
    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory not found: {directory}")
        sys.exit(1)

    # Display header
    console.print(Panel.fit(
        "[bold cyan]Automated Mentoring Report Generator[/bold cyan]\n"
        "[dim]Comprehensive 11-Section Business Analysis for Greek SMEs[/dim]",
        border_style="cyan"
    ))

    console.print(f"\n[bold]Target Directory:[/bold] {directory}\n")

    # Phase 1: Document Discovery
    console.print("[bold green]Phase 1:[/bold green] Discovering business documents...")
    files = discover_files(directory)
    console.print(f"✓ Found {len(files)} documents\n")

    # Phase 2: File Classification (LLM-based)
    console.print("[bold green]Phase 2:[/bold green] Classifying files by section relevance (intelligent content analysis)...")
    file_classification, classification_details = classify_files_by_section_llm(files, directory)
    console.print("[green]✓ Files classified using content-based analysis[/green]")

    # Phase 3: Extract Company Metadata (before creating output dir, to get AFM)
    console.print("[bold green]Phase 3:[/bold green] Extracting company metadata...")
    company_info = extract_company_metadata(directory, files)
    console.print(f"✓ Company: {company_info['company_name']}")
    console.print(f"✓ AFM: {company_info['company_afm']}")
    console.print(f"✓ KAD: {company_info['company_kad']}\n")

    # Create timestamped working directory
    project_root = Path(__file__).parent.parent
    working_dir = project_root / "working_dir"
    working_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    afm = company_info.get('company_afm', '000000000')
    output_dir = working_dir / f"{afm}_{timestamp}"
    output_dir.mkdir(exist_ok=True)

    console.print(f"[bold]Working Directory:[/bold] {output_dir}\n")

    # Copy all source files to working directory
    console.print("[bold blue]Copying source files to working directory...[/bold blue]")
    copied_files = []
    for src_file in files:
        # Preserve relative structure within mentoring/
        rel_path = src_file.relative_to(directory)
        dest_file = output_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        copied_files.append(dest_file)

    console.print(f"[green]✓ Copied {len(copied_files)} files to working directory[/green]\n")

    # Update file_classification to use working_dir paths instead of source paths
    file_classification_working = {}
    for section, src_paths in file_classification.items():
        file_classification_working[section] = []
        for src_path in src_paths:
            rel_path = src_path.relative_to(directory)
            working_path = output_dir / rel_path
            file_classification_working[section].append(working_path)

    file_classification = file_classification_working

    # Save classification with relative paths and detailed reasoning
    classification_path = output_dir / "section_file_mapping.json"
    with open(classification_path, 'w', encoding='utf-8') as f:
        json.dump(
            {str(k): [str(f.relative_to(output_dir)) for f in v] for k, v in file_classification.items()},
            f, ensure_ascii=False, indent=2
        )

    # Save detailed classification with reasoning
    detailed_classification_path = output_dir / "llm_classification_details.json"
    with open(detailed_classification_path, 'w', encoding='utf-8') as f:
        json.dump(classification_details, f, ensure_ascii=False, indent=2)

    console.print(f"✓ File classification saved to: {classification_path}")
    console.print(f"✓ Detailed classification reasoning: {detailed_classification_path}\n")

    # Display classification table
    table = Table(title="File Classification by Section")
    table.add_column("Section", style="cyan")
    table.add_column("Files", style="green")
    for section_num in range(1, 12):
        table.add_row(f"Section {section_num}", str(len(file_classification[section_num])))
    console.print(table)
    console.print()

    # Save metadata
    metadata_path = output_dir / "company_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(company_info, f, ensure_ascii=False, indent=2)

    # Phase 4: Generate Sections
    console.print("[bold green]Phase 4:[/bold green] Generating comprehensive sections (800-1200 words each)...")
    console.print("[dim]This phase requires manual Task agent execution for each section[/dim]\n")

    sections = []
    for section_num in range(1, 12):
        relevant_files = file_classification.get(section_num, [])

        # No checking for existing sections - always generate fresh
        section = generate_section_via_agent(section_num, company_info, relevant_files, output_dir)
        if section:
            sections.append(section)
            console.print(f"[green]✓ Section {section_num} generated successfully[/green]\n")
        else:
            console.print(f"[yellow]⚠ Section {section_num} skipped[/yellow]\n")

    # Phase 5: Compile Report
    console.print("[bold green]Phase 5:[/bold green] Compiling final report...")
    final_report_path = output_dir / "mentoring_report_complete.json"
    report = compile_final_report(sections, company_info, final_report_path)
    console.print(f"✓ Final report saved to: {final_report_path}\n")

    # Phase 6: Render HTML
    console.print("[bold green]Phase 6:[/bold green] Rendering HTML report...")

    try:
        project_root = Path(__file__).parent.parent
        template_path = project_root / "templates" / "mentoring_report_template.html"
        logo_path = project_root / "templates" / "microsmart logo.jpeg"

        # Simple filename (directory already has AFM and timestamp)
        html_output_path = output_dir / "mentoring_report.html"

        render_report(final_report_path, html_output_path, template_path, logo_path)
        console.print(f"[green]✓ HTML report rendered successfully[/green]")
        console.print(f"[dim]Saved to: {html_output_path}[/dim]\n")

        html_success = True

    except Exception as e:
        console.print(f"[red]✗ HTML rendering failed:[/red] {e}\n")
        html_success = False
        html_output_path = None

    # Summary
    if html_success:
        console.print(Panel.fit(
            f"[bold green]✓ Report Generation Complete![/bold green]\n\n"
            f"Company: {company_info['company_name']}\n"
            f"Sections: {len(sections)}/11\n"
            f"Output Directory: {output_dir}\n"
            f"JSON: mentoring_report_complete.json\n"
            f"HTML: mentoring_report.html",
            border_style="green",
            title="Success"
        ))
    else:
        console.print(Panel.fit(
            f"[bold yellow]⚠ Report Generation Partial[/bold yellow]\n\n"
            f"Company: {company_info['company_name']}\n"
            f"Sections: {len(sections)}/11\n"
            f"Output Directory: {output_dir}\n"
            f"JSON: mentoring_report_complete.json\n"
            f"HTML: Failed - check errors above",
            border_style="yellow",
            title="Partial Success"
        ))


if __name__ == "__main__":
    main()
