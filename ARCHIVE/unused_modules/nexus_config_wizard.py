#!/usr/bin/env python3
"""
NEXUS Configuration Wizard
Interactive setup wizard for first-time configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from rich.markdown import Markdown
import requests
import platform

console = Console()

class ConfigWizard:
    """Configuration wizard for NEXUS"""
    
    def __init__(self):
        self.config = {
            'first_run': False,
            'profile': {},
            'api_keys': {},
            'services': {},
            'features': {},
            'preferences': {}
        }
        self.home_dir = Path.home() / '.nexus'
        
    def run(self) -> Dict:
        """Run the configuration wizard"""
        # Welcome screen
        self.show_welcome()
        
        # Profile setup
        self.setup_profile()
        
        # API keys configuration
        self.setup_api_keys()
        
        # Service configuration
        self.setup_services()
        
        # Feature selection
        self.setup_features()
        
        # Preferences
        self.setup_preferences()
        
        # Tutorial option
        if Confirm.ask("\nWould you like to see a quick tutorial?"):
            self.show_tutorial()
        
        # Summary
        self.show_summary()
        
        return self.config
    
    def show_welcome(self):
        """Show welcome screen"""
        console.clear()
        
        welcome_text = """
# Welcome to NEXUS! 🚀

I'm here to help you set up your AI development environment.
This wizard will guide you through:

- Creating your developer profile
- Configuring API keys (optional)
- Setting up services
- Choosing features to enable
- Personalizing your experience

