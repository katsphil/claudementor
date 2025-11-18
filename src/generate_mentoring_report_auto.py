#!/usr/bin/env python3
"""
Automated Mentoring Report Generator

Generates comprehensive 11-section mentoring reports for Greek SMEs by:
1. Discovering and organizing business documents
2. Using Task agents to generate each section (800-1200 words)
3. Compiling into final JSON and rendering HTML

Usage:
    # AFM-based (searches SharePoint)
    uv run generate_mentoring_report_auto.py --afm 071477247

    # Direct folder path (backward compatible)
    uv run generate_mentoring_report_auto.py "path/to/business/folder"

    # Interactive prompt
    uv run generate_mentoring_report_auto.py

Example:
    uv run generate_mentoring_report_auto.py --afm 071477247
"""

import sys
import json
import subprocess
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

# Import render_report function
from src.render_report import render_report, load_logo
from src.section_prompts import get_section_prompt
from src.preprocess_documents import preprocess_directory
from src.classify_files_llm import classify_files_with_llm, prepare_file_summary
from src.sharepoint_graph_client import GraphSharePointClient
from src.logging_config import setup_logging

# Load environment variables
load_dotenv()

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
    # Removed - now using logger in main()

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

    # Removed - now using logger in main()

    # Call LLM classification
    classification, detailed_results = classify_files_with_llm(files, preprocessed_map)

    return classification, detailed_results


def extract_afm(directory: Path, provided_afm: str = None) -> str:
    """Extract AFM for directory naming - either from user input or folder name."""
    if provided_afm:
        return provided_afm

    # Try to extract from folder name
    dir_name = directory.parent.name if directory.name == 'mentoring' else directory.name

    # Pattern: "NAME - AFM - something"
    parts = dir_name.split(' - ')
    for part in parts:
        if re.match(r'^\d{9}$', part.strip()):
            return part.strip()

    # Fallback
    return "unknown"


