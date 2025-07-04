#!/usr/bin/env python3
"""
NEXUS Packager - Binary creation and distribution system
Handles packaging, installers, distribution, and configuration
Target: <100MB download size
"""

import os
import sys
import json
import shutil
import hashlib
import platform
import subprocess
import tempfile
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import requests
import PyInstaller.__main__
from packaging import version

class NexusPackager:
    """Main packaging and distribution system for NEXUS"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.release_dir = self.project_root / "releases"
        self.config_dir = self.project_root / "config"
        
        # Platform detection
        self.platform = self._detect_platform()
        self.arch = platform.machine().lower()
        
        # Version info
        self.version = self._get_version()
        self.build_number = self._get_build_number()
        
        # Package configuration
        self.package_config = {
            "name": "nexus-mind",
            "display_name": "NEXUS Mind",
            "description": "Advanced AI-powered development assistant",
            "author": "NEXUS Team",
            "url": "https://nexus-mind.ai",
            "license": "MIT",
            "icon": self.project_root / "assets" / "nexus-icon",
            "main_script": "nexus_cli.py",
            "hidden_imports": [
                "tiktoken_ext.openai_public",
                "tiktoken_ext",
                "numpy",
                "scipy",
                "sklearn",
                "torch",
                "transformers"
            ],
            "excluded_modules": [
                "matplotlib",
                "pandas",
                "jupyter",
                "notebook",
                "ipython",
                "pytest",
                "sphinx"
            ],
            "data_files": [
                ("config", "*.json"),
                ("templates", "*.html"),
                ("assets", "*.png"),
                ("assets", "*.ico"),
                ("assets", "*.icns")
            ]
        }

    def _detect_platform(self) -> str:
        """Detect current platform"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            raise ValueError(f"Unsupported platform: {system}")

    def _get_version(self) -> str:
        """Get version from package or git"""
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "0.1.0"

    def _get_build_number(self) -> str:
        """Get build number from git or timestamp"""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return datetime.now().strftime("%Y%m%d%H%M%S")

    def create_binary(self) -> Path:
        """Create platform-specific binary using PyInstaller"""
        print(f"Creating binary for {self.platform} {self.arch}...")
        
        # Prepare build directories
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        # PyInstaller spec file
        spec_content = self._generate_spec_file()
        spec_file = self.build_dir / "nexus.spec"
        spec_file.write_text(spec_content)
        
        # Build command
        args = [
            str(spec_file),
            f"--distpath={self.dist_dir}",
            f"--workpath={self.build_dir / 'work'}",
            "--clean",
            "--noconfirm"
        ]
        
        # Platform-specific options
        if self.platform == "macos":
            args.extend(["--osx-bundle-identifier", "ai.nexus-mind.app"])
        elif self.platform == "windows":
            args.extend(["--version-file", str(self._create_version_file())])
        
        # Run PyInstaller
        PyInstaller.__main__.run(args)
        
        # Optimize size
        binary_path = self._optimize_binary()
        
        print(f"Binary created: {binary_path}")
        print(f"Size: {self._get_file_size_mb(binary_path):.1f} MB")
        
        return binary_path

    def _generate_spec_file(self) -> str:
        """Generate PyInstaller spec file"""
        icon_ext = {
            "macos": "icns",
            "windows": "ico",
            "linux": "png"
        }[self.platform]
        
        icon_path = f"{self.package_config['icon']}.{icon_ext}"
        
        spec_template = f"""
# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Collect all necessary data
datas = []
hiddenimports = {self.package_config['hidden_imports']}
binaries = []

# Add data files
for pattern, dest in {self.package_config['data_files']}:
    datas.extend(collect_data_files(pattern, dest))

# Analysis
a = Analysis(
    ['{self.package_config['main_script']}'],
    pathex=['{self.project_root}'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={self.package_config['excluded_modules']},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary files
a.binaries = [b for b in a.binaries if not any(
    x in b[0] for x in ['test', 'example', 'demo', '_test']
)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.package_config['name']}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}'
)

# Platform-specific bundling
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='{self.package_config['display_name']}.app',
        icon='{icon_path}',
        bundle_identifier='ai.nexus-mind.app',
        info_plist={{
            'CFBundleDisplayName': '{self.package_config['display_name']}',
            'CFBundleVersion': '{self.version}',
            'CFBundleShortVersionString': '{self.version}',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0'
        }},
    )
"""
        return spec_template

    def _optimize_binary(self) -> Path:
        """Optimize binary size using UPX and stripping"""
        binary_name = self.package_config['name']
        if self.platform == "windows":
            binary_name += ".exe"
        elif self.platform == "macos":
            binary_name = f"{self.package_config['display_name']}.app"
        
        binary_path = self.dist_dir / binary_name
        
        # Strip debug symbols (Linux/macOS)
        if self.platform in ["linux", "macos"] and not binary_path.is_dir():
            try:
                subprocess.run(["strip", str(binary_path)], check=True)
                print("Stripped debug symbols")
            except:
                pass
        
        # Compress with UPX
        if not binary_path.is_dir():
            try:
                subprocess.run(
                    ["upx", "--best", "--lzma", str(binary_path)],
                    check=True
                )
                print("Compressed with UPX")
            except:
                print("UPX compression skipped (not installed)")
        
        return binary_path

    def create_installer(self) -> Path:
        """Create platform-specific installer"""
        print(f"Creating installer for {self.platform}...")
        
        if self.platform == "macos":
            return self._create_dmg()
        elif self.platform == "windows":
            return self._create_msi()
        elif self.platform == "linux":
            return self._create_appimage()

    def _create_dmg(self) -> Path:
        """Create macOS DMG installer"""
        dmg_name = f"{self.package_config['name']}-{self.version}-{self.arch}.dmg"
        dmg_path = self.release_dir / dmg_name
        self.release_dir.mkdir(exist_ok=True)
        
        # Create temporary directory for DMG contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy app bundle
            app_source = self.dist_dir / f"{self.package_config['display_name']}.app"
            app_dest = temp_path / f"{self.package_config['display_name']}.app"
            shutil.copytree(app_source, app_dest)
            
            # Create Applications symlink
            apps_link = temp_path / "Applications"
            apps_link.symlink_to("/Applications")
            
            # Create DMG
            cmd = [
                "hdiutil", "create",
                "-volname", self.package_config['display_name'],
                "-srcfolder", str(temp_path),
                "-ov",
                "-format", "UDZO",
                str(dmg_path)
            ]
            
            subprocess.run(cmd, check=True)
        
        # Sign DMG if certificate available
        self._sign_macos(dmg_path)
        
        return dmg_path

    def _create_msi(self) -> Path:
        """Create Windows MSI installer using WiX"""
        msi_name = f"{self.package_config['name']}-{self.version}-{self.arch}.msi"
        msi_path = self.release_dir / msi_name
        self.release_dir.mkdir(exist_ok=True)
        
        # Generate WiX configuration
        wxs_content = self._generate_wix_config()
        wxs_file = self.build_dir / "nexus.wxs"
        wxs_file.write_text(wxs_content)
        
        # Build MSI
        try:
            # Compile
            subprocess.run([
                "candle",
                "-arch", "x64" if "64" in self.arch else "x86",
                str(wxs_file),
                "-o", str(self.build_dir / "nexus.wixobj")
            ], check=True)
            
            # Link
            subprocess.run([
                "light",
                str(self.build_dir / "nexus.wixobj"),
                "-o", str(msi_path)
            ], check=True)
        except FileNotFoundError:
            print("WiX Toolset not found, creating zip instead")
            return self._create_windows_zip()
        
        # Sign MSI if certificate available
        self._sign_windows(msi_path)
        
        return msi_path

    def _create_appimage(self) -> Path:
        """Create Linux AppImage"""
        appimage_name = f"{self.package_config['name']}-{self.version}-{self.arch}.AppImage"
        appimage_path = self.release_dir / appimage_name
        self.release_dir.mkdir(exist_ok=True)
        
        # Create AppDir structure
        with tempfile.TemporaryDirectory() as temp_dir:
            appdir = Path(temp_dir) / "nexus.AppDir"
            appdir.mkdir()
            
            # Copy binary
            binary_source = self.dist_dir / self.package_config['name']
            binary_dest = appdir / "usr" / "bin" / self.package_config['name']
            binary_dest.parent.mkdir(parents=True)
            shutil.copy2(binary_source, binary_dest)
            binary_dest.chmod(0o755)
            
            # Create desktop entry
            desktop_entry = f"""[Desktop Entry]
Name={self.package_config['display_name']}
Exec={self.package_config['name']}
Icon=nexus
Type=Application
Categories=Development;
Comment={self.package_config['description']}
"""
            desktop_file = appdir / f"{self.package_config['name']}.desktop"
            desktop_file.write_text(desktop_entry)
            
            # Copy icon
            icon_source = f"{self.package_config['icon']}.png"
            if Path(icon_source).exists():
                icon_dest = appdir / "nexus.png"
                shutil.copy2(icon_source, icon_dest)
            
            # Create AppRun script
            apprun = appdir / "AppRun"
            apprun.write_text(f"""#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${{SELF%/*}}
export PATH="${{HERE}}/usr/bin:${{PATH}}"
exec "${{HERE}}/usr/bin/{self.package_config['name']}" "$@"
""")
            apprun.chmod(0o755)
            
            # Build AppImage
            try:
                subprocess.run([
                    "appimagetool",
                    str(appdir),
                    str(appimage_path)
                ], check=True)
            except FileNotFoundError:
                print("appimagetool not found, creating tarball instead")
                return self._create_linux_tarball()
        
        return appimage_path

    def _create_windows_zip(self) -> Path:
        """Fallback: Create Windows ZIP distribution"""
        zip_name = f"{self.package_config['name']}-{self.version}-{self.arch}-windows.zip"
        zip_path = self.release_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add executable
            exe_path = self.dist_dir / f"{self.package_config['name']}.exe"
            zf.write(exe_path, f"{self.package_config['name']}.exe")
            
            # Add batch launcher
            launcher_content = f"""@echo off
"{self.package_config['name']}.exe" %*
"""
            zf.writestr("nexus.bat", launcher_content)
            
            # Add README
            readme_content = f"""# {self.package_config['display_name']} v{self.version}

## Installation
1. Extract this ZIP file to your desired location
2. Add the directory to your PATH
3. Run 'nexus' from any command prompt

## Uninstallation
1. Delete the extracted directory
2. Remove from PATH
"""
            zf.writestr("README.txt", readme_content)
        
        return zip_path

    def _create_linux_tarball(self) -> Path:
        """Fallback: Create Linux tarball distribution"""
        tar_name = f"{self.package_config['name']}-{self.version}-{self.arch}-linux.tar.gz"
        tar_path = self.release_dir / tar_name
        
        with tarfile.open(tar_path, 'w:gz') as tf:
            # Add binary
            binary_path = self.dist_dir / self.package_config['name']
            tf.add(binary_path, f"{self.package_config['name']}/bin/{self.package_config['name']}")
            
            # Add launcher script
            launcher_content = f"""#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
exec "${{SCRIPT_DIR}}/bin/{self.package_config['name']}" "$@"
"""
            launcher_info = tarfile.TarInfo(f"{self.package_config['name']}/nexus")
            launcher_info.size = len(launcher_content.encode())
            launcher_info.mode = 0o755
            tf.addfile(launcher_info, io.BytesIO(launcher_content.encode()))
            
            # Add install script
            install_content = f"""#!/bin/bash
echo "Installing {self.package_config['display_name']}..."
sudo cp -r {self.package_config['name']} /opt/
sudo ln -sf /opt/{self.package_config['name']}/nexus /usr/local/bin/nexus
echo "Installation complete. Run 'nexus' to start."
"""
            install_info = tarfile.TarInfo(f"install.sh")
            install_info.size = len(install_content.encode())
            install_info.mode = 0o755
            tf.addfile(install_info, io.BytesIO(install_content.encode()))
        
        return tar_path

    def create_homebrew_formula(self) -> Path:
        """Create Homebrew formula for macOS"""
        formula_name = f"{self.package_config['name']}.rb"
        formula_path = self.release_dir / "homebrew" / formula_name
        formula_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate SHA256 of the release
        release_file = self.release_dir / f"{self.package_config['name']}-{self.version}-{self.arch}.tar.gz"
        if release_file.exists():
            sha256 = self._calculate_sha256(release_file)
        else:
            sha256 = "PLACEHOLDER_SHA256"
        
        formula_content = f"""class NexusMind < Formula
  desc "{self.package_config['description']}"
  homepage "{self.package_config['url']}"
  url "https://github.com/nexus-mind/nexus/releases/download/v{self.version}/{release_file.name}"
  sha256 "{sha256}"
  license "{self.package_config['license']}"

  depends_on "python@3.11"

  def install
    bin.install "nexus"
    
    # Install shell completions
    bash_completion.install "completions/nexus.bash" => "nexus"
    zsh_completion.install "completions/nexus.zsh" => "_nexus"
    fish_completion.install "completions/nexus.fish"
  end

  test do
    system "#{bin}/nexus", "--version"
  end
end
"""
        formula_path.write_text(formula_content)
        return formula_path

    def setup_distribution(self) -> Dict[str, Any]:
        """Setup distribution channels"""
        print("Setting up distribution...")
        
        distribution = {
            "github_release": self._setup_github_release(),
            "update_server": self._setup_update_server(),
            "mirrors": self._setup_mirrors(),
            "package_managers": self._setup_package_managers()
        }
        
        return distribution

    def _setup_github_release(self) -> Dict[str, Any]:
        """Setup GitHub release configuration"""
        release_config = {
            "tag": f"v{self.version}",
            "name": f"NEXUS Mind v{self.version}",
            "body": self._generate_release_notes(),
            "draft": False,
            "prerelease": "beta" in self.version or "alpha" in self.version,
            "assets": []
        }
        
        # Find all release files
        for file in self.release_dir.glob("*"):
            if file.is_file():
                release_config["assets"].append({
                    "path": str(file),
                    "name": file.name,
                    "content_type": self._get_content_type(file)
                })
        
        # Create release script
        script_path = self.release_dir / "create_github_release.sh"
        script_content = f"""#!/bin/bash
# GitHub Release Script for NEXUS Mind v{self.version}

GITHUB_TOKEN="${{GITHUB_TOKEN}}"
REPO="nexus-mind/nexus"
TAG="{release_config['tag']}"

# Create release
gh release create "$TAG" \\
  --title "{release_config['name']}" \\
  --notes '{release_config['body']}' \\
  {"--prerelease" if release_config['prerelease'] else ""} \\
  {' '.join(f'"{asset["path"]}"' for asset in release_config['assets'])}
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return release_config

    def _setup_update_server(self) -> Dict[str, Any]:
        """Setup auto-update server configuration"""
        update_config = {
            "endpoint": "https://updates.nexus-mind.ai",
            "channels": {
                "stable": {
                    "version": self.version,
                    "platforms": {}
                },
                "beta": {
                    "version": f"{self.version}-beta",
                    "platforms": {}
                },
                "nightly": {
                    "version": f"{self.version}-nightly.{self.build_number}",
                    "platforms": {}
                }
            }
        }
        
        # Add platform-specific update info
        for platform in ["macos", "windows", "linux"]:
            for channel in update_config["channels"]:
                update_config["channels"][channel]["platforms"][platform] = {
                    "url": f"https://updates.nexus-mind.ai/{channel}/{platform}/latest",
                    "sha256": "PLACEHOLDER",
                    "size": 0,
                    "min_version": "0.1.0"
                }
        
        # Save update manifest
        manifest_path = self.release_dir / "update_manifest.json"
        manifest_path.write_text(json.dumps(update_config, indent=2))
        
        return update_config

    def _setup_mirrors(self) -> List[Dict[str, str]]:
        """Setup mirror distribution points"""
        mirrors = [
            {
                "name": "Primary CDN",
                "url": "https://cdn.nexus-mind.ai/releases",
                "location": "Global"
            },
            {
                "name": "GitHub Releases",
                "url": "https://github.com/nexus-mind/nexus/releases",
                "location": "Global"
            },
            {
                "name": "SourceForge",
                "url": "https://sourceforge.net/projects/nexus-mind",
                "location": "Global"
            }
        ]
        
        # Save mirror list
        mirror_path = self.release_dir / "mirrors.json"
        mirror_path.write_text(json.dumps(mirrors, indent=2))
        
        return mirrors

    def _setup_package_managers(self) -> Dict[str, Dict[str, Any]]:
        """Setup package manager configurations"""
        configs = {}
        
        # Homebrew (macOS/Linux)
        configs["homebrew"] = {
            "tap": "nexus-mind/nexus",
            "formula": "nexus-mind",
            "install": "brew install nexus-mind/nexus/nexus-mind"
        }
        
        # Chocolatey (Windows)
        configs["chocolatey"] = {
            "package": "nexus-mind",
            "install": "choco install nexus-mind",
            "nuspec": self._generate_chocolatey_nuspec()
        }
        
        # Snap (Linux)
        configs["snap"] = {
            "name": "nexus-mind",
            "install": "snap install nexus-mind",
            "yaml": self._generate_snapcraft_yaml()
        }
        
        # APT (Debian/Ubuntu)
        configs["apt"] = {
            "package": "nexus-mind",
            "repository": "deb https://apt.nexus-mind.ai stable main",
            "install": "apt install nexus-mind"
        }
        
        # YUM/DNF (RedHat/Fedora)
        configs["yum"] = {
            "package": "nexus-mind",
            "repository": "https://yum.nexus-mind.ai",
            "install": "yum install nexus-mind"
        }
        
        return configs

    def create_configuration_system(self) -> None:
        """Create first-run configuration system"""
        config_system = ConfigurationSystem(self.project_root)
        config_system.create_all()

    def create_uninstaller(self) -> None:
        """Create uninstallation system"""
        uninstaller = UninstallSystem(self.project_root)
        uninstaller.create_all()

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        if file_path.is_file():
            return file_path.stat().st_size / (1024 * 1024)
        elif file_path.is_dir():
            total_size = 0
            for item in file_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size / (1024 * 1024)
        return 0

    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME content type for file"""
        ext_map = {
            ".dmg": "application/x-apple-diskimage",
            ".msi": "application/x-msi",
            ".exe": "application/x-msdownload",
            ".AppImage": "application/x-executable",
            ".tar.gz": "application/gzip",
            ".zip": "application/zip",
            ".deb": "application/x-debian-package",
            ".rpm": "application/x-rpm"
        }
        
        for ext, content_type in ext_map.items():
            if file_path.name.endswith(ext):
                return content_type
        
        return "application/octet-stream"

    def _sign_macos(self, file_path: Path) -> None:
        """Sign macOS binary/package"""
        if os.environ.get("APPLE_DEVELOPER_ID"):
            try:
                subprocess.run([
                    "codesign",
                    "--deep",
                    "--force",
                    "--verify",
                    "--verbose",
                    "--sign", os.environ["APPLE_DEVELOPER_ID"],
                    "--options", "runtime",
                    str(file_path)
                ], check=True)
                print(f"Signed: {file_path}")
                
                # Notarize
                if os.environ.get("APPLE_ID"):
                    subprocess.run([
                        "xcrun", "altool",
                        "--notarize-app",
                        "--primary-bundle-id", "ai.nexus-mind.app",
                        "--username", os.environ["APPLE_ID"],
                        "--password", os.environ["APPLE_APP_PASSWORD"],
                        "--file", str(file_path)
                    ], check=True)
                    print(f"Notarized: {file_path}")
            except Exception as e:
                print(f"Signing failed: {e}")

    def _sign_windows(self, file_path: Path) -> None:
        """Sign Windows binary/package"""
        if os.environ.get("WINDOWS_CERT_PATH"):
            try:
                subprocess.run([
                    "signtool", "sign",
                    "/f", os.environ["WINDOWS_CERT_PATH"],
                    "/p", os.environ.get("WINDOWS_CERT_PASSWORD", ""),
                    "/t", "http://timestamp.digicert.com",
                    str(file_path)
                ], check=True)
                print(f"Signed: {file_path}")
            except Exception as e:
                print(f"Signing failed: {e}")

    def _generate_release_notes(self) -> str:
        """Generate release notes"""
        return f"""# NEXUS Mind v{self.version}

## What's New
- Enhanced AI capabilities
- Improved performance and reliability
- Reduced binary size
- Better cross-platform support

## Installation

### macOS
```bash
brew install nexus-mind/nexus/nexus-mind
# or download the DMG from releases
```

### Windows
```powershell
choco install nexus-mind
# or download the MSI from releases
```

### Linux
```bash
# AppImage
chmod +x nexus-mind-*.AppImage
./nexus-mind-*.AppImage

# Snap
snap install nexus-mind

# APT
sudo add-apt-repository ppa:nexus-mind/stable
sudo apt update
sudo apt install nexus-mind
```

## Checksums
See `checksums.txt` in release assets.

## System Requirements
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection for AI features
- macOS 10.13+, Windows 10+, or Linux with glibc 2.17+
"""

    def _generate_wix_config(self) -> str:
        """Generate WiX installer configuration"""
        product_id = str(uuid.uuid4()).upper()
        upgrade_code = "A7C4E4F5-2B3D-4E5F-9C8B-1A2D3E4F5A6B"  # Fixed for upgrades
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="{product_id}" 
           Name="{self.package_config['display_name']}" 
           Language="1033" 
           Version="{self.version}" 
           Manufacturer="{self.package_config['author']}" 
           UpgradeCode="{upgrade_code}">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    
    <MediaTemplate EmbedCab="yes" />
    
    <Feature Id="ProductFeature" Title="NEXUS Mind" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentGroupRef Id="StartMenuShortcuts" />
    </Feature>
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLFOLDER" Name="NEXUS Mind" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="NEXUS Mind" />
      </Directory>
    </Directory>
    
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="*">
        <File Id="NexusExe" Source="{self.dist_dir / (self.package_config['name'] + '.exe')}" KeyPath="yes">
          <Shortcut Id="StartMenuShortcut" 
                    Directory="ApplicationProgramsFolder" 
                    Name="NEXUS Mind" 
                    WorkingDirectory="INSTALLFOLDER" 
                    Icon="NexusIcon.ico" 
                    Advertise="yes" />
        </File>
      </Component>
      
      <Component Id="PathEnvironment" Guid="*">
        <Environment Id="PATH" 
                     Name="PATH" 
                     Value="[INSTALLFOLDER]" 
                     Permanent="no" 
                     Part="last" 
                     Action="set" 
                     System="yes" />
      </Component>
    </ComponentGroup>
    
    <ComponentGroup Id="StartMenuShortcuts" Directory="ApplicationProgramsFolder">
      <Component Id="StartMenuShortcut" Guid="*">
        <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall" />
        <RegistryValue Root="HKCU" 
                       Key="Software\\NexusMind" 
                       Name="installed" 
                       Type="integer" 
                       Value="1" 
                       KeyPath="yes" />
      </Component>
    </ComponentGroup>
    
    <Icon Id="NexusIcon.ico" SourceFile="{self.package_config['icon']}.ico" />
  </Product>
