#!/usr/bin/env python3
"""
Rec Room Build Patcher
Modifies game configuration to redirect to Yellorec server
"""

import os
import json
import struct
import logging
from pathlib import Path
from typing import Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('patch-build')

# Configuration
YELLOREC_SERVER = os.getenv('YELLOREC_SERVER', 'localhost:8080')
BUILD_PATH = os.getenv('BUILD_PATH', './builds/20260323')

class BuildPatcher:
    """Patch Rec Room build to use custom server"""
    
    def __init__(self, build_path: str = BUILD_PATH, server: str = YELLOREC_SERVER):
        self.build_path = Path(build_path)
        self.server = server
        self.config_files = []
        
        if not self.build_path.exists():
            logger.error(f"Build path does not exist: {self.build_path}")
            raise FileNotFoundError(f"Build path not found: {self.build_path}")
    
    def find_config_files(self) -> list:
        """Find configuration files in the build"""
        config_patterns = [
            '*.json',
            '*.config',
            '*.cfg',
            '*.ini',
            '*config*.txt',
            'RecRoom_Data/Resources/game.config',
        ]
        
        found_files = []
        for pattern in config_patterns:
            files = self.build_path.glob(f'**/{pattern}')
            found_files.extend(files)
        
        # Remove duplicates
        self.config_files = list(set(found_files))
        logger.info(f"Found {len(self.config_files)} configuration files")
        return self.config_files
    
    def patch_json_config(self, file_path: Path) -> bool:
        """Patch JSON configuration files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            # Replace common server URL patterns
            patterns = [
                (r'https?://[^"\s]+\.recroom\.com', f'http://{self.server}'),
                (r'"host"\s*:\s*"[^"]*recroom[^"]*"', f'"host": "{self.server}"'),
                (r'"server"\s*:\s*"[^"]*recroom[^"]*"', f'"server": "{self.server}"'),
                (r'"gameserver"\s*:\s*"[^"]*"', f'"gameserver": "{self.server}"'),
                (r'"api_url"\s*:\s*"[^"]*"', f'"api_url": "http://{self.server}/api"'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Patched JSON: {file_path.name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error patching JSON {file_path}: {e}")
            return False
    
    def patch_text_config(self, file_path: Path) -> bool:
        """Patch text-based configuration files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            original_lines = lines.copy()
            patched = False
            
            for i, line in enumerate(lines):
                # Patch server URLs in config files
                if 'recroom.com' in line.lower() or 'gameserver' in line.lower():
                    new_line = re.sub(
                        r'https?://[^"\s]+\.recroom[^"\s]*',
                        f'http://{self.server}',
                        line,
                        flags=re.IGNORECASE
                    )
                    
                    # Also patch server= or host= assignments
                    new_line = re.sub(
                        r'(server|host|gameserver)\s*=\s*[^\n]*',
                        f'\\1={self.server}',
                        new_line,
                        flags=re.IGNORECASE
                    )
                    
                    if new_line != line:
                        lines[i] = new_line
                        patched = True
            
            if patched and lines != original_lines:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"Patched config: {file_path.name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error patching config {file_path}: {e}")
            return False
    
    def patch_binary_config(self, file_path: Path) -> bool:
        """Patch binary configuration files (DLL, asset bundles, etc.)"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            original_content = content
            
            # Search for URL patterns in binary files
            old_urls = [
                b'https://api.recroom.com',
                b'https://gameserver.recroom.com',
                b'https://www.recroom.com',
                b'api.recroom.com',
                b'gameserver.recroom.com',
                b'www.recroom.com',
            ]
            
            new_url = f'http://{self.server}'.encode('utf-8')
            patched = False
            
            for old_url in old_urls:
                if old_url in content:
                    # Pad with nulls to maintain binary structure
                    if len(new_url) <= len(old_url):
                        padded_url = new_url + b'\x00' * (len(old_url) - len(new_url))
                        content = content.replace(old_url, padded_url)
                        patched = True
                        logger.info(f"Replaced {old_url} in binary: {file_path.name}")
            
            if patched and content != original_content:
                with open(file_path, 'wb') as f:
                    f.write(content)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error patching binary {file_path}: {e}")
            return False
    
    def patch_build(self) -> bool:
        """Apply all patches to the build"""
        logger.info(f"Starting build patch...")
        logger.info(f"Target server: {self.server}")
        
        self.find_config_files()
        
        patched_count = 0
        
        for config_file in self.config_files:
            try:
                # Determine file type and patch accordingly
                if config_file.suffix == '.json':
                    if self.patch_json_config(config_file):
                        patched_count += 1
                elif config_file.suffix in ['.config', '.cfg', '.ini', '.txt']:
                    if self.patch_text_config(config_file):
                        patched_count += 1
                elif config_file.suffix in ['.dll', '.so', '.dylib', '.unity3d', '.assetbundle']:
                    if self.patch_binary_config(config_file):
                        patched_count += 1
                else:
                    # Try text first, then binary
                    if not self.patch_text_config(config_file):
                        self.patch_binary_config(config_file)
            
            except Exception as e:
                logger.error(f"Error processing {config_file}: {e}")
        
        logger.info(f"Patching complete. Modified {patched_count} files.")
        
        # Create patch manifest
        self.create_patch_manifest(patched_count)
        
        return patched_count > 0
    
    def create_patch_manifest(self, patched_files: int):
        """Create a manifest of applied patches"""
        manifest = {
            'patch_date': str(Path.ctime),
            'server': self.server,
            'build_path': str(self.build_path),
            'patched_files': patched_files,
            'status': 'success'
        }
        
        manifest_path = self.build_path / 'YELLOREC_PATCH_MANIFEST.json'
        
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Patch manifest created: {manifest_path}")
        except Exception as e:
            logger.error(f"Error creating patch manifest: {e}")

def main():
    """Main entry point"""
    try:
        patcher = BuildPatcher(BUILD_PATH, YELLOREC_SERVER)
        
        if patcher.patch_build():
            logger.info("✓ Build successfully patched for Yellorec server")
            exit(0)
        else:
            logger.warning("⚠ Build patching completed with no modifications")
            exit(0)
    
    except Exception as e:
        logger.error(f"✗ Build patching failed: {e}")
        exit(1)

if __name__ == '__main__':
    main()
