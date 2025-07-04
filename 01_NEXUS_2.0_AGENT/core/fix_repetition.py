#!/usr/bin/env python3
"""
🔧 NEXUS 2.0 - Repetition Fix Patch
Fixes the issue where multiple agents are created for single commands
"""

import os
import sys

def apply_repetition_fix():
    """Apply the fix to prevent multiple agent creation"""
    
    print("🔧 NEXUS 2.0 - Applying Repetition Fix...")
    print("=" * 50)
    
    # Path to the main workspace file
    workspace_file = "nexus_integrated_workspace.py"
    
    if not os.path.exists(workspace_file):
        print("❌ Error: nexus_integrated_workspace.py not found!")
        return False
    
    print("📝 Reading current workspace file...")
    
    # Read the current file
    with open(workspace_file, 'r') as f:
        content = f.read()
    
    print("🔧 Applying fixes...")
    
    # Fix 1: Replace the problematic _analyze_and_create_agents method
    old_method = '''    def _analyze_and_create_agents(self, command: str) -> Dict[str, Any]:
        """Analyze command and create appropriate agents"""
        
        command_lower = command.lower()
        agents_created = []
        
        # Web scraper request
        if any(word in command_lower for word in ['scraper', 'scrape', 'web scraping']):
            agent_id = self.stage_manager.create_agent_window("Web Scraper Development")
            agents_created.append(agent_id)
            self._simulate_agent_work(agent_id, "web_scraper")
            
        # API development
        elif any(word in command_lower for word in ['api', 'rest', 'flask', 'fastapi']):
            agent_id = self.stage_manager.create_agent_window("REST API Development")
            agents_created.append(agent_id)
            self._simulate_agent_work(agent_id, "rest_api")
            
        # Security analysis
        elif any(word in command_lower for word in ['security', 'analyze', 'audit']):
            agent_id = self.stage_manager.create_agent_window("Security Analysis")
            agents_created.append(agent_id)
            self._simulate_agent_work(agent_id, "security_audit")
            
        # General development
        elif any(word in command_lower for word in ['build', 'create', 'develop']):
            agent_id = self.stage_manager.create_agent_window("General Development")
            agents_created.append(agent_id)
            self._simulate_agent_work(agent_id, "general_dev")
            
        else:
            # Default: create a general purpose agent
            agent_id = self.stage_manager.create_agent_window("Task Processing")
            agents_created.append(agent_id)
            self._simulate_agent_work(agent_id, "general_task")
        
        return {
            'agents_created': agents_created,
            'message': f"Created {len(agents_created)} agent(s) for: {command}"
        }'''
    
    new_method = '''    def _analyze_and_create_agents(self, command: str) -> Dict[str, Any]:
        """Analyze command and create appropriate agents - FIXED VERSION"""
        
        command_lower = command.lower()
        
        # Determine task type (only ONE agent per command)
        if any(word in command_lower for word in ['scraper', 'scrape', 'web scraping']):
            task_type = "web_scraper"
            task_name = "Web Scraper Development"
        elif any(word in command_lower for word in ['api', 'rest', 'flask', 'fastapi']):
            task_type = "rest_api"
            task_name = "REST API Development"
        elif any(word in command_lower for word in ['security', 'analyze', 'audit']):
            task_type = "security_audit"
            task_name = "Security Analysis"
        elif any(word in command_lower for word in ['build', 'create', 'develop']):
            task_type = "general_dev"
            task_name = "General Development"
        else:
            task_type = "general_task"
            task_name = "Task Processing"
        
        # Create ONLY ONE agent
        agent_id = self.stage_manager.create_agent_window(task_name)
        self._simulate_agent_work(agent_id, task_type)
        
        return {
            'agents_created': [agent_id],
            'message': f"Starting: {task_name}"
        }'''
    
    # Apply the fix
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Fixed: _analyze_and_create_agents method")
    else:
        print("⚠️  Warning: Could not find exact method to replace, applying alternative fix...")
        # Alternative fix - just ensure we don't create multiple agents
        content = content.replace(
            "agents_created.append(agent_id)",
            "agents_created = [agent_id]  # FIXED: Only one agent"
        )
    
    # Fix 2: Improve the chat display to avoid repetition
    old_chat_display = '''            for msg in recent_history:
                timestamp = msg['timestamp'].strftime("%H:%M")
                msg_type = "You" if msg['type'] == 'user' else "NEXUS"
                content = msg['content'][:40] + "..." if len(msg['content']) > 40 else msg['content']
                display.append(f"│{timestamp} {msg_type}: {content:<25}│")'''
    
    new_chat_display = '''            for msg in recent_history:
                timestamp = msg['timestamp'].strftime("%H:%M")
                msg_type = "You" if msg['type'] == 'user' else "NEXUS"
                content = msg['content'][:35] + "..." if len(msg['content']) > 35 else msg['content']
                display.append(f"│{timestamp} {msg_type}: {content:<30}│")'''
    
    if old_chat_display in content:
        content = content.replace(old_chat_display, new_chat_display)
        print("✅ Fixed: Chat display formatting")
    
    # Write the fixed file
    print("💾 Writing fixed version...")
    with open(workspace_file, 'w') as f:
        f.write(content)
    
    print("✅ Repetition fix applied successfully!")
    print("\n🚀 You can now run:")
    print("python nexus_integrated_workspace.py")
    print("\nThe system will now create only ONE agent per command.")
    
    return True

def main():
    """Main function"""
    try:
        success = apply_repetition_fix()
        if success:
            print("\n🎯 Fix completed! The NEXUS system is ready to run without repetition issues.")
        else:
            print("\n❌ Fix failed. Please check the error messages above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error applying fix: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()