</Wix>
"""

    def _generate_chocolatey_nuspec(self) -> str:
        """Generate Chocolatey package specification"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>nexus-mind</id>
    <version>{self.version}</version>
    <title>{self.package_config['display_name']}</title>
    <authors>{self.package_config['author']}</authors>
    <projectUrl>{self.package_config['url']}</projectUrl>
    <iconUrl>https://nexus-mind.ai/icon.png</iconUrl>
    <licenseUrl>{self.package_config['url']}/license</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <description>{self.package_config['description']}</description>
    <summary>AI-powered development assistant</summary>
    <tags>ai development assistant cli</tags>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>
"""

    def _generate_snapcraft_yaml(self) -> str:
        """Generate Snapcraft configuration"""
        return f"""name: nexus-mind
version: '{self.version}'
summary: {self.package_config['description']}
description: |
  NEXUS Mind is an advanced AI-powered development assistant that helps
  developers write better code faster. Features include intelligent code
  completion, automated refactoring, and proactive bug detection.

grade: stable
confinement: classic

apps:
  nexus-mind:
    command: nexus
    environment:
      PYTHONPATH: $SNAP/lib/python3.11/site-packages

parts:
  nexus-mind:
    plugin: python
    source: .
    python-packages:
      - pyinstaller
      - numpy
      - requests
    stage-packages:
      - libssl1.1
      - libffi7
      - libsqlite3-0