Let's get started!
        """
        
        console.print(Panel(Markdown(welcome_text), title="NEXUS Setup Wizard", border_style="cyan"))
        console.print()
        
        if not Confirm.ask("Ready to begin?", default=True):
            console.print("[yellow]Setup cancelled. You can run this wizard anytime with: nexus config[/yellow]")
            sys.exit(0)
    
    def setup_profile(self):
        """Setup user profile"""
        console.print("\n[bold cyan]Developer Profile[/bold cyan]")
        console.print("Let's create your developer profile.\n")
        
        # Name
        name = Prompt.ask("What should I call you?", default=os.environ.get('USER', 'Developer'))
        
        # Experience level
        console.print("\nWhat's your experience level?")
        console.print("1. Beginner - New to development")
        console.print("2. Intermediate - Some experience")
        console.print("3. Advanced - Experienced developer")
        console.print("4. Expert - Senior/Lead developer")
        
        level = Prompt.ask("Select level", choices=['1', '2', '3', '4'], default='2')
        level_map = {
            '1': 'beginner',
            '2': 'intermediate',
            '3': 'advanced',
            '4': 'expert'
        }
        
        # Primary language
        console.print("\nWhat's your primary programming language?")
        languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'Other']
        for i, lang in enumerate(languages, 1):
            console.print(f"{i}. {lang}")
        
        lang_choice = Prompt.ask("Select language", choices=[str(i) for i in range(1, len(languages) + 1)], default='1')
        primary_language = languages[int(lang_choice) - 1]
        
        if primary_language == 'Other':
            primary_language = Prompt.ask("Enter your primary language")
        
        # Development focus
        console.print("\nWhat type of development do you focus on?")
        focus_areas = ['Web Development', 'Mobile Apps', 'Backend/APIs', 'Data Science/ML', 'DevOps', 'Full Stack', 'Other']
        for i, area in enumerate(focus_areas, 1):
            console.print(f"{i}. {area}")
        
        focus_choice = Prompt.ask("Select focus", choices=[str(i) for i in range(1, len(focus_areas) + 1)], default='6')
        focus = focus_areas[int(focus_choice) - 1]
        
        self.config['profile'] = {
            'name': name,
            'experience_level': level_map[level],
            'primary_language': primary_language,
            'focus_area': focus,
            'created_at': str(Path.ctime(Path.home()))
        }
        
        console.print(f"\n[green]✓ Profile created for {name}![/green]")
    
    def setup_api_keys(self):
        """Setup API keys"""
        console.print("\n[bold cyan]API Configuration[/bold cyan]")
        console.print("NEXUS can integrate with various AI services. API keys are optional but enable advanced features.\n")
        
        # Check for existing keys in environment
        env_keys = {
            'ANTHROPIC_API_KEY': 'Anthropic (Claude)',
            'OPENAI_API_KEY': 'OpenAI (GPT)',
            'GOOGLE_API_KEY': 'Google (Gemini)',
            'HUGGINGFACE_TOKEN': 'HuggingFace'
        }
        
        found_keys = {}
        for env_var, service in env_keys.items():
            if os.environ.get(env_var):
                found_keys[env_var] = service
        
        if found_keys:
            console.print("[green]Found existing API keys in environment:[/green]")
            for env_var, service in found_keys.items():
                console.print(f"  • {service}")
            
            if Confirm.ask("\nUse these keys?", default=True):
                for env_var in found_keys:
                    self.config['api_keys'][env_var.lower()] = f"${{{env_var}}}"
        
        # Ask about additional keys
        if Confirm.ask("\nWould you like to add API keys now?", default=False):
            console.print("\n[dim]Leave blank to skip any service[/dim]")
            
            # Anthropic
            if 'anthropic_api_key' not in self.config['api_keys']:
                key = Prompt.ask("Anthropic API key", password=True, default="")
                if key:
                    self.config['api_keys']['anthropic_api_key'] = key
            
            # OpenAI
            if 'openai_api_key' not in self.config['api_keys']:
                key = Prompt.ask("OpenAI API key", password=True, default="")
                if key:
                    self.config['api_keys']['openai_api_key'] = key
            
            # Custom endpoints
            if Confirm.ask("\nDo you use custom AI endpoints?", default=False):
                endpoint = Prompt.ask("Custom endpoint URL")
                key = Prompt.ask("API key", password=True)
                self.config['api_keys']['custom_endpoint'] = endpoint
                self.config['api_keys']['custom_key'] = key
        
        if self.config['api_keys']:
            console.print("\n[green]✓ API keys configured[/green]")
        else:
            console.print("\n[yellow]No API keys configured. You can add them later with: nexus config[/yellow]")
    
    def setup_services(self):
        """Setup service configuration"""
        console.print("\n[bold cyan]Service Configuration[/bold cyan]")
        console.print("NEXUS runs several services. Let's configure them.\n")
        
        # Check available ports
        def is_port_available(port: int) -> bool:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return True
                except:
                    return False
        
        # Default ports
        default_ports = {
            'web_ui': 8000,
            'api': 8001,
            'websocket': 8002,
            'monitoring': 8003
        }
        
        # Check and suggest ports
        console.print("Checking available ports...")
        services = {}
        
        for service, default_port in default_ports.items():
            if is_port_available(default_port):
                port = default_port
                status = "[green]available[/green]"
            else:
                # Find next available port
                port = default_port
                while not is_port_available(port) and port < default_port + 100:
                    port += 1
                status = f"[yellow]using {port} (default {default_port} in use)[/yellow]"
            
            console.print(f"  • {service.replace('_', ' ').title()}: Port {port} {status}")
            
            services[service] = {
                'enabled': True,
                'port': port,
                'host': '127.0.0.1'
            }
        
        # Ask about external access
        if Confirm.ask("\nAllow external access to services?", default=False):
            console.print("[yellow]⚠️  This will expose services to your network[/yellow]")
            for service in services:
                services[service]['host'] = '0.0.0.0'
        
        self.config['services'] = services
        console.print("\n[green]✓ Services configured[/green]")
    
    def setup_features(self):
        """Setup feature preferences"""
        console.print("\n[bold cyan]Feature Selection[/bold cyan]")
        console.print("Choose which NEXUS features to enable:\n")
        
        features = {
            'voice_control': {
                'name': 'Voice Control',
                'description': 'Control NEXUS with voice commands',
                'default': True
            },
            'vision_processing': {
                'name': 'Vision Processing',
                'description': 'Analyze screenshots and images',
                'default': True
            },
            'auto_complete': {
                'name': 'AI Auto-Complete',
                'description': 'Intelligent code completion',
                'default': True
            },
            'continuous_learning': {
                'name': 'Continuous Learning',
                'description': 'Learn from your coding patterns',
                'default': True
            },
            'web_scraping': {
                'name': 'Web Scraping',
                'description': 'Extract information from websites',
                'default': False
            },
            'web_interface': {
                'name': 'Web Interface',
                'description': 'Web UI for NEXUS control and monitoring',
                'default': True
            },
            'project_generation': {
                'name': 'Project Generation',
                'description': 'Generate complete project structures',
                'default': True
            },
            'code_review': {
                'name': 'AI Code Review',
                'description': 'Automatic code quality checks',
                'default': True
            },
            'deployment_automation': {
                'name': 'Deployment Automation',
                'description': 'Automated deployment pipelines',
                'default': False
            }
        }
        
        for feature_id, feature_info in features.items():
            enabled = Confirm.ask(
                f"Enable {feature_info['name']}? ({feature_info['description']})",
                default=feature_info['default']
            )
            self.config['features'][feature_id] = enabled
        
        console.print("\n[green]✓ Features configured[/green]")
    
    def setup_preferences(self):
        """Setup user preferences"""
        console.print("\n[bold cyan]Preferences[/bold cyan]\n")
        
        # Theme
        console.print("Choose your theme:")
        themes = ['Dark', 'Light', 'Auto (follows system)', 'Matrix', 'Cyberpunk']
        for i, theme in enumerate(themes, 1):
            console.print(f"{i}. {theme}")
        
        theme_choice = Prompt.ask("Select theme", choices=[str(i) for i in range(1, len(themes) + 1)], default='1')
        theme_map = {
            '1': 'dark',
            '2': 'light',
            '3': 'auto',
            '4': 'matrix',
            '5': 'cyberpunk'
        }
        
        # Editor
        console.print("\nPreferred code editor:")
        editors = ['VS Code', 'Sublime Text', 'Vim/Neovim', 'Emacs', 'IntelliJ', 'Other']
        for i, editor in enumerate(editors, 1):
            console.print(f"{i}. {editor}")
        
        editor_choice = Prompt.ask("Select editor", choices=[str(i) for i in range(1, len(editors) + 1)], default='1')
        editor = editors[int(editor_choice) - 1]
        
        # Auto-save
        auto_save = Confirm.ask("\nEnable auto-save?", default=True)
        
        # Telemetry
        console.print("\n[dim]NEXUS can collect anonymous usage data to improve the experience.[/dim]")
        telemetry = Confirm.ask("Enable telemetry?", default=False)
        
        self.config['preferences'] = {
            'theme': theme_map[theme_choice],
            'editor': editor,
            'auto_save': auto_save,
            'telemetry': telemetry,
            'notifications': True,
            'sound_effects': False
        }
        
        console.print("\n[green]✓ Preferences saved[/green]")
    
    def show_tutorial(self):
        """Show quick tutorial"""
        console.clear()
        
        tutorial = """
