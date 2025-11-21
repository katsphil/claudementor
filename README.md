# Mentoring Report Generator

Generates comprehensive 11-section mentoring reports for Greek SMEs using Claude Code to analyze business documents.

## Quick Start

### Windows
Double-click `run_mentoring_report.bat` - handles all setup automatically.

### Linux/Mac
```bash
uv sync
uv run mentoring-report --afm 071477247
```

## Usage

### AFM-Based (SharePoint)
```bash
uv run mentoring-report --afm 071477247
```
Automatically searches SharePoint for the AFM folder and downloads files from the `mentoring` subfolder.

### Direct Folder Path
```bash
uv run mentoring-report "path/to/business/folder"
```

### Interactive Mode
```bash
uv run mentoring-report
```
Prompts you to choose between AFM search or direct folder path.

## Prerequisites

- **Claude Code** with document-skills plugin (xlsx, docx, pptx, pdf)
- **Python 3.11+** with uv package manager
- **FFmpeg** (optional, for video transcription)

## SharePoint Setup

Required for AFM-based mode only. Copy `.env.example` to `.env` and configure:

```env
SHAREPOINT_TENANT_ID="your-tenant-id"
SHAREPOINT_CLIENT_ID="your-client-id"
SHAREPOINT_CLIENT_SECRET="your-client-secret"
SHAREPOINT_SITE_NAME="axiologiseis"
SHAREPOINT_DRIVE_NAME="Έγγραφα"
```

### Getting Credentials
1. Azure Portal → App Registrations
2. Create/select app → note Application (client) ID and Directory (tenant) ID
3. Certificates & secrets → New client secret → copy Value
4. API permissions → Microsoft Graph → Sites.Read.All, Files.Read.All → Grant admin consent

### Expected SharePoint Structure
```
axiologiseis/
└── Έγγραφα/
    └── [COMPANY_NAME - AFM - CODE]/
        └── mentoring/          ← Files downloaded from here
            ├── document1.pdf
            ├── spreadsheet.xlsx
            └── ...
```

## Output

All files saved to `working_dir/[AFM]_[timestamp]/`:
- Source files (downloaded or copied)
- `section_N_generated.json` - Individual sections
- `mentoring_report_complete.json` - Compiled report
- `mentoring_report.html` - Final HTML report

## How It Works

1. **Document Discovery**: Finds/downloads business documents
2. **Pre-processing**: Extracts structured data from Excel files
3. **Classification**: Categorizes files by type (financial, operational, etc.)
4. **Section Generation**: Uses Claude Code Task agents to generate 11 sections (800-1200 words each)
5. **Compilation**: Combines sections into final JSON
6. **Rendering**: Produces professional HTML report

## Files

- `src/generate_mentoring_report_auto.py` - Main orchestrator
- `src/render_report.py` - JSON to HTML renderer
- `src/preprocess_documents.py` - Excel pre-processor
- `src/classify_files_llm.py` - File classifier
- `src/sharepoint_graph_client.py` - SharePoint integration
- `src/video_processing.py` - Video transcription with OpenAI Whisper
- `templates/mentoring_report_template.html` - Jinja2 template
- `pyproject.toml` - Dependencies and console script entry point

## Troubleshooting

**"Module not found: src"**
- Run `uv sync` to install dependencies
- Use `uv run mentoring-report` (not `uv run src/generate_...`)

**"Authentication failed"**
- Verify credentials in `.env`
- Check Azure app has correct API permissions
- Ensure admin consent is granted

**"No mentoring subfolder found"**
- AFM folder must contain a `mentoring` subfolder with files inside