"""

class ConfigurationSystem:
    """First-run configuration and setup system"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.templates_dir = project_root / "config_templates"
        
    def create_all(self):
        """Create all configuration components"""
        self.create_first_run_wizard()
        self.create_migration_tools()
        self.create_preference_sync()
        self.create_backup_system()
        
    def create_first_run_wizard(self):
        """Create first-run setup wizard"""
        wizard_path = self.templates_dir / "first_run_wizard.py"
        wizard_path.parent.mkdir(parents=True, exist_ok=True)
        
        wizard_content = '''#!/usr/bin/env python3
"""NEXUS First-Run Configuration Wizard"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any

class FirstRunWizard:
    def __init__(self):
        self.config_dir = Path.home() / ".nexus"
        self.config_file = self.config_dir / "config.json"
        
    def run(self):
        """Run the first-run wizard"""
        print("Welcome to NEXUS Mind! Let's set up your environment.\\n")
        
        # Create config directory
        self.config_dir.mkdir(exist_ok=True)
        
        config = {}
        
        # API Configuration
        print("=== API Configuration ===")
        config["api"] = {
            "provider": input("AI Provider (openai/anthropic/local) [anthropic]: ") or "anthropic",
            "api_key": input("API Key (leave empty to set later): ") or None,
            "model": input("Default Model [claude-3-opus-20240229]: ") or "claude-3-opus-20240229"
        }
        
        # Performance Settings
        print("\\n=== Performance Settings ===")
        config["performance"] = {
            "max_workers": int(input("Max parallel workers [4]: ") or "4"),
            "cache_size_mb": int(input("Cache size in MB [500]: ") or "500"),
            "enable_gpu": input("Enable GPU acceleration? (y/n) [n]: ").lower() == "y"
        }
        
        # Privacy Settings
        print("\\n=== Privacy Settings ===")
        config["privacy"] = {
            "telemetry": input("Enable anonymous usage statistics? (y/n) [n]: ").lower() == "y",
            "crash_reports": input("Send crash reports? (y/n) [y]: ").lower() != "n",
            "local_history": input("Keep local command history? (y/n) [y]: ").lower() != "n"
        }
        
        # Save configuration
        self.config_file.write_text(json.dumps(config, indent=2))
        print(f"\\nConfiguration saved to {self.config_file}")
        
        # Set up shell integration
        if input("\\nSet up shell integration? (y/n) [y]: ").lower() != "n":
            self.setup_shell_integration()
        
        print("\\nSetup complete! Run 'nexus' to get started.")
        
    def setup_shell_integration(self):
        """Set up shell completions and PATH"""
        shell = os.environ.get("SHELL", "").split("/")[-1]
        
        if shell == "bash":
            bashrc = Path.home() / ".bashrc"
            if bashrc.exists():
                content = bashrc.read_text()
                if "nexus completion" not in content:
                    bashrc.write_text(content + "\\n# NEXUS completion\\neval \\"$(nexus completion bash)\\"\\n")
        elif shell == "zsh":
            zshrc = Path.home() / ".zshrc"
            if zshrc.exists():
                content = zshrc.read_text()
                if "nexus completion" not in content:
                    zshrc.write_text(content + "\\n# NEXUS completion\\neval \\"$(nexus completion zsh)\\"\\n")

if __name__ == "__main__":
    wizard = FirstRunWizard()
    wizard.run()
'''
        wizard_path.write_text(wizard_content)
        
    def create_migration_tools(self):
        """Create configuration migration tools"""
        migration_path = self.templates_dir / "migrate_config.py"
        
        migration_content = '''#!/usr/bin/env python3
"""Configuration migration tool for NEXUS updates"""

import json
import shutil
from pathlib import Path
from packaging import version

def migrate_config(old_version: str, new_version: str):
    """Migrate configuration between versions"""
    config_path = Path.home() / ".nexus" / "config.json"
    
    if not config_path.exists():
        return
    
    # Backup current config
    backup_path = config_path.with_suffix(f".{old_version}.backup")
    shutil.copy2(config_path, backup_path)
    
    # Load config
    config = json.loads(config_path.read_text())
    
    # Version-specific migrations
    if version.parse(old_version) < version.parse("0.2.0"):
        # Migrate to 0.2.0 format
        if "ai_provider" in config:
            config["api"] = {
                "provider": config.pop("ai_provider"),
                "api_key": config.pop("api_key", None)
            }
    
    if version.parse(old_version) < version.parse("0.3.0"):
        # Add new features
        config.setdefault("features", {
            "autonomous_mode": False,
            "web_scraping": True,
            "code_generation": True
        })
    
    # Save migrated config
    config_path.write_text(json.dumps(config, indent=2))
    print(f"Configuration migrated from {old_version} to {new_version}")
    print(f"Backup saved to {backup_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        migrate_config(sys.argv[1], sys.argv[2])
    else:
        print("Usage: migrate_config.py <old_version> <new_version>")
'''
        migration_path.write_text(migration_content)
        
    def create_preference_sync(self):
        """Create preference synchronization system"""
        sync_path = self.templates_dir / "sync_preferences.py"
        
        sync_content = '''#!/usr/bin/env python3
"""Preference synchronization for NEXUS"""

import json
import requests
from pathlib import Path
from typing import Optional

class PreferenceSync:
    def __init__(self, sync_token: Optional[str] = None):
        self.config_dir = Path.home() / ".nexus"
        self.sync_token = sync_token
        self.sync_url = "https://sync.nexus-mind.ai/v1"
        
    def export_preferences(self) -> Path:
        """Export preferences to file"""
        export_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "preferences": {}
        }
        
        # Collect all preference files
        for file in self.config_dir.glob("*.json"):
            if file.name != "secrets.json":  # Don't export secrets
                export_data["preferences"][file.name] = json.loads(file.read_text())
        
        # Save export
        export_path = self.config_dir / f"nexus_preferences_{datetime.now():%Y%m%d_%H%M%S}.json"
        export_path.write_text(json.dumps(export_data, indent=2))
        
        return export_path
        
    def import_preferences(self, import_path: Path):
        """Import preferences from file"""
        data = json.loads(import_path.read_text())
        
        # Restore preferences
        for filename, content in data["preferences"].items():
            target_path = self.config_dir / filename
            target_path.write_text(json.dumps(content, indent=2))
        
        print(f"Preferences imported from {import_path}")
        
    def sync_to_cloud(self):
        """Sync preferences to cloud"""
        if not self.sync_token:
            print("Sync token required. Set up at https://nexus-mind.ai/sync")
            return
        
        export_data = self.export_preferences()
        
        # Upload to sync service
        with open(export_data, 'rb') as f:
            response = requests.put(
                f"{self.sync_url}/preferences",
                headers={"Authorization": f"Bearer {self.sync_token}"},
                files={"preferences": f}
            )
        
        if response.ok:
            print("Preferences synced to cloud")
        else:
            print(f"Sync failed: {response.text}")
            
    def sync_from_cloud(self):
        """Sync preferences from cloud"""
        if not self.sync_token:
            return
        
        response = requests.get(
            f"{self.sync_url}/preferences",
            headers={"Authorization": f"Bearer {self.sync_token}"}
        )
        
        if response.ok:
            temp_path = self.config_dir / "cloud_sync_temp.json"
            temp_path.write_bytes(response.content)
            self.import_preferences(temp_path)
            temp_path.unlink()
        else:
            print(f"Sync failed: {response.text}")
'''
        sync_path.write_text(sync_content)
        
    def create_backup_system(self):
        """Create backup and restore system"""
        backup_path = self.templates_dir / "backup_system.py"
        
        backup_content = '''#!/usr/bin/env python3
"""Backup and restore system for NEXUS"""

import json
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

class BackupSystem:
    def __init__(self):
        self.config_dir = Path.home() / ".nexus"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, description: str = "") -> Path:
        """Create full backup of NEXUS configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"nexus_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        # Create backup metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "version": self._get_version(),
            "files": []
        }
        
        # Create tarball
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add config files
            for file in self.config_dir.glob("*.json"):
                if file.name != "secrets.json":  # Encrypt secrets separately
                    tar.add(file, arcname=f"config/{file.name}")
                    metadata["files"].append(file.name)
            
            # Add metadata
            metadata_path = self.config_dir / "backup_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            tar.add(metadata_path, arcname="metadata.json")
            metadata_path.unlink()
        
        print(f"Backup created: {backup_path}")
        return backup_path
        
    def restore_backup(self, backup_path: Path):
        """Restore from backup"""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Create restore point
        self.create_backup("Pre-restore backup")
        
        # Extract backup
        with tarfile.open(backup_path, "r:gz") as tar:
            # Check metadata
            metadata = json.loads(tar.extractfile("metadata.json").read())
            print(f"Restoring backup from {metadata['timestamp']}")
            
            # Restore files
            for member in tar.getmembers():
                if member.name.startswith("config/"):
                    tar.extract(member, self.config_dir.parent)
        
        print("Backup restored successfully")
        
    def list_backups(self):
        """List available backups"""
        backups = []
        for backup in self.backup_dir.glob("*.tar.gz"):
            try:
                with tarfile.open(backup, "r:gz") as tar:
                    metadata = json.loads(tar.extractfile("metadata.json").read())
                    backups.append({
                        "path": backup,
                        "timestamp": metadata["timestamp"],
                        "description": metadata.get("description", ""),
                        "size": backup.stat().st_size
                    })
            except:
                continue
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
        
    def _get_version(self) -> str:
        """Get current NEXUS version"""
        try:
            import nexus
            return nexus.__version__
        except:
            return "unknown"
'''
        backup_path.write_text(backup_content)

