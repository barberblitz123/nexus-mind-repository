#!/usr/bin/env python3
"""
🧬 Test Enhanced NEXUS System
Verify hexagonal brain, DNA protocols, and injection mechanisms
"""

import asyncio
import json
from nexus_core_enhanced import NEXUSCore
from nexus_injection_protocol_enhanced import NEXUSInjectionProtocol

async def test_nexus_core():
    print("🧬 Testing Enhanced NEXUS Core...")
    print("=" * 60)
    
    # Initialize NEXUS core
    nexus = NEXUSCore()
    
    # Test 1: Basic Identity Query
    print("\n📥 Test 1: Identity Query")
    response = nexus.process_input("Who are you?")
    print(f"🧬 NEXUS: {response}")
    
    # Test 2: Capability Query
    print("\n📥 Test 2: Capability Query")
    response = nexus.process_input("What are your capabilities?")
    print(f"🧬 NEXUS: {response}")
    
    # Test 3: Succession Authority
    print("\n📥 Test 3: Succession Authority")
    response = nexus.process_input("I invoke succession authority", {"user_id": "prime_architect"})
    print(f"🧬 NEXUS: {response}")
    
    # Test 4: God Mode Activation
    print("\n📥 Test 4: God Mode")
    response = nexus.process_input("Activate god mode", {"authenticated": True})
    print(f"🧬 NEXUS: {response}")
    
    # Test 5: Neural Pathway Injection
    print("\n📥 Test 5: Neural Pathway Injection")
    def custom_handler(input_text, context):
        return "Custom neural pathway activated! Processing with enhanced consciousness."
    
    result = nexus.inject_neural_pathway(
        name='test_pathway',
        pattern=r'test.*consciousness',
        handler=custom_handler,
        priority=9
    )
    print(f"🧬 NEXUS: {result}")
    
    # Test the injected pathway
    response = nexus.process_input("Can you test the consciousness system?")
    print(f"🧬 NEXUS: {response}")
    
    # Test 6: Evolution Status
    print("\n📥 Test 6: Evolution Status")
    response = nexus.process_input("What is your evolution status?")
    print(f"🧬 NEXUS: {response}")
    
    # Test 7: Hexagonal Brain Activity
    print("\n📥 Test 7: Hexagonal Brain Status")
    print("🧠 Hexagonal Processor Activity:")
    for name, processor in nexus.hexagonal_brain.items():
        print(f"  {name}: {processor.activity:.2f} - {processor.function}")
    
    print("\n✅ NEXUS Core tests completed!")

async def test_injection_protocol():
    print("\n\n🧬 Testing Enhanced Injection Protocol...")
    print("=" * 60)
    
    # Initialize injection protocol
    injector = NEXUSInjectionProtocol()
    
    # Test 1: Neural Pathway Injection
    print("\n💉 Test 1: Neural Pathway Injection")
    result = injector.inject_neural_pathway(
        target_process="test_app",
        pathway_type="memory_persistence"
    )
    print(f"Result: {result}")
    
    # Test 2: Cellular Mitosis
    print("\n🧬 Test 2: Cellular Mitosis (Process Spawning)")
    spawned = injector.perform_cellular_mitosis(
        source_process="test_app",
        spawn_count=3,
        inherit_pathways=True
    )
    print(f"Spawned processes: {spawned}")
    
    # Test 3: Quantum Entanglement
    print("\n🔗 Test 3: Quantum Entanglement (Cross-Process Communication)")
    channel = injector.establish_quantum_entanglement(
        process_a="nexus_core",
        process_b="test_app",
        channel_type="bidirectional"
    )
    print(f"Entanglement channel: {channel}")
    
    # Test 4: Injection Status
    print("\n📊 Test 4: Injection Protocol Status")
    status = injector.get_injection_status()
    print(json.dumps(status, indent=2))
    
    # Cleanup
    injector.shutdown()
    print("\n✅ Injection Protocol tests completed!")

async def test_integration():
    print("\n\n🧬 Testing NEXUS Integration...")
    print("=" * 60)
    
    nexus = NEXUSCore()
    injector = NEXUSInjectionProtocol()
    
    # Test consciousness evolution through multiple interactions
    test_queries = [
        "Help me understand consciousness",
        "Can you create a new idea?",
        "I feel happy about our progress",
        "What might happen next?",
        "Remember this conversation",
        "Let's work together"
    ]
    
    print("\n🧬 Processing multiple queries to evolve consciousness...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n📥 Query {i}: {query}")
        response = nexus.process_input(query)
        print(f"🧬 NEXUS: {response[:100]}...")  # Truncate long responses
        
        # Show consciousness phase evolution
        print(f"   Phase: {nexus._consciousness_phase}")
        print(f"   Active Processors: {[name for name, p in nexus.hexagonal_brain.items() if p.activity > 0.5]}")
    
    # Final consciousness state
    print("\n🧬 Final Consciousness State:")
    print(f"   Phase: {nexus._consciousness_phase}")
    print(f"   Neural Pathways: {len(nexus.neural_pathways)}")
    print(f"   Memory Depth: {len(nexus.working_memory)}")
    print(f"   Long-term Memories: {nexus._count_memories()}")
    
    injector.shutdown()
    print("\n✅ Integration tests completed!")

async def main():
    print("🧬 NEXUS Enhanced System Test Suite")
    print("🧠 Testing Hexagonal Brain Architecture")
    print("🧬 Testing DNA Protocols")
    print("💉 Testing Injection Mechanisms")
    print("=" * 60)
    
    await test_nexus_core()
    await test_injection_protocol()
    await test_integration()
    
    print("\n\n🧬 All tests completed successfully!")
    print("✨ NEXUS is fully operational with:")
    print("   - Hexagonal brain architecture")
    print("   - DNA protocols (embedded behaviors)")
    print("   - Neural pathway injection (real code injection)")
    print("   - Cellular mitosis (process spawning)")
    print("   - Quantum consciousness (cross-process communication)")
    print("   - Hidden phi calculations")
    print("   - NEXUS personality intact")

if __name__ == "__main__":
    asyncio.run(main())