# NEXUS Quick Start Tutorial

## Basic Commands

### 1. Start NEXUS
```bash
nexus
```

### 2. Create a new project
```bash
nexus create myproject --template react
```

### 3. Chat with AI
```bash
nexus chat
> Help me build a REST API
```

### 4. Check status
```bash
nexus status
```

## Keyboard Shortcuts (in Terminal UI)

- **1-6**: Switch between tabs
- **Ctrl+Tab**: Next tab
- **Ctrl+P**: Command palette
- **Ctrl+Q**: Quit

## Web Interface

Open your browser to: http://localhost:8000

## Voice Commands

Say "Hey NEXUS" followed by:
- "Create a new project"
- "Show me the code"
- "Run the tests"
- "Deploy to production"

## Getting Help

- In terminal: `nexus help`
- In chat: Type "help"
- Online: https://nexus.ai/docs
        """
        
        console.print(Panel(Markdown(tutorial), title="Quick Start Tutorial", border_style="cyan"))
        console.print("\nPress Enter to continue...")
        input()
    
    def show_summary(self):
        """Show configuration summary"""
        console.clear()
        console.print("[bold cyan]Configuration Summary[/bold cyan]\n")
        
        # Profile
        profile = self.config['profile']
        console.print(f"[bold]Profile:[/bold]")
        console.print(f"  Name: {profile['name']}")
        console.print(f"  Level: {profile['experience_level']}")
        console.print(f"  Language: {profile['primary_language']}")
        console.print(f"  Focus: {profile['focus_area']}")
        
        # API Keys
        console.print(f"\n[bold]API Keys:[/bold]")
        if self.config['api_keys']:
            for key in self.config['api_keys']:
                console.print(f"  • {key.replace('_', ' ').title()}: [green]Configured[/green]")
        else:
            console.print("  [yellow]None configured[/yellow]")
        
        # Services
        console.print(f"\n[bold]Services:[/bold]")
        for service, config in self.config['services'].items():
            if config['enabled']:
                console.print(f"  • {service.replace('_', ' ').title()}: Port {config['port']}")
        
        # Features
        console.print(f"\n[bold]Enabled Features:[/bold]")
        for feature, enabled in self.config['features'].items():
            if enabled:
                console.print(f"  • {feature.replace('_', ' ').title()}")
        
        # Preferences
        prefs = self.config['preferences']
        console.print(f"\n[bold]Preferences:[/bold]")
        console.print(f"  Theme: {prefs['theme']}")
        console.print(f"  Editor: {prefs['editor']}")
        console.print(f"  Auto-save: {'Yes' if prefs['auto_save'] else 'No'}")
        
        console.print("\n[green]✓ Configuration complete![/green]")
        console.print("\nYou can change these settings anytime with: [cyan]nexus config[/cyan]")

def main():
    """Run wizard standalone"""
    wizard = ConfigWizard()
    config = wizard.run()
    
    # Save configuration
    config_dir = Path.home() / '.nexus' / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    console.print("\n[green]Configuration saved![/green]")

if __name__ == "__main__":
    main()