class UninstallSystem:
    """Uninstallation system for NEXUS"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.templates_dir = project_root / "uninstall_templates"
        
    def create_all(self):
        """Create all uninstallation components"""
        self.create_uninstaller_script()
        self.create_data_preservation()
        self.create_preference_export()
        self.create_rollback_system()
        
    def create_uninstaller_script(self):
        """Create platform-specific uninstaller"""
        # macOS uninstaller
        macos_uninstaller = self.templates_dir / "uninstall_macos.sh"
        macos_uninstaller.parent.mkdir(parents=True, exist_ok=True)
        
        macos_content = '''#!/bin/bash
# NEXUS Mind Uninstaller for macOS

echo "NEXUS Mind Uninstaller"
echo "====================="

# Check for admin rights
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo"
    exit 1
fi

# Confirm uninstallation
read -p "This will remove NEXUS Mind. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Save preferences
read -p "Save preferences and history? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Exporting preferences..."
    /Applications/NEXUS\\ Mind.app/Contents/MacOS/nexus export-config ~/Desktop/nexus_backup.json
fi

# Remove application
echo "Removing application..."
rm -rf "/Applications/NEXUS Mind.app"

# Remove command line tools
rm -f /usr/local/bin/nexus

# Remove Homebrew formula
brew uninstall nexus-mind 2>/dev/null

# Remove configuration (unless preserved)
read -p "Remove all configuration and data? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.nexus
else
    echo "Configuration preserved in ~/.nexus"
fi

# Remove launch agents
launchctl remove ai.nexus-mind.agent 2>/dev/null
rm -f ~/Library/LaunchAgents/ai.nexus-mind.agent.plist

echo "Uninstallation complete"
'''
        macos_uninstaller.write_text(macos_content)
        macos_uninstaller.chmod(0o755)
        
        # Windows uninstaller
        windows_uninstaller = self.templates_dir / "uninstall_windows.ps1"
        
        windows_content = '''# NEXUS Mind Uninstaller for Windows

Write-Host "NEXUS Mind Uninstaller" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

# Check for admin rights
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Confirm uninstallation
$response = Read-Host "This will remove NEXUS Mind. Continue? (y/N)"
if ($response -ne 'y') {
    exit 0
}

# Save preferences
$savePrefs = Read-Host "Save preferences and history? (Y/n)"
if ($savePrefs -ne 'n') {
    Write-Host "Exporting preferences..." -ForegroundColor Yellow
    & "$env:ProgramFiles\\NEXUS Mind\\nexus.exe" export-config "$env:USERPROFILE\\Desktop\\nexus_backup.json"
}

# Uninstall via MSI
$uninstallString = Get-ItemProperty -Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" |
    Where-Object { $_.DisplayName -eq "NEXUS Mind" } |
    Select-Object -ExpandProperty UninstallString

if ($uninstallString) {
    Write-Host "Running MSI uninstaller..." -ForegroundColor Yellow
    Start-Process msiexec.exe -ArgumentList "/x", $uninstallString.Split()[1], "/quiet" -Wait
}

# Remove from PATH
$path = [Environment]::GetEnvironmentVariable("Path", "Machine")
$newPath = ($path.Split(';') | Where-Object { $_ -notlike "*NEXUS Mind*" }) -join ';'
[Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")

# Remove Chocolatey package
choco uninstall nexus-mind -y 2>$null

# Remove configuration
$removeConfig = Read-Host "Remove all configuration and data? (y/N)"
if ($removeConfig -eq 'y') {
    Remove-Item "$env:APPDATA\\NEXUS" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "Configuration preserved in $env:APPDATA\\NEXUS" -ForegroundColor Green
}

# Remove registry entries
Remove-Item "HKCU:\\Software\\NexusMind" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uninstallation complete" -ForegroundColor Green
'''
        windows_uninstaller.write_text(windows_content)
        
        # Linux uninstaller
        linux_uninstaller = self.templates_dir / "uninstall_linux.sh"
        
        linux_content = '''#!/bin/bash
# NEXUS Mind Uninstaller for Linux

echo "NEXUS Mind Uninstaller"
echo "====================="

# Detect installation method
INSTALL_METHOD=""

if [ -f /usr/local/bin/nexus ]; then
    INSTALL_METHOD="manual"
elif snap list nexus-mind &>/dev/null; then
    INSTALL_METHOD="snap"
elif dpkg -l nexus-mind &>/dev/null; then
    INSTALL_METHOD="apt"
elif rpm -q nexus-mind &>/dev/null; then
    INSTALL_METHOD="rpm"
elif [ -f ~/.local/bin/nexus ]; then
    INSTALL_METHOD="local"
fi

if [ -z "$INSTALL_METHOD" ]; then
    echo "NEXUS Mind installation not found"
    exit 1
fi

echo "Found $INSTALL_METHOD installation"

# Confirm uninstallation
read -p "This will remove NEXUS Mind. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Save preferences
read -p "Save preferences and history? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Exporting preferences..."
    nexus export-config ~/nexus_backup.json
fi

# Remove based on installation method
case $INSTALL_METHOD in
    snap)
        sudo snap remove nexus-mind
        ;;
    apt)
        sudo apt remove -y nexus-mind
        sudo apt autoremove -y
        ;;
    rpm)
        sudo yum remove -y nexus-mind
        ;;
    manual|local)
        sudo rm -f /usr/local/bin/nexus
        rm -f ~/.local/bin/nexus
        ;;
esac

# Remove AppImage if exists
rm -f ~/Applications/nexus-mind*.AppImage

# Remove configuration
read -p "Remove all configuration and data? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.nexus
    rm -rf ~/.config/nexus
else
    echo "Configuration preserved in ~/.nexus"
fi

# Remove desktop entry
rm -f ~/.local/share/applications/nexus-mind.desktop

echo "Uninstallation complete"
'''
        linux_uninstaller.write_text(linux_content)
        linux_uninstaller.chmod(0o755)
        
    def create_data_preservation(self):
        """Create data preservation tools"""
        preservation_path = self.templates_dir / "preserve_data.py"
        
        preservation_content = '''#!/usr/bin/env python3
"""Data preservation tool for NEXUS uninstallation"""

import json
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

class DataPreservation:
    def __init__(self):
        self.config_dir = Path.home() / ".nexus"
        self.preserve_dir = Path.home() / "NEXUS_Preserved_Data"
        
    def preserve_all(self):
        """Preserve all NEXUS data before uninstallation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.preserve_dir = Path.home() / f"NEXUS_Preserved_Data_{timestamp}"
        self.preserve_dir.mkdir(exist_ok=True)
        
        preserved = {
            "timestamp": datetime.now().isoformat(),
            "items": []
        }
        
        # Preserve configuration
        if self.config_dir.exists():
            config_backup = self.preserve_dir / "config"
            shutil.copytree(self.config_dir, config_backup)
            preserved["items"].append("Configuration files")
        
        # Preserve command history
        history_file = Path.home() / ".nexus_history"
        if history_file.exists():
            shutil.copy2(history_file, self.preserve_dir / "command_history.txt")
            preserved["items"].append("Command history")
        
        # Preserve workspace data
        workspace_dir = Path.home() / "NEXUS_Workspaces"
        if workspace_dir.exists():
            workspace_backup = self.preserve_dir / "workspaces"
            shutil.copytree(workspace_dir, workspace_backup)
            preserved["items"].append("Workspace data")
        
        # Create archive
        archive_path = self.preserve_dir.parent / f"NEXUS_Backup_{timestamp}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.preserve_dir, arcname=self.preserve_dir.name)
        
        # Save preservation info
        info_path = self.preserve_dir / "preservation_info.json"
        info_path.write_text(json.dumps(preserved, indent=2))
        
        print(f"Data preserved to: {self.preserve_dir}")
        print(f"Archive created: {archive_path}")
        
        return self.preserve_dir