def generate_section_via_agent(section_num: int, company_info: dict, relevant_files: list[Path],
                                output_dir: Path, logger: logging.Logger) -> dict:
    """
    Generate a section using Claude Task agent - FULLY AUTOMATED.

    Returns the generated section dict.
    """
    start_time = datetime.now().strftime("%H:%M:%S")
    logger.info(f"Section {section_num} - Started: {start_time}")

    # Get the prompt for this section
    prompt = get_section_prompt(section_num, company_info, relevant_files)

    # Save prompt for debugging
    prompt_file = output_dir / f"section_{section_num}_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

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
            logger.error(f"Error calling Claude: {result.stderr}")
            return None

        # First, check if Claude already wrote the file directly (most common case)
        section_file = output_dir / f"section_{section_num}_generated.json"
        if section_file.exists():
            try:
                with open(section_file, 'r', encoding='utf-8') as f:
                    section_data = json.load(f)
                logger.info(f"Section {section_num} generated successfully")
                return section_data
            except Exception as e:
                logger.error(f"Section {section_num} - File exists but couldn't parse: {e}")
                return None

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
                logger.error(f"Section {section_num} - Could not extract JSON from output")
                # Save output for debugging
                debug_file = output_dir / f"section_{section_num}_output_debug.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                logger.info(f"Debug output saved to: {debug_file}")
                return None

        # Parse the JSON
        try:
            section_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Section {section_num} - JSON parse error: {e}")
            debug_file = output_dir / f"section_{section_num}_output_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"Debug output saved to: {debug_file}")
            return None

        # Save the generated section
        section_file = output_dir / f"section_{section_num}_generated.json"
        with open(section_file, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Section {section_num} generated successfully")

        return section_data

    except Exception as e:
        logger.error(f"Error generating section {section_num}: {e}")
        return None


def compile_final_report(sections: list[dict], company_info: dict, output_path: Path):
    """Compile all sections into final report JSON."""

    # Generate executive summary
    company_name = company_info.get('company_name', 'την επιχείρηση')
    afm = company_info.get('afm', '')
    afm_text = f" (ΑΦΜ: {afm})" if afm else ""

    executive_summary = f"""
    <h2>Συνοπτική Παρουσίαση</h2>
    <p>Η παρούσα αναφορά παρέχει μια ολοκληρωμένη ανάλυση και στρατηγική καθοδήγηση για
    <strong>{company_name}</strong>{afm_text}, με στόχο την ενίσχυση
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
        "company_name": company_info.get('company_name', ''),
        "afm": company_info.get('afm', ''),
        "kad": company_info.get('kad', ''),
        "website": company_info.get('website', ''),
        "report_title": f"Comprehensive Mentoring & Business Development Report - {company_info.get('company_name', 'Greek SME')}",
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


def download_from_sharepoint(afm: str, logger: logging.Logger) -> Path:
    """
    Download files from SharePoint for given AFM.
    Returns the directory containing downloaded files.
    """
    logger.info(f"Searching SharePoint for AFM: {afm}")

    try:
        # Initialize SharePoint client
        client = GraphSharePointClient()
        logger.info("Connected to SharePoint")

        # Search for AFM folder
        folders = client.search_folders(afm)

        if not folders:
            logger.error(f"No folders found in SharePoint for AFM: {afm}")
            logger.info("Please check:")
            logger.info("  1. AFM is correct")
            logger.info("  2. SharePoint contains a folder with this AFM")
            logger.info("  3. SharePoint credentials are configured in .env")
            sys.exit(1)

        logger.info(f"Found {len(folders)} folder(s) containing '{afm}'")

        # Find mentoring subfolder
        mentoring_folder = None
        afm_folder_info = None

        for folder_info in folders:
            folder_items = client.get_folder_items(folder_info['id'])

            # Look for 'mentoring' subfolder
            for item in folder_items:
                if item.get("type") == "folder" and item["name"].lower() == "mentoring":
                    mentoring_folder = item
                    afm_folder_info = folder_info
                    break

            if mentoring_folder:
                break

        if not mentoring_folder:
            logger.error("No 'mentoring' subfolder found in AFM folder")
            logger.info(f"Searched in: {', '.join([f['name'] for f in folders])}")
            sys.exit(1)

        logger.info(f"Found mentoring subfolder in '{afm_folder_info['name']}'")

        # Create working directory
        project_root = Path(__file__).parent.parent
        working_dir = project_root / "working_dir"
        working_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = working_dir / f"{afm}_{timestamp}"
        output_dir.mkdir(exist_ok=True)

        logger.info(f"Working Directory: {output_dir}")

        # Download files from mentoring subfolder directly into working_dir
        logger.info("Downloading files from SharePoint...")
        downloaded_files = client.download_folder_files(
            mentoring_folder['id'],
            output_dir,
            recursive=True
        )

        logger.info(f"Downloaded {len(downloaded_files)} files")

        return output_dir

    except Exception as e:
        logger.error(f"Failed to download from SharePoint: {e}")
        sys.exit(1)


def main():
    # Initialize logging
    setup_logging(log_file="app.log")
    logger = logging.getLogger(__name__)

    # Parse command-line arguments
    afm_mode = False
    afm_number = None
    directory_path = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--afm" and i + 1 < len(sys.argv):
            afm_mode = True
            afm_number = sys.argv[i + 1]
            i += 2
        else:
            # Direct directory path (backward compatible)
            directory_path = arg
            i += 1

    # Interactive mode if no arguments
    if not afm_mode and not directory_path:
        choice = input("Enter [1] for AFM search or [2] for direct folder path: ").strip()
        if choice == "1":
            afm_number = input("Enter AFM number: ").strip()
            if not afm_number:
                logger.error("AFM number required")
                sys.exit(1)
            afm_mode = True
        elif choice == "2":
            directory_path = input("Enter directory path: ").strip()
            if not directory_path:
                logger.error("Directory path required")
                sys.exit(1)
        else:
            logger.error("Invalid choice")
            sys.exit(1)

    # Track start time
    start_time = datetime.now()
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    # Display header
    console.print(Panel.fit(
        "[bold cyan]Automated Mentoring Report Generator[/bold cyan]\n"
        "[dim]Comprehensive 11-Section Business Analysis for Greek SMEs[/dim]",
        border_style="cyan"
    ))

    console.print(f"\n[bold]Generation started:[/bold] {start_time_str}\n")

    # Determine working directory
    if afm_mode:
        # Download from SharePoint
        directory = download_from_sharepoint(afm_number, logger)
    else:
        # Use provided directory path
        directory = Path(directory_path).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            sys.exit(1)
        logger.info(f"Target Directory: {directory}")

    # Phase 1: Document Discovery
    logger.info("Phase 1: Discovering business documents...")
    files = discover_files(directory)
    logger.info(f"Found {len(files)} documents")

    # Phase 2: File Classification (LLM-based)
    logger.info("Phase 2: Classifying files by section relevance...")
    file_classification, classification_details = classify_files_by_section_llm(files, directory)
    logger.info("Files classified using content-based analysis")

    # Phase 3: Extract AFM for directory naming (full metadata from Section 1 later)
    logger.info("Phase 3: Extracting AFM for directory naming...")
    afm_for_directory = extract_afm(directory, afm_number if afm_mode else None)
    logger.info(f"AFM: {afm_for_directory}")

    # Placeholder metadata - will be populated by Section 1
    company_info = {
        "company_name": "",
        "afm": "",
        "kad": "",
        "website": ""
    }

    # Determine output directory
    if afm_mode:
        # SharePoint mode: directory IS already the working_dir
        output_dir = directory
        # Files are already in working_dir, update classification paths
        file_classification_working = file_classification
    else:
        # Direct folder mode: Create working directory and copy files
        project_root = Path(__file__).parent.parent
        working_dir = project_root / "working_dir"
        working_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = working_dir / f"{afm_for_directory}_{timestamp}"
        output_dir.mkdir(exist_ok=True)

        logger.info(f"Working Directory: {output_dir}")

        # Copy all source files to working directory
        logger.info("Copying source files to working directory...")
        copied_files = []
        for src_file in files:
            # Preserve relative structure within mentoring/
            rel_path = src_file.relative_to(directory)
            dest_file = output_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            copied_files.append(dest_file)

        logger.info(f"Copied {len(copied_files)} files to working directory")

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
    logger.info("Phase 4: Generating comprehensive sections (800-1200 words each)...")

    sections = []

    # Generate Section 1 FIRST to extract metadata
    logger.info("Generating Section 1 first to extract company metadata...")
    relevant_files = file_classification.get(1, [])
    section_1 = generate_section_via_agent(1, company_info, relevant_files, output_dir, logger)

    if section_1:
        sections.append(section_1)

        # Extract metadata from Section 1
        if 'metadata' in section_1:
            company_info = section_1['metadata']
            logger.info(f"Extracted metadata - Company: {company_info.get('company_name', 'N/A')}")
            logger.info(f"AFM: {company_info.get('afm', 'N/A')}, KAD: {company_info.get('kad', 'N/A')}")
            if company_info.get('website'):
                logger.info(f"Website: {company_info['website']}")
        else:
            logger.warning("Section 1 did not return metadata, using folder-based extraction")
    else:
        logger.error("Section 1 generation failed")

    # Generate remaining sections (2-11)
    for section_num in range(2, 12):
        relevant_files = file_classification.get(section_num, [])

        # No checking for existing sections - always generate fresh
        section = generate_section_via_agent(section_num, company_info, relevant_files, output_dir, logger)
        if section:
            sections.append(section)
        else:
            logger.warning(f"Section {section_num} skipped")

    # Phase 5: Compile Report
    logger.info("Phase 5: Compiling final report...")
    final_report_path = output_dir / "mentoring_report_complete.json"
    report = compile_final_report(sections, company_info, final_report_path)

    # Phase 6: Render HTML
    logger.info("Phase 6: Rendering HTML report...")

    try:
        project_root = Path(__file__).parent.parent
        template_path = project_root / "templates" / "mentoring_report_template.html"
        logo_path = project_root / "templates" / "microsmart logo.jpeg"

        # Simple filename (directory already has AFM and timestamp)
        html_output_path = output_dir / "mentoring_report.html"

        render_report(final_report_path, html_output_path, template_path, logo_path)
        logger.info("HTML report rendered successfully")

        html_success = True

    except Exception as e:
        logger.error(f"HTML rendering failed: {e}")
        html_success = False
        html_output_path = None

    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_minutes = int(elapsed.total_seconds() // 60)
    elapsed_seconds = int(elapsed.total_seconds() % 60)
    elapsed_str = f"{elapsed_minutes}m {elapsed_seconds}s" if elapsed_minutes > 0 else f"{elapsed_seconds}s"

    # Summary
    if html_success:
        console.print(Panel.fit(
            f"[bold green]Report Generation Complete[/bold green]\n\n"
            f"Company: {company_info['company_name']}\n"
            f"Sections: {len(sections)}/11\n"
            f"Duration: {elapsed_str}\n"
            f"Output Directory: {output_dir}\n"
            f"JSON: mentoring_report_complete.json\n"
            f"HTML: mentoring_report.html",
            border_style="green",
            title="Success"
        ))
    else:
        console.print(Panel.fit(
            f"[bold yellow]Report Generation Partial[/bold yellow]\n\n"
            f"Company: {company_info['company_name']}\n"
            f"Sections: {len(sections)}/11\n"
            f"Duration: {elapsed_str}\n"
            f"Output Directory: {output_dir}\n"
            f"JSON: mentoring_report_complete.json\n"
            f"HTML: Failed - check errors above",
            border_style="yellow",
            title="Partial Success"
        ))


if __name__ == "__main__":
    main()
