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
from datetime import datetime

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
        self.patched_files = []
        
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
            '*.txt',
            '*.xml',
            '*.yaml',
            '*.yml',
        ]
        
        found_files = []
        
        # Search for config files
        for pattern in config_patterns:
            try:
                files = list(self.build_path.rglob(pattern))
                found_files.extend(files)
            except:
                pass
        
        # Also check specific known config paths
        known_paths = [
            'RecRoom_Data/Resources/game.config',
            'RecRoom_Data/Resources/config.json',
            'config/game.config',
            'config.json',
            'game.config',
        ]
        
        for path in known_paths:
            full_path = self.build_path / path
            if full_path.exists() and full_path not in found_files:
                found_files.append(full_path)
        
        # Remove duplicates and filter out certain files
        self.config_files = list(set(found_files))
        
        # Remove artifacts and build files
        self.config_files = [f for f in self.config_files if not any(x in str(f) for x in ['.zip', '.exe', '.dll', '.so', '.dylib'])]
        
        logger.info(f"Found {len(self.config_files)} configuration files to scan")
        return self.config_files
    
    def patch_file(self, file_path: Path) -> bool:
        """Patch a configuration file"""
        try:
            # Try reading as text first
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace common server URL patterns
                patterns = [
                    # HTTPS URLs
                    (r'https?://[a-zA-Z0-9\-\.]*\.?recroom\.com[^\s"\']*', f'http://{self.server}'),
                    (r'https?://gameserver[^\s"\']*', f'http://{self.server}'),
                    (r'https?://api[^\s"\']*recroom[^\s"\']*', f'http://{self.server}'),
                    
                    # JSON fields
                    (r'"host"\s*:\s*"[^"]*recroom[^"]*"', f'"host": "{self.server}"'),
                    (r'"server"\s*:\s*"[^"]*recroom[^"]*"', f'"server": "{self.server}"'),
                    (r'"gameserver"\s*:\s*"[^"]*"', f'"gameserver": "{self.server}"'),
                    (r'"api_url"\s*:\s*"[^"]*"', f'"api_url": "http://{self.server}/api"'),
                    (r'"api_server"\s*:\s*"[^"]*"', f'"api_server": "http://{self.server}"'),
                    (r'"game_server"\s*:\s*"[^"]*"', f'"game_server": "http://{self.server}"'),
                    
                    # Config file formats
                    (r'(server|host|gameserver)\s*=\s*[^\n]*recroom[^\n]*', f'\\1={self.server}'),
                    (r'(api_url|api_server)\s*=\s*[^\n]*', f'\\1=http://{self.server}/api'),
                ]
                
                for pattern, replacement in patterns:
                    new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    if new_content != content:
                        content = new_content
                
                # Check if content changed
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"✓ Patched: {file_path.relative_to(self.build_path)}")
                    return True
                
                return False
            
            except UnicodeDecodeError:
                # Try binary patching for non-text files
                logger.debug(f"File appears to be binary: {file_path.name}")
                return False
        
        except Exception as e:
            logger.debug(f"Error patching {file_path}: {e}")
            return False
    
    def patch_build(self) -> bool:
        """Apply all patches to the build"""
        logger.info(f"Starting build patch...")
        logger.info(f"Target server: {self.server}")
        logger.info(f"Build path: {self.build_path}")
        
        self.find_config_files()
        
        if not self.config_files:
            logger.warning("No configuration files found to patch")
            return False
        
        patched_count = 0
        
        for config_file in self.config_files:
            try:
                if self.patch_file(config_file):
                    patched_count += 1
                    self.patched_files.append(str(config_file))
            except Exception as e:
                logger.debug(f"Error processing {config_file}: {e}")
        
        logger.info(f"Patching complete. Modified {patched_count} files.")
        
        if patched_count > 0:
            # Create patch manifest
            self.create_patch_manifest(patched_count)
            return True
        else:
            logger.warning("No files were actually modified - config may already be patched or no matches found")
            return False
    
    def create_patch_manifest(self, patched_files: int):
        """Create a manifest of applied patches"""
        manifest = {
            'patch_date': datetime.now().isoformat(),
            'server': self.server,
            'build_path': str(self.build_path),
            'patched_files': patched_files,
            'files': self.patched_files,
            'status': 'success'
        }
        
        manifest_path = self.build_path / 'YELLOREC_PATCH_MANIFEST.json'
        
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"✓ Patch manifest created: {manifest_path}")
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
            logger.warning("⚠ Build patching completed with no modifications - continuing anyway")
            exit(0)
    
    except Exception as e:
        logger.error(f"✗ Build patching failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
