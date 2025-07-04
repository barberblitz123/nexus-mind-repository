#!/usr/bin/env python3
"""
Script to help update import paths to use the new PYTHON_MODULES structure.
This script analyzes Python files and suggests import updates.
"""

import os
import re
from pathlib import Path

# Mapping of old module names to new paths
MODULE_MAPPING = {
    # Agents
    'manus_continuous_agent': 'PYTHON_MODULES.agents.manus_continuous_agent',
    'nexus_autonomous_agent': 'PYTHON_MODULES.agents.nexus_autonomous_agent',
    'nexus_agent_orchestrator_advanced': 'PYTHON_MODULES.agents.nexus_agent_orchestrator_advanced',
    
    # Memory
    'nexus_memory_core': 'PYTHON_MODULES.memory.nexus_memory_core',
    'nexus_memory_types': 'PYTHON_MODULES.memory.nexus_memory_types',
    'nexus_episodic_memory': 'PYTHON_MODULES.memory.nexus_episodic_memory',
    'nexus_semantic_memory': 'PYTHON_MODULES.memory.nexus_semantic_memory',
    'nexus_working_memory': 'PYTHON_MODULES.memory.nexus_working_memory',
    'nexus_mem0_core': 'PYTHON_MODULES.memory.nexus_mem0_core',
    
    # Scrapers
    'nexus_web_scraper': 'PYTHON_MODULES.scrapers.nexus_web_scraper',
    'nexus_scraper_proxies': 'PYTHON_MODULES.scrapers.nexus_scraper_proxies',
    'nexus_scraper_stealth': 'PYTHON_MODULES.scrapers.nexus_scraper_stealth',
    
    # Core Systems
    'nexus_core_production': 'PYTHON_MODULES.core_systems.nexus_core_production',
    'nexus_config_production': 'PYTHON_MODULES.core_systems.nexus_config_production',
    'nexus_database_production': 'PYTHON_MODULES.core_systems.nexus_database_production',
    'nexus_startup_manager': 'PYTHON_MODULES.core_systems.nexus_startup_manager',
    'nexus_omnipotent_core': 'PYTHON_MODULES.core_systems.nexus_omnipotent_core',
    
    # Interfaces
    'nexus_webinar_interface': 'PYTHON_MODULES.interfaces.nexus_webinar_interface',
    'manus_web_interface': 'PYTHON_MODULES.interfaces.manus_web_interface',
    'manus_web_interface_v2': 'PYTHON_MODULES.interfaces.manus_web_interface_v2',
    
    # Integrations
    'nexus_integration_core': 'PYTHON_MODULES.integrations.nexus_integration_core',
    'manus_nexus_integration': 'PYTHON_MODULES.integrations.manus_nexus_integration',
    'nexus_enhanced_manus': 'PYTHON_MODULES.integrations.nexus_enhanced_manus',
    
    # Utilities
    'nexus_unified_tools': 'PYTHON_MODULES.utilities.nexus_unified_tools',
    'nexus_doc_generator': 'PYTHON_MODULES.utilities.nexus_doc_generator',
    'nexus_bug_detector': 'PYTHON_MODULES.utilities.nexus_bug_detector',
    'nexus_performance_analyzer': 'PYTHON_MODULES.utilities.nexus_performance_analyzer',
    'nexus_security_scanner': 'PYTHON_MODULES.utilities.nexus_security_scanner',
    'nexus_project_generator': 'PYTHON_MODULES.utilities.nexus_project_generator',
    
    # Processors
    'nexus_vision_processor': 'PYTHON_MODULES.processors.nexus_vision_processor',
    'nexus_voice_control': 'PYTHON_MODULES.processors.nexus_voice_control',
    
    # Launchers
    'nexus_minimal': 'PYTHON_MODULES.launchers.nexus_minimal',
}

def find_imports(file_path):
    """Find all import statements in a Python file."""
    imports_to_update = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find import statements
    import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
    
    for line_num, line in enumerate(content.split('\n'), 1):
        line = line.strip()
        match = re.match(import_pattern, line)
        
        if match:
            from_module = match.group(1)
            import_names = match.group(2)
            
            # Check if this import needs updating
            if from_module:
                for old_module, new_module in MODULE_MAPPING.items():
                    if old_module in from_module:
                        imports_to_update.append({
                            'line_num': line_num,
                            'old_line': line,
                            'suggestion': line.replace(from_module, new_module)
                        })
            else:
                # Handle direct imports
                for old_module, new_module in MODULE_MAPPING.items():
                    if old_module in import_names:
                        new_line = f"from {new_module} import *"  # or specific imports
                        imports_to_update.append({
                            'line_num': line_num,
                            'old_line': line,
                            'suggestion': new_line
                        })
    
    return imports_to_update

def analyze_directory(directory):
    """Analyze all Python files in a directory for import updates."""
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip the PYTHON_MODULES directory itself
        if 'PYTHON_MODULES' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = find_imports(file_path)
                
                if imports:
                    results[file_path] = imports
    
    return results

def print_report(results):
    """Print a report of suggested import updates."""
    if not results:
        print("No import updates needed!")
        return
    
    print("Import Update Report")
    print("=" * 80)
    
    for file_path, imports in results.items():
        print(f"\nFile: {file_path}")
        print("-" * 40)
        
        for imp in imports:
            print(f"  Line {imp['line_num']}:")
            print(f"    Old: {imp['old_line']}")
            print(f"    New: {imp['suggestion']}")
    
    print(f"\n\nTotal files needing updates: {len(results)}")
    total_imports = sum(len(imports) for imports in results.values())
    print(f"Total imports to update: {total_imports}")

if __name__ == "__main__":
    # Analyze the repository
    repo_root = "/workspaces/nexus-mind-repository"
    
    print("Analyzing Python files for import updates...")
    results = analyze_directory(repo_root)
    
    print_report(results)
    
    # Optionally save the report
    save_report = input("\nSave detailed report to file? (y/n): ")
    if save_report.lower() == 'y':
        report_path = os.path.join(repo_root, "PYTHON_MODULES", "import_update_report.txt")
        with open(report_path, 'w') as f:
            for file_path, imports in results.items():
                f.write(f"\nFile: {file_path}\n")
                f.write("-" * 40 + "\n")
                for imp in imports:
                    f.write(f"  Line {imp['line_num']}:\n")
                    f.write(f"    Old: {imp['old_line']}\n")
                    f.write(f"    New: {imp['suggestion']}\n")
        print(f"Report saved to: {report_path}")