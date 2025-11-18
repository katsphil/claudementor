"""
SharePoint client using Microsoft Graph API and MSAL authentication.
Modern, secure approach for SharePoint integration.
"""

import os
import logging
import requests
import msal
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import quote
import colorlog


def login_to_sharepoint(
    sharepoint_tenant_id: str, 
    sharepoint_client_id: str, 
    sharepoint_client_secret: str
) -> str:
    """
    Authenticate with Microsoft Graph API using MSAL and client credentials.
    
    Args:
        sharepoint_tenant_id: Azure AD tenant ID
        sharepoint_client_id: Application (client) ID from Azure AD app registration
        sharepoint_client_secret: Client secret from Azure AD app registration
        
    Returns:
        Access token for Microsoft Graph API
        
    Raises:
        Exception: If authentication fails
    """
    logger = colorlog.getLogger(__name__)
    
    # Authority and scopes
    authority = f"https://login.microsoftonline.com/{sharepoint_tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]  # Using .default for application permissions

    # Create a ConfidentialClientApplication instance
    app = msal.ConfidentialClientApplication(
        sharepoint_client_id,
        authority=authority,
        client_credential=sharepoint_client_secret,
    )

    # Acquire a token (try silent first, then client credentials)
    result = app.acquire_token_silent(scope, account=None)
    if not result:
        logger.info("No cached token found, acquiring new token...")
        result = app.acquire_token_for_client(scopes=scope)

    if "access_token" not in result:
        logger.error("Could not obtain an access token:")
        logger.error(f"Error: {result.get('error')}")
        logger.error(f"Error description: {result.get('error_description')}")
        logger.error(f"Correlation ID: {result.get('correlation_id')}")
        raise Exception(f"Authentication failed: {result.get('error_description', 'Unknown error')}")

    access_token = result["access_token"]
    logger.info("Successfully authenticated with Microsoft Graph API")
    return access_token


