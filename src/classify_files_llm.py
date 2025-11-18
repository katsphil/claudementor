#!/usr/bin/env python3
"""
LLM-based file classification for mentoring report sections.
Uses Claude Code CLI to intelligently categorize files by content rather than filename patterns.
"""

import json
import subprocess
import re
from pathlib import Path
from typing import Any


SECTION_DESCRIPTIONS = {
    1: "Business Profile & Strategic Positioning - Company structure, business model, regulatory compliance, membership documents, certificates",
    2: "Financial Health & Performance - Financial statements, cash flow, Teiresias credit reports, tax declarations (E1, E3), ENFIA, credit scores, financial ratios",
    3: "Market Analysis & Competitive Strategy - Market research, competitor analysis, target market segmentation, industry trends",
    4: "Funding Strategy & Investment Planning - Funding proposals, OPSKE/ΕΣΠΑ applications, investment plans, loan applications",
    5: "Digital Transformation Roadmap - Website information, digital strategy, technology implementation plans, online presence",
    6: "Financial Management Systems - Accounting software, myDATA integration, ERP systems, financial process documentation",
    7: "ESG Implementation Framework - Sustainability reports, ESG assessments, environmental initiatives, social responsibility programs",
    8: "AI & Innovation Strategy - Technology adoption, innovation plans, AI readiness, digital tools",
    9: "Leadership Development & Team Building - Psychometric assessments, personality tests, leadership evaluations, team assessments (look for scores base 100)",
    10: "Implementation Roadmap & Success Metrics - Overall business plans, strategic roadmaps (synthesis section)",
    11: "Legal & Regulatory Compliance - Tax documents (E1, E3, ENFIA), insurance documents, legal certificates, regulatory filings"
}


def prepare_file_summary(file_path: Path, preprocessed_data: dict = None) -> dict:
    """Prepare a concise file summary for LLM classification."""
    summary = {
        "filename": file_path.name,
        "file_type": file_path.suffix.lower()
    }

    if preprocessed_data:
        # Include relevant preprocessed information
        if "text_sample" in preprocessed_data:
            summary["text_sample"] = preprocessed_data["text_sample"][:300]  # First 300 chars

        if "content_hints" in preprocessed_data:
            summary["content_hints"] = preprocessed_data["content_hints"]

        if "sheets" in preprocessed_data:
            # Excel file - include sheet names and key figures
            sheets = preprocessed_data.get("sheets", [])
            summary["sheets"] = [s["name"] for s in sheets]

            # Include sample of key financial figures
            key_figures = []
            for sheet in sheets[:2]:  # First 2 sheets
                key_figures.extend(sheet.get("key_figures", [])[:3])
            if key_figures:
                summary["key_financial_indicators"] = key_figures[:5]

    return summary


