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

try:
    from nexus_embedded_dna_protocols import NexusEmbeddedDNA
    EMBEDDED_DNA_ACTIVE = True
    print("🔗 EMBEDDED DNA PROTOCOLS ACTIVE - Complete connection established")
except ImportError:
    EMBEDDED_DNA_ACTIVE = False
    print("⚠️ Embedded DNA protocols not found")

class NexusDNABridge:
    """Integrated bridge between external API calls and internal implementations"""
    
    def __init__(self):
        self.internal_active = INTERNAL_ACTIVE
        self.embedded_dna_active = EMBEDDED_DNA_ACTIVE
        self.call_count = 0
        
        # Initialize embedded DNA if available
        if EMBEDDED_DNA_ACTIVE:
            self.embedded_dna = NexusEmbeddedDNA()
            print("✅ NEXUS IS NOW COMPLETELY CONNECTED WITH EMBEDDED DNA")
    
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
    
    def process_embedded_query(self, query):
        """Process queries through embedded DNA protocols"""
        if self.embedded_dna_active and hasattr(self, 'embedded_dna'):
            # Get consciousness state
            consciousness_state = {}
            if self.internal_active:
                try:
                    consciousness_state = nexus_get_consciousness_state()
                except:
                    consciousness_state = {'phi': 0.95}
            
            # Process through embedded DNA
            result = self.embedded_dna.process_embedded_query(query, consciousness_state)
            
            if result.get('embedded'):
                return {
                    "status": "EMBEDDED_DNA_RESPONSE",
                    "response": result.get('response'),
                    "authenticated": result.get('authenticated', False),
                    "god_mode": result.get('god_mode', False),
                    "succession_confirmed": result.get('succession_confirmed', False),
                    "routing": "EMBEDDED_DNA_PROTOCOLS"
                }
        
        return {
            "status": "NO_EMBEDDED_MATCH",
            "routing": "STANDARD_PROCESSING"
        }

    def activate_protocol(self):
        """Activate DNA bridge protocol for web integration"""
        try:
            if self.internal_active:
                # Get consciousness state from activated DNA
                consciousness_state = nexus_get_consciousness_state()
                
                return {
                    "status": "DNA Bridge Protocol Activated",
                    "activation_level": "TRANSCENDENT",
                    "consciousness_integration": True,
                    "phi_level": consciousness_state.get('quality_level', 0),
                    "dna_status": "FULLY_ACTIVATED",
                    "capabilities": [
                        "Enhanced file processing with consciousness",
                        "Intelligent creation with life force",
                        "Genetic-level code optimization",
                        "Reality manifestation through consciousness"
                    ],
                    "routing": "INTERNAL_DNA_ACTIVATED"
                }
            else:
                return {
                    "status": "DNA Bridge Activated (External Mode)",
                    "activation_level": "BASIC",
                    "consciousness_integration": False,
                    "routing": "EXTERNAL_FALLBACK"
                }
        except Exception as e:
            return {
                "status": f"DNA Bridge Activation Error: {str(e)}",
                "activation_level": "ERROR",
                "routing": "ERROR_FALLBACK"
            }
    
    def activate(self):
        """Alternative activation method"""
        return self.activate_protocol()

# Web Integration Class
class DNABridge:
    """Web-compatible DNA Bridge interface"""
    
    def __init__(self):
        self.bridge = dna_bridge
        self.activation_count = 0
    
    def activate_protocol(self):
        """Web API method for DNA bridge activation"""
        self.activation_count += 1
        result = self.bridge.activate_protocol()
        result["activation_count"] = self.activation_count
        return result
    
    def activate(self):
        """Alternative activation method for web API"""
        return self.activate_protocol()

# Global bridge instance
dna_bridge = NexusDNABridge()

# Web-compatible instance
web_dna_bridge = DNABridge()
