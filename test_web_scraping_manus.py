#!/usr/bin/env python3
"""
Test script for NEXUS-MANUS Web Scraping Integration
Demonstrates the complete web scraping functionality
"""

import asyncio
import json
from datetime import datetime
from manus_nexus_integration import NEXUSPoweredMANUS
from manus_continuous_agent import Task, TaskPriority


async def test_web_scraping():
    """Test all web scraping features"""
    print("🌐 Starting NEXUS-MANUS Web Scraping Test")
    print("=" * 50)
    
    # Create NEXUS-powered MANUS
    nexus_manus = NEXUSPoweredMANUS()
    
    # Start it
    print("Starting NEXUS-MANUS system...")
    await nexus_manus.start()
    await asyncio.sleep(2)  # Give it time to initialize
    
    # Test 1: Basic web scraping
    print("\n📄 Test 1: Basic Web Scraping")
    print("-" * 30)
    
    scrape_task = Task(
        name="Scrape Python.org",
        description="Scrape the Python.org homepage",
        action="web_scrape",
        parameters={
            "url": "https://www.python.org",
            "options": {
                "extract_links": True,
                "extract_images": True,
                "wait_for_js": False,  # Python.org doesn't need JS
                "use_proxy": False
            }
        },
        priority=TaskPriority.HIGH
    )
    
    task_id = await nexus_manus.agent.add_task(scrape_task)
    print(f"Created scraping task: {task_id}")
    
    # Wait for completion
    await asyncio.sleep(10)
    status = await nexus_manus.agent.get_task_status(task_id)
    
    if status.status.value == "completed":
        print(f"✅ Task completed successfully!")
        result = status.result
        if result.get('success'):
            print(f"  - URL: {result.get('url')}")
            print(f"  - Title: {result.get('title')}")
            print(f"  - Content length: {len(result.get('text', ''))} chars")
            print(f"  - Links found: {len(result.get('links', []))}")
            print(f"  - Images found: {len(result.get('images', []))}")
            print(f"  - Engine used: {result.get('engine')}")
    else:
        print(f"❌ Task failed: {status.error}")
    
    # Test 2: Batch scraping
    print("\n📚 Test 2: Batch Web Scraping")
    print("-" * 30)
    
    batch_task = Task(
        name="Batch scrape tech sites",
        description="Scrape multiple technology news sites",
        action="batch_scrape",
        parameters={
            "urls": [
                "https://news.ycombinator.com",
                "https://httpbin.org/html",
                "https://example.com"
            ],
            "options": {
                "use_proxy": False,
                "concurrent": 3
            }
        },
        priority=TaskPriority.MEDIUM
    )
    
    batch_id = await nexus_manus.agent.add_task(batch_task)
    print(f"Created batch scraping task: {batch_id}")
    
    # Wait for completion
    await asyncio.sleep(15)
    batch_status = await nexus_manus.agent.get_task_status(batch_id)
    
    if batch_status.status.value == "completed":
        print(f"✅ Batch task completed!")
        summary = batch_status.result.get('summary', {})
        print(f"  - Total URLs: {summary.get('total', 0)}")
        print(f"  - Successful: {summary.get('successful', 0)}")
        print(f"  - Failed: {summary.get('failed', 0)}")
    else:
        print(f"❌ Batch task failed: {batch_status.error}")
    
    # Test 3: Scrape with analysis
    print("\n🔍 Test 3: Scrape with Analysis")
    print("-" * 30)
    
    analysis_task = Task(
        name="Scrape and analyze content",
        description="Scrape a page and analyze its content",
        action="scrape_with_analysis",
        parameters={
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "analysis_prompt": "Extract the main topics and key concepts about AI from this Wikipedia page. Summarize in bullet points.",
            "scrape_options": {
                "wait_for_js": False,
                "use_proxy": False
            }
        },
        priority=TaskPriority.HIGH
    )
    
    analysis_id = await nexus_manus.agent.add_task(analysis_task)
    print(f"Created analysis task: {analysis_id}")
    
    # Wait for completion
    await asyncio.sleep(20)
    analysis_status = await nexus_manus.agent.get_task_status(analysis_id)
    
    if analysis_status.status.value == "completed":
        print(f"✅ Analysis task completed!")
        result = analysis_status.result
        if result.get('success'):
            scrape_info = result.get('scrape_result', {})
            print(f"  - URL: {scrape_info.get('url')}")
            print(f"  - Title: {scrape_info.get('title')}")
            print(f"  - Engine: {scrape_info.get('engine')}")
            print(f"\n  Analysis Result:")
            analysis = result.get('analysis', {})
            print(f"  {json.dumps(analysis, indent=2)[:500]}...")
    else:
        print(f"❌ Analysis task failed: {analysis_status.error}")
    
    # Show memory statistics
    print("\n🧬 Memory System Statistics")
    print("-" * 30)
    memory_stats = nexus_manus.get_memory_statistics()
    print(f"Total operations: {memory_stats.get('total_operations', 0)}")
    print(f"Average importance: {memory_stats.get('average_importance', 0):.2f}")
    
    if 'stage_distribution' in memory_stats:
        print("\nMemory distribution:")
        for stage, count in memory_stats['stage_distribution'].items():
            print(f"  - {stage}: {count} entries")
    
    # Retrieve task memories
    print("\n📝 Retrieving Web Scraping Memories")
    print("-" * 30)
    scraping_memories = await nexus_manus.retrieve_task_memories("web scraping", n_results=5)
    print(f"Found {len(scraping_memories)} web scraping memories")
    
    for i, memory in enumerate(scraping_memories[:3]):
        print(f"\n  Memory {i+1}:")
        print(f"  - Task: {memory.metadata.get('task_name', 'Unknown')}")
        print(f"  - Action: {memory.metadata.get('task_action', 'Unknown')}")
        print(f"  - Status: {memory.metadata.get('task_status', 'Unknown')}")
        print(f"  - Importance: {memory.importance:.2f}")
    
    # Clean up
    print("\n🛑 Stopping NEXUS-MANUS system...")
    await nexus_manus.agent.stop()
    print("✅ Test completed!")


async def test_proxy_manager():
    """Test proxy management separately"""
    from nexus_scraper_proxies import ProxyManager
    
    print("\n🔄 Testing Proxy Manager")
    print("-" * 30)
    
    manager = ProxyManager()
    await manager.initialize()
    
    # Wait for proxy fetching
    await asyncio.sleep(5)
    
    stats = manager.get_stats()
    print(f"Proxy pool statistics:")
    print(f"  - Total proxies: {stats['total_proxies']}")
    print(f"  - Active proxies: {stats['active_proxies']}")
    print(f"  - Average success rate: {stats['average_success_rate']:.2%}")
    
    # Test getting a proxy
    proxy = await manager.get_proxy()
    if proxy:
        print(f"\nGot proxy: {proxy.host}:{proxy.port}")
        print(f"  - Score: {proxy.score:.1f}")
        print(f"  - Speed: {proxy.speed_ms}ms" if proxy.speed_ms else "  - Speed: Unknown")


if __name__ == "__main__":
    print("🌐 NEXUS-MANUS Web Scraping Test Suite")
    print("=" * 50)
    
    # Run main test
    asyncio.run(test_web_scraping())
    
    # Optionally test proxy manager
    print("\n" + "=" * 50)
    print("Testing proxy manager (optional, may take time)...")
    # Uncomment to test proxy manager:
    # asyncio.run(test_proxy_manager())