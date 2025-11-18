# AFM-Based SharePoint Integration

## Overview

The mentoring report generator now supports AFM-based file retrieval from SharePoint. Simply provide an AFM number, and the system will automatically:
1. Search SharePoint for the AFM folder
2. Locate the "mentoring" subfolder
3. Download files to working directory
4. Generate the comprehensive mentoring report

## Setup

### 1. Install Dependencies

```bash
uv sync
```

This installs the required SharePoint dependencies:
- `msal` - Microsoft authentication
- `python-dotenv` - Environment variable management
- `colorlog` - Enhanced logging
- `requests` - HTTP client

### 2. Configure SharePoint Credentials

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your SharePoint credentials:

```env
SHAREPOINT_TENANT_ID="your-tenant-id-here"
SHAREPOINT_CLIENT_ID="your-client-application-id-here"
SHAREPOINT_CLIENT_SECRET="your-client-secret-here"
SHAREPOINT_SITE_NAME="axiologiseis"
SHAREPOINT_DRIVE_NAME="Έγγραφα"
```

#### Getting SharePoint Credentials

1. Go to Azure Portal → App Registrations
2. Create or select your app
3. Note the:
   - **Application (client) ID** → SHAREPOINT_CLIENT_ID
   - **Directory (tenant) ID** → SHAREPOINT_TENANT_ID
4. Create a client secret:
   - Certificates & secrets → New client secret
   - Copy the **Value** → SHAREPOINT_CLIENT_SECRET
5. Grant API permissions:
   - API permissions → Add permission → Microsoft Graph
   - Application permissions → Sites.Read.All, Files.Read.All
   - Grant admin consent

## Usage

### Option 1: AFM-Based (SharePoint)

```bash
uv run src/generate_mentoring_report_auto.py --afm 071477247
```

This will:
- Authenticate with SharePoint
- Search for folder containing AFM "071477247"
- Find the "mentoring" subfolder within it
- Download all files to `working_dir/071477247_[timestamp]/`
- Generate the mentoring report

### Option 2: Direct Folder Path (Backward Compatible)

```bash
uv run src/generate_mentoring_report_auto.py "path/to/business/folder"
```

Works exactly as before - no SharePoint needed.

### Option 3: Interactive Mode

```bash
uv run src/generate_mentoring_report_auto.py
```

The script will prompt you to choose:
- [1] AFM search (SharePoint)
- [2] Direct folder path

## SharePoint Folder Structure Expected

```
SharePoint Site: axiologiseis
└── Έγγραφα (Documents)
    └── [AFM_NUMBER]/  (e.g., "ΤΟΣΙΟΣ ΚΩΝΣΤΑΝΤΙΝΟΣ - 071477247 - ΕΑΤ")
        └── mentoring/  (REQUIRED - files downloaded from here)
            ├── document1.pdf
            ├── spreadsheet.xlsx
            ├── report.docx
            └── ...
```

**Important**: The system specifically looks for a subfolder named "mentoring" (case-insensitive) within the AFM folder.

## Output

All modes produce the same output structure in `working_dir/[AFM]_[timestamp]/`:

```
working_dir/071477247_20251118_193045/
├── document1.pdf                     ← Source files (from SharePoint or local)
├── spreadsheet.xlsx                  ← Source files
├── section_1_generated.json         ← Generated sections
├── section_2_generated.json         ← Generated sections
├── ...
├── mentoring_report_complete.json   ← Compiled report
└── mentoring_report.html            ← Final HTML report
```

## Error Handling

### AFM not found
```
[ERROR] No folders found in SharePoint for AFM: 071477247

Please check:
  1. AFM is correct
  2. SharePoint contains a folder with this AFM
  3. SharePoint credentials are configured in .env
```

### No mentoring subfolder
```
[ERROR] No 'mentoring' subfolder found in AFM folder

Searched in: ΤΟΣΙΟΣ ΚΩΝΣΤΑΝΤΙΝΟΣ - 071477247 - ΕΑΤ
```

### Authentication failure
```
[ERROR] Failed to download from SharePoint: Authentication failed: [details]
```

Check your `.env` credentials and ensure API permissions are granted.

## Troubleshooting

### "Module not found: sharepoint_graph_client"
Run `uv sync` to install dependencies.

### "Authentication failed"
1. Verify credentials in `.env`
2. Check Azure app has correct API permissions
3. Ensure admin consent is granted
4. Verify tenant ID is correct

### "No mentoring subfolder found"
The AFM folder must contain a subfolder named "mentoring" (case-insensitive). Files must be inside this subfolder.

## Development

To add logging or modify SharePoint behavior, edit:
- `src/sharepoint_graph_client.py` - SharePoint integration
- `src/generate_mentoring_report_auto.py` - Main workflow (download_from_sharepoint function)
