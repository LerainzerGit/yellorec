#!/usr/bin/env python3
"""
Rec Room Build Downloader
Downloads and manages Rec Room builds from archive.recagain.site
"""

import os
import json
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('build-downloader')

# Configuration
ARCHIVE_URL = "https://archive.recagain.site"
BUILD_NUMBER = "20260323"
BUILDS_DIR = "./builds"
METADATA_FILE = "./builds/manifest.json"

class BuildDownloader:
    """Download and manage Rec Room builds"""
    
    def __init__(self, archive_url: str = ARCHIVE_URL, builds_dir: str = BUILDS_DIR):
        self.archive_url = archive_url
        self.builds_dir = Path(builds_dir)
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load or create build manifest"""
        if Path(METADATA_FILE).exists():
            try:
                with open(METADATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading manifest: {e}")
        
        return {
            "builds": {},
            "last_updated": None,
            "version": "1.0"
        }
    
    def _save_manifest(self):
        """Save build manifest"""
        try:
            with open(METADATA_FILE, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
    
    def get_available_builds(self) -> list:
        """Fetch list of available builds from archive"""
        try:
            logger.info(f"Fetching available builds from {self.archive_url}")
            response = requests.get(f"{self.archive_url}/api/builds", timeout=10)
            response.raise_for_status()
            return response.json().get('builds', [])
        except Exception as e:
            logger.error(f"Error fetching builds list: {e}")
            return []
    
    def download_build(self, build_number: str) -> bool:
        """Download specific build"""
        try:
            logger.info(f"Starting download of build {build_number}")
            
            # Check if already downloaded
            build_path = self.builds_dir / build_number
            if build_path.exists():
                logger.info(f"Build {build_number} already exists at {build_path}")
                return True
            
            # Download build
            download_url = f"{self.archive_url}/builds/{build_number}/download"
            logger.info(f"Downloading from {download_url}")
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create build directory
            build_path.mkdir(parents=True, exist_ok=True)
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Download and save build
            build_file = build_path / f"RecRoom_{build_number}.zip"
            with open(build_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {percent:.1f}%")
            
            logger.info(f"Build {build_number} downloaded successfully")
            
            # Update manifest
            self.manifest["builds"][build_number] = {
                "downloaded_at": datetime.now().isoformat(),
                "path": str(build_file),
                "size": os.path.getsize(build_file),
                "status": "downloaded"
            }
            self.manifest["last_updated"] = datetime.now().isoformat()
            self._save_manifest()
            
            return True
        
        except Exception as e:
            logger.error(f"Error downloading build {build_number}: {e}")
            return False
    
    def extract_build(self, build_number: str) -> bool:
        """Extract downloaded build"""
        try:
            import zipfile
            
            build_path = self.builds_dir / build_number
            build_file = build_path / f"RecRoom_{build_number}.zip"
            
            if not build_file.exists():
                logger.error(f"Build file not found: {build_file}")
                return False
            
            logger.info(f"Extracting build {build_number}")
            
            with zipfile.ZipFile(build_file, 'r') as zip_ref:
                zip_ref.extractall(build_path)
            
            logger.info(f"Build {build_number} extracted successfully")
            
            # Update manifest
            self.manifest["builds"][build_number]["status"] = "extracted"
            self._save_manifest()
            
            return True
        
        except Exception as e:
            logger.error(f"Error extracting build {build_number}: {e}")
            return False
    
    def verify_build(self, build_number: str) -> bool:
        """Verify build integrity"""
        try:
            build_path = self.builds_dir / build_number
            
            if not build_path.exists():
                logger.error(f"Build path does not exist: {build_path}")
                return False
            
            # Check for essential build files
            required_files = [
                "RecRoom.exe",
                "RecRoom_Data",
                "UnityPlayer.dll"
            ]
            
            found_files = []
            for file in required_files:
                if (build_path / file).exists():
                    found_files.append(file)
            
            if len(found_files) > 0:
                logger.info(f"Build {build_number} verification: Found {len(found_files)} essential files")
                self.manifest["builds"][build_number]["verified"] = True
                self._save_manifest()
                return True
            else:
                logger.warning(f"Build {build_number} verification: Missing essential files")
                return False
        
        except Exception as e:
            logger.error(f"Error verifying build {build_number}: {e}")
            return False
    
    def get_build_info(self, build_number: str) -> Optional[Dict[str, Any]]:
        """Get build information"""
        if build_number in self.manifest["builds"]:
            return self.manifest["builds"][build_number]
        return None
    
    def list_downloaded_builds(self) -> list:
        """List all downloaded builds"""
        return list(self.manifest["builds"].keys())

def main():
    """Main entry point"""
    downloader = BuildDownloader()
    
    logger.info("Rec Room Build Downloader")
    logger.info(f"Archive URL: {ARCHIVE_URL}")
    logger.info(f"Target Build: {BUILD_NUMBER}")
    
    # Fetch available builds
    available = downloader.get_available_builds()
    if available:
        logger.info(f"Found {len(available)} available builds")
    
    # Download build
    if downloader.download_build(BUILD_NUMBER):
        logger.info(f"Build {BUILD_NUMBER} download complete")
        
        # Extract build
        if downloader.extract_build(BUILD_NUMBER):
            logger.info(f"Build {BUILD_NUMBER} extraction complete")
            
            # Verify build
            if downloader.verify_build(BUILD_NUMBER):
                logger.info(f"Build {BUILD_NUMBER} verified successfully")
                logger.info("Build is ready to use with Yellorec server")
            else:
                logger.warning(f"Build {BUILD_NUMBER} verification failed")
    else:
        logger.error(f"Failed to download build {BUILD_NUMBER}")

if __name__ == '__main__':
    main()
