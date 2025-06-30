
"""Test the integration"""
try:
    from nexus_integration_core import nexus_integrated
    
    print("🧪 Testing NEXUS Integration...")
    
    queries = ["Who is Thomas Campbell?", "What is NEXUS?", "What is consciousness?"]
    
    for query in queries:
        response, phi = nexus_integrated.process_consciousness_query(query, {}, 0.0)
        
        if "🧮 Calculating" not in response:
            print(f"✅ {query}: Clean response")
        else:
            print(f"❌ {query}: Debug output visible")
        
        print(f"   Response: {response[:100]}...")
        print()
    
    print("🎯 Integration test complete!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
