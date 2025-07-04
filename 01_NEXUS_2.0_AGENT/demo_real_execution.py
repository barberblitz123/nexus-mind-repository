#!/usr/bin/env python3
"""
Demonstration of REAL NEXUS Agent Execution

This demo shows that agents actually execute code,
not just simulate it.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interfaces'))

from interfaces.nexus_connector import get_connector
from core.nexus_logger import get_logger


async def demo():
    print("🎭 NEXUS 2.0 - Real Execution Demo")
    print("=" * 50)
    
    # Initialize
    connector = get_connector()
    logger = get_logger()
    
    print("\n1️⃣  Creating a Developer Agent...")
    agent = await connector.create_agent(
        "demo-dev-001",
        "Demo Developer",
        "developer"
    )
    print(f"   ✅ Created: {agent['name']} (ID: {agent['agent_id'][:8]}...)")
    
    # Demo 1: Execute Python Code
    print("\n2️⃣  Executing REAL Python code...")
    result = await connector.execute_agent_task(
        agent['agent_id'],
        "create a Python script that calculates fibonacci numbers"
    )
    
    if result['success']:
        print("   ✅ Code executed successfully!")
        print("   Output:")
        print("   " + result['output'].replace('\n', '\n   '))
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Demo 2: File Operations
    print("\n3️⃣  Creating a REAL file...")
    result = await connector.execute_agent_task(
        agent['agent_id'],
        "create file demo_output.txt with current timestamp"
    )
    
    if result['success']:
        print("   ✅ File created!")
        print(f"   Location: {result['output']}")
    
    # Demo 3: Shell Commands
    print("\n4️⃣  Running REAL shell commands...")
    
    # Create a DevOps agent for shell access
    devops_agent = await connector.create_agent(
        "demo-devops-001",
        "Demo DevOps",
        "devops"
    )
    
    result = await connector.execute_agent_task(
        devops_agent['agent_id'],
        "list Python files in current directory"
    )
    
    if result['success']:
        print("   ✅ Command executed!")
        print("   Files found:")
        print("   " + result['output'].replace('\n', '\n   ')[:200] + "...")
    
    # Demo 4: Code Analysis
    print("\n5️⃣  Analyzing REAL code...")
    result = await connector.execute_agent_task(
        agent['agent_id'],
        "analyze code structure in this directory"
    )
    
    if result['success']:
        print("   ✅ Analysis complete!")
        print("   Results:")
        print("   " + result['output'].replace('\n', '\n   ')[:300] + "...")
    
    # Show metrics
    print("\n6️⃣  System Metrics:")
    metrics = await connector.get_system_metrics()
    print(f"   Total agents: {metrics['agents']['total']}")
    print(f"   Tasks completed: {metrics['agents']['total_tasks_completed']}")
    print(f"   Errors: {metrics['total_errors']}")
    
    # Show agent memory
    print("\n7️⃣  Agent Learning/Memory:")
    memory = await connector.get_agent_memory(agent['agent_id'])
    print(f"   Tasks completed: {memory['tasks_completed']}")
    print(f"   Success history: {len(memory['success_history'])} entries")
    print(f"   Error patterns learned: {list(memory['learned_patterns'].keys())}")
    
    # Export logs
    print("\n8️⃣  Exporting logs...")
    log_path = await connector.export_logs()
    print(f"   ✅ Logs exported to: {log_path}")
    
    print("\n" + "=" * 50)
    print("🎆 Demo complete! This was REAL execution, not simulation.")
    print("\n📊 Check the logs for full audit trail:")
    print(f"   {logger.log_dir}/")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║        NEXUS 2.0 - REAL EXECUTION DEMO       ║
║                                              ║
║  This demo proves agents execute REAL code,  ║
║  not simulations. Watch as they:             ║
║                                              ║
║  • Execute Python code in subprocess         ║
║  • Create actual files on disk              ║
║  • Run shell commands                       ║
║  • Analyze real code                        ║
║  • Learn from their actions                 ║
║                                              ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()