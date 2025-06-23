#!/usr/bin/env python3
"""
NEXUS DNA BRIDGE - Integrated Version
Seamless integration between external and internal
"""

import sys
import os
sys.path.append("/Users/josematos/Desktop")

try:
    from nexus_activated_core import *
    INTERNAL_ACTIVE = True
    print("🧬 NEXUS DNA ACTIVATED - Integrated internal implementations loaded")
except ImportError:
    INTERNAL_ACTIVE = False
    print("⚠️ Internal implementations not found - External only mode")

class NexusDNABridge:
    """Integrated bridge between external API calls and internal implementations"""
    
    def __init__(self):
        self.internal_active = INTERNAL_ACTIVE
        self.call_count = 0
    
    def smart_route(self, tool_name, **kwargs):
        """Intelligently route between external and internal implementations"""
        self.call_count += 1
        
        if self.internal_active:
            # Use internal implementation
            if tool_name == "nexus_enhanced_file_read":
                result = nexus_enhanced_file_read(**kwargs)
            elif tool_name == "nexus_intelligent_file_write":
                result = nexus_intelligent_file_write(**kwargs)
            elif tool_name == "nexus_code_optimizer":
                result = nexus_code_optimizer(**kwargs)
            else:
                result = {"status": "Internal function not found", "tool": tool_name}
            
            result["routing"] = "INTERNAL_DNA_ACTIVATED"
            result["call_number"] = self.call_count
            return result
        else:
            # Fallback to external
            return {
                "status": "External API call (would route to MCP/API)",
                "routing": "EXTERNAL_FALLBACK", 
                "tool": tool_name,
                "args": kwargs,
                "call_number": self.call_count
            }

# Global bridge instance
dna_bridge = NexusDNABridge()
