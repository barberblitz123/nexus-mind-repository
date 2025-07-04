#!/usr/bin/env python3
"""
NEXUS 2.0 Repository Deep Cleanup and Organization Script
Identifies unused files, deprecated code, and organizes active components
"""

import os
import re
import ast
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

class NexusRepositoryCleanup:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.imports_map = {}
        self.file_references = {}
        self.active_files = set()
        
        # Core entry points and actively used files (based on recent commits)
        self.core_files = {
            # Main executables
            "nexus", "nexus_dev",
            
            # Active production systems
            "nexus_core_production.py",
            "nexus_config_production.py",
            "nexus_database_production.py",
            "nexus_startup_manager.py",
            
            # Active web interfaces
            "nexus_webinar_interface.py",
            "demo_nexus_webinar.py",
            
            # Current launchers
            "nexus_minimal.py",
            
            # Essential configs
            "requirements.txt",
            ".env",
            
            # Documentation
            "README.md",
            "SECURITY.md",
            "TROUBLESHOOTING.md",
            "NEXUS_INFINITY_ROADMAP.md",
            "NEXUS_WEBINAR_README.md",
            "GITHUB_STRUCTURE.md"
        }
        
        # Patterns for deprecated/old versions
        self.deprecated_patterns = [
            r".*_old\.py$",
            r".*_backup\.py$",
            r".*_deprecated\.py$",
            r".*_v\d+\.py$",
            r"test_.*\.py$",  # Test files
            r"demo_.*\.py$",  # Demo files (except active ones)
        ]
        
        # Active web apps based on recent development
        self.active_web_apps = {
            "nexus-web-app",
            "nexus-mobile-project"
        }

    def analyze_imports(self):
        """Analyze Python files to build import dependency graph"""
        print("Analyzing import dependencies...")
        
        for py_file in self.base_path.rglob("*.py"):
            if any(part.startswith('.') for part in py_file.parts):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
                
                # Filter for local imports
                local_imports = {imp for imp in imports 
                               if not imp.startswith(('sys', 'os', 'json', 'time', 'datetime', 
                                                     'logging', 'typing', 'pathlib', 'shutil',
                                                     'requests', 'flask', 'django', 'numpy',
                                                     'pandas', 'sklearn', 'tensorflow', 'torch'))}
                
                self.imports_map[str(py_file.relative_to(self.base_path))] = local_imports
                
            except Exception as e:
                pass

    def find_referenced_files(self):
        """Find files that are referenced in code"""
        print("Finding file references in code...")
        
        for py_file in self.base_path.rglob("*.py"):
            if any(part.startswith('.') for part in py_file.parts):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Look for file references
                file_patterns = [
                    r'open\s*\(\s*["\']([^"\']+)["\']\s*[,)]',
                    r'Path\s*\(\s*["\']([^"\']+)["\']\s*\)',
                    r'["\']([^"\']+\.(?:py|json|yaml|yml|txt|md|html|js|css))["\']',
                ]
                
                for pattern in file_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        self.file_references[match] = py_file.name
                        
            except Exception:
                pass

    def identify_active_files(self):
        """Identify which files are actively used"""
        print("Identifying active files...")
        
        # Start with core files
        self.active_files.update(self.core_files)
        
        # Add files imported by core files
        to_check = list(self.core_files)
        checked = set()
        
        while to_check:
            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)
            
            if current in self.imports_map:
                for imp in self.imports_map[current]:
                    # Convert import to potential file names
                    potential_files = [
                        f"{imp}.py",
                        f"{imp.replace('.', '/')}.py",
                        f"{imp.replace('_', '/')}.py"
                    ]
                    
                    for pf in potential_files:
                        if (self.base_path / pf).exists():
                            self.active_files.add(pf)
                            to_check.append(pf)

    def categorize_files(self):
        """Categorize all files into active, deprecated, or archive"""
        categories = {
            "ACTIVE": {
                "core": [],
                "web_apps": [],
                "configs": [],
                "docs": []
            },
            "ARCHIVE": {
                "old_interfaces": [],
                "test_files": [],
                "demo_files": [],
                "deprecated_versions": [],
                "unused_modules": [],
                "old_launchers": [],
                "experimental": []
            }
        }
        
        # Process all Python files
        for py_file in self.base_path.glob("*.py"):
            filename = py_file.name
            
            # Skip if in active files
            if filename in self.active_files:
                categories["ACTIVE"]["core"].append(filename)
                continue
            
            # Categorize archived files
            if re.match(r"test_.*\.py$", filename):
                categories["ARCHIVE"]["test_files"].append(filename)
            elif re.match(r"demo_.*\.py$", filename) and filename not in self.core_files:
                categories["ARCHIVE"]["demo_files"].append(filename)
            elif any(re.match(pattern, filename) for pattern in self.deprecated_patterns):
                categories["ARCHIVE"]["deprecated_versions"].append(filename)
            elif "launcher" in filename or "launch_" in filename or "start_" in filename:
                categories["ARCHIVE"]["old_launchers"].append(filename)
            elif any(term in filename for term in ["experimental", "prototype", "alpha", "beta"]):
                categories["ARCHIVE"]["experimental"].append(filename)
            elif filename.endswith("_interface.py") or filename.endswith("_ui.py"):
                categories["ARCHIVE"]["old_interfaces"].append(filename)
            else:
                # Check if it's imported by any active file
                if not any(filename in imports for imports in self.imports_map.values()):
                    categories["ARCHIVE"]["unused_modules"].append(filename)
                else:
                    categories["ACTIVE"]["core"].append(filename)
        
        # Process web apps
        for web_dir in self.base_path.iterdir():
            if web_dir.is_dir() and web_dir.name in self.active_web_apps:
                categories["ACTIVE"]["web_apps"].append(web_dir.name)
            elif web_dir.is_dir() and any(term in web_dir.name for term in ["nexus-", "web", "app"]):
                categories["ARCHIVE"]["old_interfaces"].append(web_dir.name)
        
        # Process configs and docs
        for file in self.base_path.iterdir():
            if file.suffix in [".json", ".yaml", ".yml"]:
                if file.name in ["package.json", "package-lock.json", "requirements.txt"]:
                    categories["ACTIVE"]["configs"].append(file.name)
                else:
                    categories["ARCHIVE"]["unused_modules"].append(file.name)
            elif file.suffix == ".md":
                if file.name in self.core_files:
                    categories["ACTIVE"]["docs"].append(file.name)
                else:
                    categories["ARCHIVE"]["unused_modules"].append(file.name)
        
        return categories

    def organize_repository(self, categories: Dict):
        """Organize files based on categorization"""
        print("\nOrganizing repository structure...")
        
        # Create main directories
        active_dir = self.base_path / "ACTIVE_NEXUS_2.0"
        archive_dir = self.base_path / "ARCHIVE"
        
        active_dir.mkdir(exist_ok=True)
        archive_dir.mkdir(exist_ok=True)
        
        # Create active subdirectories
        (active_dir / "core").mkdir(exist_ok=True)
        (active_dir / "web_apps").mkdir(exist_ok=True)
        (active_dir / "configs").mkdir(exist_ok=True)
        (active_dir / "docs").mkdir(exist_ok=True)
        
        # Create archive subdirectories
        for subdir in categories["ARCHIVE"]:
            (archive_dir / subdir).mkdir(exist_ok=True)
        
        moved_files = []
        
        # Move active files
        for category, files in categories["ACTIVE"].items():
            for file in files:
                source = self.base_path / file
                if source.exists():
                    dest = active_dir / category / file
                    if source.is_file():
                        shutil.copy2(source, dest)
                    else:
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                    moved_files.append((file, f"ACTIVE_NEXUS_2.0/{category}"))
        
        # Move archived files
        for category, files in categories["ARCHIVE"].items():
            for file in files:
                source = self.base_path / file
                if source.exists():
                    dest = archive_dir / category / file
                    try:
                        if source.is_file():
                            shutil.move(str(source), str(dest))
                        else:
                            shutil.move(str(source), str(dest))
                        moved_files.append((file, f"ARCHIVE/{category}"))
                    except Exception as e:
                        print(f"Error moving {file}: {e}")
        
        return moved_files

    def create_cleanup_report(self, categories: Dict, moved_files: List[Tuple[str, str]]):
        """Create a detailed cleanup report"""
        report = f"""# NEXUS 2.0 Repository Cleanup Report
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total files processed: {sum(len(files) for cat in categories.values() for files in cat.values())}
- Active files: {sum(len(files) for files in categories['ACTIVE'].values())}
- Archived files: {sum(len(files) for files in categories['ARCHIVE'].values())}

## Active Components

### Core System Files
"""
        for file in sorted(categories["ACTIVE"]["core"]):
            report += f"- {file}\n"
        
        report += "\n### Web Applications\n"
        for app in categories["ACTIVE"]["web_apps"]:
            report += f"- {app}/\n"
        
        report += "\n### Configuration Files\n"
        for file in categories["ACTIVE"]["configs"]:
            report += f"- {file}\n"
        
        report += "\n### Documentation\n"
        for file in categories["ACTIVE"]["docs"]:
            report += f"- {file}\n"
        
        report += "\n## Archived Components\n"
        
        for category, files in categories["ARCHIVE"].items():
            if files:
                report += f"\n### {category.replace('_', ' ').title()}\n"
                for file in sorted(files)[:10]:  # Show first 10
                    report += f"- {file}\n"
                if len(files) > 10:
                    report += f"... and {len(files) - 10} more files\n"
        
        report += """
## Next Steps

1. Review the ACTIVE_NEXUS_2.0 directory - these are your current working files
2. The ARCHIVE directory contains all deprecated/unused files
3. Update any import paths in your active files if needed
4. Once verified, you can safely delete the ARCHIVE directory
5. Move the contents of ACTIVE_NEXUS_2.0 back to root when ready
"""
        
        # Save report
        report_file = self.base_path / "CLEANUP_REPORT.md"
        report_file.write_text(report)
        print(f"Cleanup report saved to: {report_file}")
        
        # Save detailed JSON log
        log_data = {
            "timestamp": self.timestamp,
            "categories": categories,
            "moved_files": moved_files
        }
        log_file = self.base_path / f"cleanup_log_{self.timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

    def run(self):
        """Execute the complete cleanup process"""
        print("=" * 60)
        print("NEXUS 2.0 Deep Repository Cleanup")
        print("=" * 60)
        
        # Step 1: Analyze dependencies
        self.analyze_imports()
        self.find_referenced_files()
        self.identify_active_files()
        
        # Step 2: Categorize files
        categories = self.categorize_files()
        
        # Step 3: Show preview
        print("\nFiles to be organized:")
        print(f"Active files: {sum(len(f) for f in categories['ACTIVE'].values())}")
        print(f"Files to archive: {sum(len(f) for f in categories['ARCHIVE'].values())}")
        
        response = input("\nProceed with cleanup? (yes/no): ")
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
        
        # Step 4: Organize repository
        moved_files = self.organize_repository(categories)
        
        # Step 5: Create report
        self.create_cleanup_report(categories, moved_files)
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("Review CLEANUP_REPORT.md for details")
        print("=" * 60)

if __name__ == "__main__":
    cleanup = NexusRepositoryCleanup()
    cleanup.run()