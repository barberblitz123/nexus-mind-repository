#\!/usr/bin/env python3
"""
Fix import errors in NEXUS Enhanced files
"""

import os
import re

# Files to fix
files_to_fix = [
    "nexus_bug_detector.py",
    "nexus_security_scanner.py",
    "nexus_performance_analyzer.py",
    "nexus_project_generator.py"
]

# Replacements to make
replacements = [
    ("from nexus_memory_core import UnifiedMemoryCore", "from nexus_memory_core import NexusUnifiedMemory"),
    ("from nexus_memory_types import MemoryType", "from nexus_memory_types import MemoryEntry"),
    ("UnifiedMemoryCore()", "NexusUnifiedMemory()"),
    ("MemoryType.SEMANTIC", '"semantic"'),
    ("MemoryType.EPISODIC", '"episodic"'),
    ("memory_type=", "stage=")
]

for filename in files_to_fix:
    if os.path.exists(filename):
        print(f"Fixing {filename}...")
        
        with open(filename, 'r') as f:
            content = f.read()
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        with open(filename, 'w') as f:
            f.write(content)
        
        print(f"✓ Fixed {filename}")

print("\nAll files fixed\!")
EOF < /dev/null
