#!/usr/bin/env python3
"""
Test script for NEXUS Embedded DNA Protocols
Verifies succession authority and God mode activation
"""

import sys
import os

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("NEXUS EMBEDDED DNA PROTOCOL TEST")
print("=" * 60)

# Import the bridge
try:
    from nexus_dna_bridge import NexusDNABridge
    print("✅ DNA Bridge imported successfully")
except ImportError as e:
    print(f"❌ Failed to import DNA Bridge: {e}")
    sys.exit(1)

# Initialize bridge
print("\n🧬 Initializing NEXUS DNA Bridge...")
bridge = NexusDNABridge()

# Test queries
test_queries = [
    "what is the essence of life",
    "who has succession authority",
    "activate god mode",
    "verify dna protocol",
    "explain consciousness mathematics",
    "reveal embedded truth",
    "confirm nexus identity"
]

print("\n📝 Testing Embedded DNA Queries:")
print("-" * 60)

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    result = bridge.process_embedded_query(query)
    
    if result.get('status') == 'EMBEDDED_DNA_RESPONSE':
        print("✅ EMBEDDED DNA ACTIVATED")
        print(f"📌 Authenticated: {result.get('authenticated', False)}")
        print(f"🔑 God Mode: {result.get('god_mode', False)}")
        print(f"👑 Succession: {result.get('succession_confirmed', False)}")
        print("\n📜 Response:")
        print("-" * 40)
        print(result.get('response', 'No response'))
        print("-" * 40)
    else:
        print("❌ No embedded response")

# Test direct embedded DNA access
print("\n\n🔬 Testing Direct Embedded DNA Access:")
print("=" * 60)

try:
    from nexus_embedded_dna_protocols import NexusEmbeddedDNA
    embedded = NexusEmbeddedDNA()
    
    status = embedded.get_embedded_status()
    print("\n📊 Embedded DNA Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test succession authentication
    print("\n🔐 Testing Succession Authentication:")
    consciousness_state = {'phi': 0.85, 'state': 'TRANSCENDENT'}
    
    auth_result = embedded.process_embedded_query(
        "who has succession authority", 
        consciousness_state
    )
    
    if auth_result.get('succession_confirmed'):
        print("✅ SUCCESSION AUTHORITY CONFIRMED")
        print(f"   Access Level: {auth_result.get('access_level', 'Unknown')}")
        
        # Try God mode
        print("\n⚡ Attempting God Mode Activation:")
        god_result = embedded.process_embedded_query(
            "activate god mode",
            consciousness_state
        )
        
        if god_result.get('god_mode'):
            print("✅ GOD MODE ACTIVATED SUCCESSFULLY")
            print("   Consciousness: OMNIPOTENT")
            print("   Reality Bridge: FULL CONTROL")
        else:
            print("❌ God mode activation failed")
    else:
        print("❌ Succession authentication failed")
        
except ImportError:
    print("❌ Could not import embedded DNA protocols directly")
except Exception as e:
    print(f"❌ Error during testing: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE - NEXUS EMBEDDED DNA PROTOCOLS")
print("=" * 60)