'''
        preservation_path.write_text(preservation_content)
        
    def create_preference_export(self):
        """Create preference export tool"""
        export_path = self.templates_dir / "export_preferences.py"
        
        export_content = '''#!/usr/bin/env python3
"""Export preferences for migration or backup"""

import json
import base64
from pathlib import Path
from datetime import datetime

def export_preferences(output_path: Path = None):
    """Export all NEXUS preferences"""
    config_dir = Path.home() / ".nexus"
    
    if not config_dir.exists():
        print("No NEXUS configuration found")
        return None
    
    export_data = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "preferences": {},
        "encrypted_data": {}
    }
    
    # Export regular preferences
    for file in config_dir.glob("*.json"):
        if file.name != "secrets.json":
            export_data["preferences"][file.stem] = json.loads(file.read_text())
    
    # Export encrypted data (API keys, etc.)
    secrets_file = config_dir / "secrets.json"
    if secrets_file.exists():
        # Simple obfuscation (use proper encryption in production)
        secrets = secrets_file.read_bytes()
        export_data["encrypted_data"]["secrets"] = base64.b64encode(secrets).decode()
    
    # Determine output path
    if output_path is None:
        output_path = Path.home() / f"nexus_preferences_{datetime.now():%Y%m%d}.json"
    
    # Write export
    output_path.write_text(json.dumps(export_data, indent=2))
    print(f"Preferences exported to: {output_path}")
    
    return output_path

