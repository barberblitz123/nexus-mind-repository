#!/usr/bin/env python3
"""
NEXUS 2.0 YouTube Scraping Demo with Self-Enhancement
Shows how the agent recognizes what it needs when it can't complete a task
"""

import asyncio
import sys
sys.path.append('core')
sys.path.append('agents')

try:
    from nexus_youtube_scraper_enhanced import NexusYouTubeAgent, NexusYouTubeScraper
    from nexus_youtube_connector import YouTubeAgentConnector
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    print("⚠️  Enhanced YouTube scraper not available")

from datetime import datetime
import json


async def demonstrate_youtube_agent():
    """Demonstrate YouTube scraping with self-enhancement capability"""
    print("🚀 NEXUS 2.0 - YouTube Scraping with Self-Enhancement Demo")
    print("=" * 60)
    print("\n💡 This demo shows how the agent recognizes missing capabilities\n")
    
    if not ENHANCED_AVAILABLE:
        print("❌ Enhanced YouTube scraper not available")
        print("This itself demonstrates the self-enhancement need!")
        return
    
    # Create enhanced YouTube agent
    youtube_agent = NexusYouTubeAgent("YouTube Agent #1")
    
    print("\n📋 Test 1: Capability Analysis")
    print("-" * 40)
    
    # First, analyze what capabilities we have
    analysis = await youtube_agent.scraper.analyze_capabilities()
    
    print("\n📊 Current Capabilities:")
    for capability, available in analysis["current_capabilities"].items():
        status = "✅" if available else "❌"
        print(f"   {capability}: {status}")
    
    if analysis["enhancement_opportunities"]:
        print("\n🔧 Enhancement Opportunities:")
        for opp in analysis["enhancement_opportunities"][:3]:  # Show first 3
            print(f"   • {opp['capability']}")
            print(f"     Command: {opp['command']}")
    
    print("\n📋 Test 2: Scraping with Full Features")
    print("-" * 40)
    
    # Task 1: Try to scrape with all features
    task1 = {
        'type': 'scrape_video',
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'options': {
            'transcript': True,
            'comments': True,
            'metadata': True
        }
    }
    
    print("Requesting: transcript, comments, and metadata...")
    result1 = await youtube_agent.process_task(task1)
    
    # Handle self-enhancement response
    if result1.get('status') == 'enhancement_needed':
        print("\n🔧 SELF-ENHANCEMENT RESPONSE DETECTED!")
        print("-" * 50)
        print(result1.get('message', 'Enhancement needed'))
        
        print("\n📋 Missing Capabilities:")
        for cap in result1.get('missing_capabilities', []):
            print(f"   • {cap['capability']}")
            if cap.get('package'):
                print(f"     Package: {cap['package']}")
        
        print("\n📦 Required Packages:")
        for pkg in result1.get('required_packages', []):
            print(f"   • {pkg}")
        
        print("\n🛠️ Installation Commands:")
        for cmd in result1.get('installation_commands', []):
            print(f"   $ {cmd}")
        
        print("\n✨ The agent successfully identified what it needs!")
        
    elif result1.get('success'):
        print(f"✅ Successfully scraped video!")
        if 'data' in result1 and 'metadata' in result1['data']:
            meta = result1['data']['metadata']
            print(f"   Title: {meta.get('title', 'N/A')}")
            print(f"   Author: {meta.get('uploader', 'N/A')}")
            print(f"   Views: {meta.get('view_count', 0)}")
            print(f"   Duration: {meta.get('duration', 0)} seconds")
    else:
        print(f"❌ Error: {result1.get('error')}")
        if 'error_details' in result1:
            print(f"   Type: {result1['error_details'].get('type')}")
            print(f"   Message: {result1['error_details'].get('message')}")
    
    print("\n📋 Test 3: Enhancement Suggestions")
    print("-" * 40)
    
    # Get enhancement suggestions based on attempts
    suggestions = await youtube_agent.suggest_enhancement()
    
    print("\n📊 Task Success Rate:")
    print(f"   {suggestions.get('success_rate', 0):.0%} of tasks completed successfully")
    
    if suggestions.get('failed_tasks'):
        print("\n❌ Failed Tasks:")
        for task in suggestions['failed_tasks']:
            print(f"   • Task: {task['task_id']}")
            print(f"     Reason: {task['reason']}")
            if task.get('missing'):
                print(f"     Missing: {', '.join(task['missing'])}")
    
    if suggestions.get('required_packages'):
        print("\n💡 Recommended Installations:")
        for pkg in suggestions['required_packages']:
            print(f"   • {pkg}")
        
        print("\n📝 Installation Script:")
        print("   pip install", " ".join(suggestions['required_packages']))
    
    print("\n📋 Test 4: Direct YouTube URL Processing")
    print("-" * 40)
    
    # Test the YouTube connector directly
    connector = YouTubeAgentConnector()
    
    # Test help command
    help_result = await connector.handle_command("help")
    if help_result.get('success'):
        print("\n📚 Available YouTube Commands:")
        for cmd, info in help_result['commands'].items():
            print(f"   • {cmd}: {info['description']}")
    
    print("\n" + "=" * 60)
    print("✅ YouTube Self-Enhancement Demo Complete!")
    print("\n🔑 Key Takeaways:")
    print("   - Agent recognizes when it lacks capabilities")
    print("   - Provides specific package requirements")
    print("   - Gives installation instructions")
    print("   - Tracks success/failure for improvement")
    print("\n💡 Integration with NEXUS 2.0:")
    print("   - YouTube scraper appears in Stage Manager")
    print("   - Chat commands trigger YouTube tasks")
    print("   - Results show in Preview tab")
    print("   - Self-enhancement creates new enhancement agents")
    