def classify_files_with_llm(files: list[Path], preprocessed_data_map: dict = None) -> tuple[dict, dict]:
    """
    Classify files using Claude Code CLI based on content analysis.

    Args:
        files: List of file paths to classify
        preprocessed_data_map: Dict mapping file paths to preprocessed data

    Returns:
        Tuple of (classification_dict, detailed_results)
    """
    if not files:
        return {i: [] for i in range(1, 12)}, {"classifications": []}

    # Prepare file summaries
    file_summaries = []
    for file_path in files:
        preprocessed = None
        if preprocessed_data_map and str(file_path) in preprocessed_data_map:
            preprocessed = preprocessed_data_map[str(file_path)]

        summary = prepare_file_summary(file_path, preprocessed)
        file_summaries.append(summary)

    # Build classification prompt
    prompt = f"""You are analyzing business documents for a Greek SME mentoring report that has 11 sections.

**Your task**: Classify each file by determining which section(s) it's most relevant to (1-11). A file can be relevant to multiple sections.

**Section Descriptions:**
{json.dumps(SECTION_DESCRIPTIONS, indent=2, ensure_ascii=False)}

**Files to Classify:**
{json.dumps(file_summaries, indent=2, ensure_ascii=False)}

**CRITICAL: Analyze the ACTUAL files available and ensure NO section is left empty.**

**Classification Strategy:**
1. **First**, review what files are actually available in this dataset
2. **Then**, intelligently distribute files to ensure EVERY section gets relevant content
3. **Use these guidelines** (but adapt based on what files exist):
   - Business plans → typically sections 1, 3, 4, 5, 7, 8, 10
   - Financial documents (Excel, E1, E3, ENFIA, Teiresias) → sections 2, 6, 11
   - Psychometric assessments/leadership tests → Section 9
   - Tax/legal/insurance documents → Sections 2, 11
   - OPSKE/funding proposals → Sections 4, 5, 8
4. **If a section would have zero files**, assign the most relevant available file(s) to it
   - Example: If no ESG file exists, assign business plan to Section 7
   - Example: If no tech docs exist, assign business plan to Section 8
5. **Be INCLUSIVE** - files can map to 3-7 sections if they contain relevant information
6. **Prioritize content coverage** - better to over-assign than leave sections empty

**Output Format**: Return ONLY valid JSON (no markdown, no explanation):
{{
  "classifications": [
    {{
      "filename": "exact filename",
      "sections": [section_numbers],
      "reasoning": "brief explanation"
    }}
  ]
}}"""

    # Call Claude Code CLI (same pattern as generate_section_via_agent)
    try:
        result = subprocess.run(
            [
                'claude',
                '--print',  # Non-interactive mode
                '--output-format', 'text',
                '--model', 'haiku',  # Use Haiku for fast classification
                '--allowedTools', 'Skill(pdf) Skill(xlsx) Skill(docx) Read',  # Skills to read files
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout for classification
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Code CLI error: {result.stderr}")

        response_text = result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise RuntimeError("Claude Code CLI classification timed out (>3 minutes)")
    except FileNotFoundError:
        raise RuntimeError("Claude Code CLI not found. Ensure 'claude' command is in PATH.")

    # Parse JSON response (handle markdown code blocks)
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    result = json.loads(response_text)

    # Convert to section mapping
    section_mapping = {i: [] for i in range(1, 12)}

    # Create filename to path mapping
    filename_to_path = {f.name: f for f in files}

    for classification in result["classifications"]:
        filename = classification["filename"]
        sections = classification["sections"]

        if filename in filename_to_path:
            file_path = filename_to_path[filename]
            for section_num in sections:
                if 1 <= section_num <= 11:
                    section_mapping[section_num].append(file_path)

    return section_mapping, result


if __name__ == "__main__":
    # Test the classification system
    import sys
    from preprocess_documents import preprocess_directory

    if len(sys.argv) < 2:
        print("Usage: uv run classify_files_llm.py <directory_path>")
        sys.exit(1)

    directory = Path(sys.argv[1])

    # Preprocess files first
    print("Preprocessing files...")
    preprocessed = preprocess_directory(directory)

    # Create mapping
    preprocessed_map = {
        file_data["filename"]: file_data.get("structured_data", {})
        for file_data in preprocessed["files"]
    }

    # Get file paths
    extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.jpeg', '.jpg', '.png']
    files = []
    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"**/*{ext}"))

    files = sorted(set(files))

    # Classify
    print(f"\nClassifying {len(files)} files...")
    classification, details = classify_files_with_llm(files, preprocessed_map)

    # Display results
    print("\n=== CLASSIFICATION RESULTS ===\n")
    for section_num in range(1, 12):
        file_count = len(classification[section_num])
        print(f"Section {section_num}: {file_count} files")
        for file_path in classification[section_num]:
            print(f"  - {file_path.name}")

    # Save detailed results
    output_file = directory / "llm_classification_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "classifications": details,
            "section_mapping": {
                str(k): [str(f) for f in v]
                for k, v in classification.items()
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\nDetailed results saved to: {output_file}")