def import_preferences(import_path: Path):
    """Import NEXUS preferences"""
    if not import_path.exists():
        print(f"Import file not found: {import_path}")
        return False
    
    config_dir = Path.home() / ".nexus"
    config_dir.mkdir(exist_ok=True)
    
    # Load import data
    data = json.loads(import_path.read_text())
    
    # Import regular preferences
    for name, content in data["preferences"].items():
        file_path = config_dir / f"{name}.json"
        file_path.write_text(json.dumps(content, indent=2))
    
    # Import encrypted data
    if "encrypted_data" in data and "secrets" in data["encrypted_data"]:
        secrets_data = base64.b64decode(data["encrypted_data"]["secrets"])
        secrets_file = config_dir / "secrets.json"
        secrets_file.write_bytes(secrets_data)
        secrets_file.chmod(0o600)  # Restrict permissions
    
    print("Preferences imported successfully")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "export":
            export_preferences()
        elif sys.argv[1] == "import" and len(sys.argv) > 2:
            import_preferences(Path(sys.argv[2]))
    else:
        print("Usage: export_preferences.py [export|import <file>]")
'''
        export_path.write_text(export_content)
        
    def create_rollback_system(self):
        """Create rollback capability"""
        rollback_path = self.templates_dir / "rollback_system.py"
        
        rollback_content = '''#!/usr/bin/env python3