class GraphSharePointClient:
    """Client for interacting with SharePoint using Microsoft Graph API."""
    
    def __init__(
        self, 
        tenant_id: Optional[str] = None, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None,
        site_name: Optional[str] = None,
        drive_name: Optional[str] = None
    ):
        """
        Initialize SharePoint Graph client.
        
        Args:
            tenant_id: Azure AD tenant ID (defaults to env var SHAREPOINT_TENANT_ID)
            client_id: Application (client) ID (defaults to env var SHAREPOINT_CLIENT_ID)
            client_secret: Client secret (defaults to env var SHAREPOINT_CLIENT_SECRET)
            site_name: SharePoint site name (defaults to env var SHAREPOINT_SITE_NAME)
            drive_name: Document library name (defaults to env var SHAREPOINT_DRIVE_NAME)
        """
        self.tenant_id = tenant_id or os.getenv("SHAREPOINT_TENANT_ID")
        self.client_id = client_id or os.getenv("SHAREPOINT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SHAREPOINT_CLIENT_SECRET")
        self.site_name = site_name or os.getenv("SHAREPOINT_SITE_NAME")
        self.drive_name = drive_name or os.getenv("SHAREPOINT_DRIVE_NAME")
        
        self.logger = colorlog.getLogger(__name__)
        
        # Validate required parameters
        if not all([self.tenant_id, self.client_id, self.client_secret, self.site_name]):
            raise ValueError(
                "Missing required SharePoint configuration. Set SHAREPOINT_TENANT_ID, "
                "SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET, and SHAREPOINT_SITE_NAME "
                "environment variables."
            )
        
        # Authenticate and get access token
        self.access_token = login_to_sharepoint(
            self.tenant_id, self.client_id, self.client_secret
        )
        
        # Set up Graph API headers
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get site and drive information
        self.site_id = self._get_site_id()
        self.drive_id = self._get_drive_id()
        
    def _get_site_id(self) -> str:
        """Get SharePoint site ID from Graph API."""
        # Assuming sharepoint.com domain - adjust if using different domain
        site_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{self.site_name}"
        
        response = requests.get(site_url, headers=self.headers)
        
        if response.status_code != 200:
            self.logger.error(f"Failed to get site ID: {response.status_code} - {response.text}")
            raise Exception(f"Failed to get site ID for '{self.site_name}': {response.text}")
        
        site_data = response.json()
        site_id = site_data["id"]
        self.logger.info(f"Found SharePoint site: {self.site_name} (ID: {site_id})")
        return site_id
    
    def _get_drive_id(self) -> str:
        """Get document library (drive) ID from Graph API."""
        if not self.drive_name:
            # If no drive name specified, use the default drive
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive"
        else:
            # Get all drives and find the one with matching name
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
        
        response = requests.get(drives_url, headers=self.headers)
        
        if response.status_code != 200:
            self.logger.error(f"Failed to get drive ID: {response.status_code} - {response.text}")
            raise Exception(f"Failed to get drive ID: {response.text}")
        
        drives_data = response.json()
        
        if not self.drive_name:
            # Using default drive
            drive_id = drives_data["id"]
            drive_name = drives_data["name"]
            self.logger.info(f"Using default drive: {drive_name} (ID: {drive_id})")
            return drive_id
        else:
            # Find drive by name
            drives = drives_data.get("value", [])
            for drive in drives:
                if drive["name"] == self.drive_name:
                    drive_id = drive["id"]
                    self.logger.info(f"Found drive: {self.drive_name} (ID: {drive_id})")
                    return drive_id
            
            # If not found by exact name, try case-insensitive search
            for drive in drives:
                if drive["name"].lower() == self.drive_name.lower():
                    drive_id = drive["id"]
                    self.logger.info(f"Found drive (case-insensitive): {drive['name']} (ID: {drive_id})")
                    return drive_id
            
            available_drives = [drive["name"] for drive in drives]
            raise Exception(
                f"Drive '{self.drive_name}' not found. Available drives: {available_drives}"
            )
    
    def search_folders(self, search_string: str, folder_path: str = "root") -> List[Dict[str, Any]]:
        """
        Search for folders containing the specified string using Graph API search.
        
        Args:
            search_string: String to search for in folder names
            folder_path: Base folder to search in (default: "root")
            
        Returns:
            List of folder information dictionaries
        """
        try:
            self.logger.info(f"Searching for folders containing '{search_string}' in '{folder_path}'")
            
            # Use Graph API search endpoint
            # Search query syntax: https://docs.microsoft.com/en-us/graph/search-query-parameter
            search_query = quote(f"{search_string} AND contentclass:STS_List_DocumentLibrary")
            search_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/{folder_path}/search(q='{search_string}')"
            
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                self.logger.error(f"Search failed: {response.status_code} - {response.text}")
                return []
            
            search_results = response.json()
            folders = []
            
            # Filter results to only include folders
            for item in search_results.get("value", []):
                if item.get("folder") is not None:  # This indicates it's a folder
                    folder_info = {
                        "id": item["id"],
                        "name": item["name"],
                        "web_url": item.get("webUrl"),
                        "parent_path": item.get("parentReference", {}).get("path", ""),
                        "item_count": item.get("folder", {}).get("childCount", 0)
                    }
                    folders.append(folder_info)
                    self.logger.info(f"Found folder: {item['name']} (ID: {item['id']})")
            
            self.logger.info(f"Found {len(folders)} folders containing '{search_string}'")
            return folders
            
        except Exception as e:
            self.logger.error(f"Error searching folders: {e}")
            raise
    
    def get_folder_items(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Get all items (files and subfolders) from a specific folder.
        
        Args:
            folder_id: SharePoint folder ID
            
        Returns:
            List of item information dictionaries
        """
        try:
            self.logger.info(f"Getting items from folder ID: {folder_id}")
            
            items_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{folder_id}/children"
            
            response = requests.get(items_url, headers=self.headers)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get folder items: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get items from folder: {response.text}")
            
            items_data = response.json()
            items = []
            
            for item in items_data.get("value", []):
                item_info = {
                    "id": item["id"],
                    "name": item["name"],
                    "type": "folder" if "folder" in item else "file",
                    "size": item.get("size", 0),
                    "download_url": item.get("@microsoft.graph.downloadUrl"),
                    "web_url": item.get("webUrl"),
                    "last_modified": item.get("lastModifiedDateTime")
                }
                items.append(item_info)
                
                item_type = "folder" if item_info["type"] == "folder" else "file"
                self.logger.debug(f"Found {item_type}: {item['name']} ({item_info['size']} bytes)")
            
            files_count = sum(1 for item in items if item["type"] == "file")
            folders_count = sum(1 for item in items if item["type"] == "folder")
            
            self.logger.info(f"Found {files_count} files and {folders_count} folders")
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting folder items: {e}")
            raise
    
    def download_file(self, file_item: Dict[str, Any], local_path: Path) -> Dict[str, str]:
        """
        Download a single file from SharePoint.
        
        Args:
            file_item: File information dictionary from get_folder_items()
            local_path: Local directory path where file should be saved
            
        Returns:
            Dictionary with download information
        """
        try:
            file_name = file_item["name"]
            file_size = file_item["size"]
            download_url = file_item.get("download_url")
            
            if not download_url:
                # If no direct download URL, use Graph API endpoint
                download_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{file_item['id']}/content"
            
            self.logger.info(f"Downloading file: {file_name} ({file_size} bytes)")
            
            # Download the file
            response = requests.get(download_url, headers=self.headers, stream=True)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to download file: {response.status_code} - {response.text}")
                raise Exception(f"Failed to download file '{file_name}': {response.text}")
            
            # Ensure local directory exists
            local_path.mkdir(parents=True, exist_ok=True)
            local_file_path = local_path / file_name
            
            # Write file to disk
            with open(local_file_path, 'wb') as local_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        local_file.write(chunk)
            
            # Verify file size
            actual_size = local_file_path.stat().st_size
            if actual_size != file_size:
                self.logger.warning(f"File size mismatch for {file_name}: expected {file_size}, got {actual_size}")
            
            download_info = {
                "name": file_name,
                "local_path": str(local_file_path),
                "size": actual_size,
                "sharepoint_id": file_item["id"],
                "web_url": file_item.get("web_url", "")
            }
            
            self.logger.info(f"Successfully downloaded: {file_name}")
            return download_info
            
        except Exception as e:
            self.logger.error(f"Error downloading file '{file_item.get('name', 'unknown')}': {e}")
            raise
    
    def download_folder_files(self, folder_id: str, local_download_path: Path, recursive: bool = False) -> List[Dict[str, str]]:
        """
        Download all files from a SharePoint folder.
        
        Args:
            folder_id: SharePoint folder ID
            local_download_path: Local path where files should be downloaded
            recursive: Whether to recursively download from subfolders
            
        Returns:
            List of dictionaries with file download information
        """
        try:
            self.logger.info(f"Downloading files from folder ID: {folder_id}")
            
            # Get all items in the folder
            items = self.get_folder_items(folder_id)
            
            downloaded_files = []
            
            for item in items:
                if item["type"] == "file":
                    try:
                        download_info = self.download_file(item, local_download_path)
                        downloaded_files.append(download_info)
                    except Exception as e:
                        self.logger.error(f"Failed to download file '{item['name']}': {e}")
                        continue
                        
                elif item["type"] == "folder" and recursive:
                    # Create subfolder and download recursively
                    subfolder_path = local_download_path / item["name"]
                    self.logger.info(f"Processing subfolder: {item['name']}")
                    
                    subfolder_files = self.download_folder_files(
                        item["id"], subfolder_path, recursive=True
                    )
                    downloaded_files.extend(subfolder_files)
            
            self.logger.info(f"Downloaded {len(downloaded_files)} files from folder")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Error downloading files from folder '{folder_id}': {e}")
            raise


def download_sharepoint_files(
    search_string: str,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    site_name: Optional[str] = None,
    drive_name: Optional[str] = None,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    Main function to search SharePoint folders and download files using Microsoft Graph API.
    
    Args:
        search_string: String to search for in folder names
        tenant_id: Azure AD tenant ID (optional, uses env var if not provided)
        client_id: Application (client) ID (optional, uses env var if not provided)
        client_secret: Client secret (optional, uses env var if not provided)
        site_name: SharePoint site name (optional, uses env var if not provided)
        drive_name: Document library name (optional, uses env var if not provided)
        recursive: Whether to recursively download from subfolders
        
    Returns:
        Dictionary with search results and downloaded files information
    """
    logger = colorlog.getLogger(__name__)
    
    try:
        # Initialize SharePoint Graph client
        client = GraphSharePointClient(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            site_name=site_name,
            drive_name=drive_name
        )
        
        # Search for folders containing the search string
        matching_folders = client.search_folders(search_string)
        
        # Filter results to only include folders where the AFM appears in the folder name
        # This eliminates false positives from content/metadata matches
        name_filtered_folders = [
            folder for folder in matching_folders 
            if search_string.lower() in folder['name'].lower()
        ]
        
        if name_filtered_folders != matching_folders:
            logger.info(f"Filtered {len(matching_folders)} search results to {len(name_filtered_folders)} folders with AFM in name")
            matching_folders = name_filtered_folders
        
        if not matching_folders:
            logger.warning(f"No folders found containing '{search_string}'")
            return {
                'search_string': search_string,
                'matching_folders': [],
                'downloaded_files': [],
                'total_files_downloaded': 0,
                'local_downloads_path': ""
            }
        
        # Create local downloads directory
        project_root = Path(__file__).parent
        downloads_dir = project_root / "downloads" / search_string
        
        all_downloaded_files = []
        
        # Download files from each matching folder's 'mentoring' subfolder
        for folder_info in matching_folders:
            logger.info(f"Processing folder: {folder_info['name']}")
            
            # Look for 'mentoring' subfolder within the AFM folder
            try:
                folder_items = client.get_folder_items(folder_info['id'])
                mentoring_folder = None
                
                # Find the 'mentoring' subfolder
                for item in folder_items:
                    if item["type"] == "folder" and item["name"].lower() == "mentoring":
                        mentoring_folder = item
                        break
                
                if not mentoring_folder:
                    logger.warning(f"No 'mentoring' subfolder found in '{folder_info['name']}' - skipping this folder")
                    continue
                
                logger.info(f"Found 'mentoring' subfolder in '{folder_info['name']}' - downloading files from there")
                
                # Create subdirectory for this folder
                local_folder_dir = downloads_dir / folder_info['name']
                
                downloaded_files = client.download_folder_files(
                    mentoring_folder['id'], local_folder_dir, recursive=recursive
                )
                all_downloaded_files.extend(downloaded_files)
                
            except Exception as e:
                logger.error(f"Error processing folder '{folder_info['name']}': {e}")
                continue
        
        result = {
            'search_string': search_string,
            'matching_folders': matching_folders,
            'downloaded_files': all_downloaded_files,
            'total_files_downloaded': len(all_downloaded_files),
            'local_downloads_path': str(downloads_dir)
        }
        
        logger.info(f"Successfully downloaded {len(all_downloaded_files)} files from {len(matching_folders)} folders")
        return result
        
    except Exception as e:
        logger.error(f"Failed to download SharePoint files: {e}")
        raise