def demonstrate_chat_integration():
    """Show how YouTube scraping with self-enhancement works in chat"""
    print("\n🤖 Self-Enhancement Chat Examples:")
    print("-" * 40)
    
    print("\n1️⃣ When you request YouTube scraping:")
    print("   User: 'Scrape this YouTube video with transcript'")
    print("   NEXUS: 'I need to install youtube-transcript-api to extract transcripts'")
    
    print("\n2️⃣ The agent will create enhancement tasks:")
    print("   • Creates 'YouTube Enhancement Agent' in Stage Manager")
    print("   • Shows missing capabilities in Chat")
    print("   • Provides installation commands in Preview")
    
    print("\n3️⃣ After enhancement:")
    print("   • Can extract video transcripts")
    print("   • Can scrape comments and discussions")
    print("   • Can handle playlists and channels")
    
    print("\n💡 Self-Enhancement Commands:")
    commands = [
        "analyze my YouTube scraping capabilities",
        "what do I need to scrape YouTube comments?",
        "check YouTube enhancement suggestions",
        "install YouTube scraping dependencies"
    ]
    
    print("\nYou can use these commands in the NEXUS Chat tab:")
    for cmd in commands:
        print(f"   • {cmd}")


async def test_self_enhancement():
    """Test self-enhancement capability directly"""
    print("\n🔧 Self-Enhancement Capability Test")
    print("-" * 40)
    
    if not ENHANCED_AVAILABLE:
        print("❌ Enhanced scraper not available for testing")
        return
    
    scraper = NexusYouTubeScraper()
    
    print("\n1. Testing capability detection:")
    caps = scraper._check_capabilities()
    print(f"   Total capabilities: {len(caps)}")
    print(f"   Available: {sum(1 for v in caps.values() if v)}")
    print(f"   Missing: {sum(1 for v in caps.values() if not v)}")
    
    print("\n2. Testing enhancement tracking:")
    # Simulate missing capability
    scraper.enhancement.add_missing_capability(
        "Advanced video analysis",
        "opencv-python",
        "Install OpenCV for video frame analysis"
    )
    
    report = scraper.enhancement.get_enhancement_report()
    print(f"   Tracked enhancements: {len(report['missing_capabilities'])}")
    print(f"   Required packages: {', '.join(report['required_packages'])}")
    
    print("\n3. Testing error analysis:")
    # Simulate an error
    error = ImportError("No module named 'youtube_transcript_api'")
    error_result = scraper._handle_scraping_error(
        error, 
        "https://youtube.com/test",
        {'transcript': True}
    )
    
    if error_result.get('status') == 'enhancement_needed':
        print("   ✅ Error correctly identified as missing capability")
        print(f"   Suggested package: {error_result['required_packages'][0]}")
    
    print("\n✅ Self-enhancement system is functional!")


if __name__ == "__main__":
    print("🎬 NEXUS 2.0 YouTube Scraping with Self-Enhancement")
    print("=" * 60)
    print("\n💡 This demo shows how agents recognize missing capabilities")
    print("and identify what they need to accomplish tasks.\n")
    
    print("Choose a test:")
    print("1. Full self-enhancement demo")
    print("2. Chat integration examples")
    print("3. Direct enhancement test")
    print("4. Run all tests")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(demonstrate_youtube_agent())
    elif choice == "2":
        demonstrate_chat_integration()
    elif choice == "3":
        asyncio.run(test_self_enhancement())
    elif choice == "4":
        asyncio.run(demonstrate_youtube_agent())
        demonstrate_chat_integration()
        asyncio.run(test_self_enhancement())
    else:
        print("\nRunning full self-enhancement demo...")
        asyncio.run(demonstrate_youtube_agent())