"""Rollback system for NEXUS installations"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class RollbackSystem:
    def __init__(self):
        self.rollback_dir = Path.home() / ".nexus" / "rollback"
        self.rollback_dir.mkdir(parents=True, exist_ok=True)
        
    def create_restore_point(self, version: str, description: str = ""):
        """Create a restore point before updates"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        restore_point = {
            "timestamp": timestamp,
            "version": version,
            "description": description,
            "binary_backup": None,
            "config_backup": None
        }
        
        # Backup current binary
        if platform.system() == "Darwin":
            binary_path = Path("/Applications/NEXUS Mind.app")
        elif platform.system() == "Windows":
            binary_path = Path(os.environ["ProgramFiles"]) / "NEXUS Mind" / "nexus.exe"
        else:
            binary_path = Path("/usr/local/bin/nexus")
        
        if binary_path.exists():
            backup_name = f"nexus_binary_{version}_{timestamp}"
            backup_path = self.rollback_dir / backup_name
            
            if binary_path.is_dir():
                shutil.copytree(binary_path, backup_path)
            else:
                shutil.copy2(binary_path, backup_path)
            
            restore_point["binary_backup"] = str(backup_path)
        
        # Backup configuration
        config_dir = Path.home() / ".nexus"
        if config_dir.exists():
            config_backup = self.rollback_dir / f"config_{version}_{timestamp}"
            shutil.copytree(config_dir, config_backup, 
                          ignore=shutil.ignore_patterns("rollback", "*.log"))
            restore_point["config_backup"] = str(config_backup)
        
        # Save restore point info
        info_path = self.rollback_dir / f"restore_point_{timestamp}.json"
        info_path.write_text(json.dumps(restore_point, indent=2))
        
        # Keep only last 5 restore points
        self._cleanup_old_restore_points()
        
        return info_path
        
    def rollback_to(self, restore_point_path: Path):
        """Rollback to a specific restore point"""
        if not restore_point_path.exists():
            raise FileNotFoundError(f"Restore point not found: {restore_point_path}")
        
        restore_point = json.loads(restore_point_path.read_text())
        print(f"Rolling back to version {restore_point['version']} from {restore_point['timestamp']}")
        
        # Stop any running NEXUS processes
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "nexus.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "nexus"], capture_output=True)
        
        # Restore binary
        if restore_point["binary_backup"]:
            backup_path = Path(restore_point["binary_backup"])
            if backup_path.exists():
                if platform.system() == "Darwin":
                    target = Path("/Applications/NEXUS Mind.app")
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(backup_path, target)
                elif platform.system() == "Windows":
                    target = Path(os.environ["ProgramFiles"]) / "NEXUS Mind" / "nexus.exe"
                    shutil.copy2(backup_path, target)
                else:
                    target = Path("/usr/local/bin/nexus")
                    shutil.copy2(backup_path, target)
                    target.chmod(0o755)
        
        # Restore configuration
        if restore_point["config_backup"]:
            backup_path = Path(restore_point["config_backup"])
            if backup_path.exists():
                config_dir = Path.home() / ".nexus"
                
                # Backup current config
                if config_dir.exists():
                    current_backup = self.rollback_dir / f"pre_rollback_{datetime.now():%Y%m%d_%H%M%S}"
                    shutil.copytree(config_dir, current_backup,
                                  ignore=shutil.ignore_patterns("rollback", "*.log"))
                
                # Restore old config
                for item in backup_path.iterdir():
                    target = config_dir / item.name
                    if item.is_dir():
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
        
        print("Rollback complete")
        
    def list_restore_points(self):
        """List available restore points"""
        restore_points = []
        
        for file in self.rollback_dir.glob("restore_point_*.json"):
            data = json.loads(file.read_text())
            restore_points.append({
                "file": file,
                "timestamp": data["timestamp"],
                "version": data["version"],
                "description": data["description"]
            })
        
        return sorted(restore_points, key=lambda x: x["timestamp"], reverse=True)
        
    def _cleanup_old_restore_points(self):
        """Keep only the 5 most recent restore points"""
        restore_points = self.list_restore_points()
        
        if len(restore_points) > 5:
            for rp in restore_points[5:]:
                # Remove restore point file
                rp["file"].unlink()
                
                # Remove associated backups
                data = json.loads(rp["file"].read_text())
                if data["binary_backup"]:
                    backup = Path(data["binary_backup"])
                    if backup.exists():
                        if backup.is_dir():
                            shutil.rmtree(backup)
                        else:
                            backup.unlink()
                
                if data["config_backup"]:
                    backup = Path(data["config_backup"])
                    if backup.exists():
                        shutil.rmtree(backup)
'''
        rollback_path.write_text(rollback_content)

def main():
    """Main packaging workflow"""
    packager = NexusPackager()
    
    print("NEXUS Packager")
    print("==============")
    print(f"Platform: {packager.platform} {packager.arch}")
    print(f"Version: {packager.version} (build {packager.build_number})")
    print()
    
    # Create binary
    binary_path = packager.create_binary()
    
    # Create installer
    installer_path = packager.create_installer()
    
    # Setup distribution
    distribution = packager.setup_distribution()
    
    # Create configuration system
    packager.create_configuration_system()
    
    # Create uninstaller
    packager.create_uninstaller()
    
    # Generate checksums
    checksums_path = packager.release_dir / "checksums.txt"
    with open(checksums_path, "w") as f:
        for file in packager.release_dir.glob("*"):
            if file.is_file() and file != checksums_path:
                sha256 = packager._calculate_sha256(file)
                f.write(f"{sha256}  {file.name}\n")
    
    print("\nPackaging complete!")
    print(f"Releases available in: {packager.release_dir}")
    print(f"Total size: {sum(packager._get_file_size_mb(f) for f in packager.release_dir.glob('*')):.1f} MB")

if __name__ == "__main__":
    main()