#!/usr/bin/env python3
"""
🚀 Enhanced MANUS Launcher
Easy launcher for the complete Enhanced MANUS system with all new features
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path


def print_banner():
    """Print the Enhanced MANUS banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗                 ║
    ║     ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝                 ║
    ║     ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗                 ║
    ║     ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║                 ║
    ║     ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║                 ║
    ║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                 ║
    ║                                                                   ║
    ║           🚀 ENHANCED MANUS - Complete Development Suite 🚀       ║
    ║                                                                   ║
    ║     ✨ Features:                                                  ║
    ║     • Project Generation from Natural Language                    ║
    ║     • Automatic Bug Detection and Fixing                          ║
    ║     • Security Vulnerability Scanning                             ║
    ║     • Performance Analysis and Optimization                       ║
    ║     • Documentation Generation                                     ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def quick_generate_project():
    """Quick project generation interface"""
    from nexus_enhanced_manus import EnhancedMANUSOmnipotent
    
    print("\n🏗️  PROJECT GENERATOR")
    print("="*50)
    
    description = input("\n📝 Describe your project in natural language:\n> ")
    
    project_types = ["auto", "web", "api", "fullstack", "mobile", "desktop"]
    print("\n📋 Project type (press Enter for auto-detect):")
    for i, ptype in enumerate(project_types):
        print(f"  {i}. {ptype}")
    
    type_input = input("> ").strip()
    project_type = project_types[int(type_input)] if type_input.isdigit() else "auto"
    
    output_dir = input("\n📁 Output directory (default: ./generated_project): ").strip()
    if not output_dir:
        output_dir = "./generated_project"
    
    print(f"\n🚀 Generating {project_type} project...")
    
    manus = EnhancedMANUSOmnipotent()
    result = await manus.execute_specialty({
        'command': 'generate_project',
        'description': description,
        'type': project_type,
        'output_dir': output_dir
    })
    
    print(f"\n✅ Project generated successfully!")
    print(f"📁 Location: {result.get('project_directory', output_dir)}")
    print(f"📄 Files created: {result.get('files_created', 'N/A')}")


async def quick_analyze_project():
    """Quick project analysis interface"""
    from nexus_enhanced_manus import EnhancedMANUSOmnipotent
    
    print("\n🔍 PROJECT ANALYZER")
    print("="*50)
    
    directory = input("\n📁 Project directory to analyze (default: .): ").strip()
    if not directory:
        directory = "."
    
    print("\n📋 Select analysis type:")
    print("  1. Full analysis (all tools)")
    print("  2. Bug detection only")
    print("  3. Security scan only")
    print("  4. Performance analysis only")
    print("  5. Generate documentation only")
    
    choice = input("> ").strip()
    
    manus = EnhancedMANUSOmnipotent()
    
    if choice == "1":
        print("\n🚀 Running full analysis...")
        result = await manus.execute_specialty({
            'command': 'full_analysis',
            'directory': directory
        })
        print(f"\n✅ Analysis complete! Report: {result.get('report_path', 'N/A')}")
        
    elif choice == "2":
        print("\n🐛 Detecting bugs...")
        result = await manus.execute_specialty({
            'command': 'analyze_project',
            'directory': directory,
            'include_security': False,
            'include_performance': False
        })
        bugs = result.get('bugs', {})
        print(f"\n✅ Found {bugs.get('total_bugs', 0)} bugs!")
        
    elif choice == "3":
        print("\n🛡️ Scanning for vulnerabilities...")
        result = await manus.execute_specialty({
            'command': 'analyze_project',
            'directory': directory,
            'include_security': True,
            'include_performance': False
        })
        security = result.get('security', {})
        print(f"\n✅ Risk Score: {security.get('risk_score', 0)}/10")
        print(f"🔒 Found {security.get('total_vulnerabilities', 0)} vulnerabilities")
        
    elif choice == "4":
        print("\n⚡ Analyzing performance...")
        result = await manus.execute_specialty({
            'command': 'optimize_performance',
            'directory': directory
        })
        print(f"\n✅ Analyzed {result.get('files_analyzed', 0)} files")
        print(f"💡 Found {result.get('optimization_opportunities', 0)} optimization opportunities")
        
    elif choice == "5":
        print("\n📚 Generating documentation...")
        from nexus_doc_generator import DocGeneratorOmnipotent
        generator = DocGeneratorOmnipotent()
        output_dir = f"{directory}/docs"
        await generator.sync_documentation(directory, output_dir)
        print(f"\n✅ Documentation generated in {output_dir}/")


async def interactive_menu():
    """Interactive menu for Enhanced MANUS"""
    while True:
        print("\n🚀 ENHANCED MANUS - MAIN MENU")
        print("="*50)
        print("1. Generate new project")
        print("2. Analyze existing project")
        print("3. Fix all issues automatically")
        print("4. Start web interface")
        print("5. Run demonstration")
        print("6. Show help")
        print("0. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
            
        elif choice == "1":
            await quick_generate_project()
            
        elif choice == "2":
            await quick_analyze_project()
            
        elif choice == "3":
            directory = input("\n📁 Project directory (default: .): ").strip() or "."
            print("\n🔧 Fixing all issues...")
            from nexus_enhanced_manus import EnhancedMANUSOmnipotent
            manus = EnhancedMANUSOmnipotent()
            result = await manus.execute_specialty({
                'command': 'fix_all_issues',
                'directory': directory,
                'auto_commit': False
            })
            print(f"\n✅ Fixed {result.get('total_fixes', 0)} issues!")
            
        elif choice == "4":
            print("\n🌐 Starting web interface...")
            print("   Access at: http://localhost:8001")
            print("   Press Ctrl+C to stop")
            os.system("python manus_web_interface.py")
            
        elif choice == "5":
            print("\n🎭 Running demonstration...")
            from demo_enhanced_manus import main as demo_main
            await demo_main()
            
        elif choice == "6":
            print_help()
        
        input("\nPress Enter to continue...")


def print_help():
    """Print help information"""
    print("""
📚 ENHANCED MANUS HELP
=====================

Enhanced MANUS is a complete development suite that includes:

1. PROJECT GENERATOR
   - Generates complete projects from natural language descriptions
   - Supports multiple frameworks (React, Vue, Flask, FastAPI, etc.)
   - Creates tests, documentation, and CI/CD pipelines

2. BUG DETECTOR
   - Finds common programming bugs and anti-patterns
   - Provides automatic fix suggestions
   - Supports Python, JavaScript, TypeScript

3. SECURITY SCANNER
   - Detects OWASP Top 10 vulnerabilities
   - Checks for hardcoded credentials
   - Identifies insecure coding patterns

4. PERFORMANCE ANALYZER
   - Calculates time/space complexity
   - Identifies optimization opportunities
   - Suggests algorithmic improvements

5. DOCUMENTATION GENERATOR
   - Generates API documentation
   - Creates user guides
   - Produces architecture diagrams

USAGE EXAMPLES:

# Generate a project
python launch_enhanced_manus.py --generate "Create a REST API for task management"

# Analyze current directory
python launch_enhanced_manus.py --analyze .

# Fix all issues
python launch_enhanced_manus.py --fix-all .

# Start web interface
python launch_enhanced_manus.py --web

For more information, see the documentation in the docs/ directory.
    """)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced MANUS - Complete Development Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--generate", 
        metavar="DESCRIPTION",
        help="Generate a project from description"
    )
    parser.add_argument(
        "--analyze", 
        metavar="DIRECTORY",
        help="Analyze a project directory"
    )
    parser.add_argument(
        "--fix-all", 
        metavar="DIRECTORY",
        help="Fix all issues in a project"
    )
    parser.add_argument(
        "--web", 
        action="store_true",
        help="Start the web interface"
    )
    parser.add_argument(
        "--demo", 
        action="store_true",
        help="Run the demonstration"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle command line arguments
    if args.generate:
        asyncio.run(quick_generate_project())
    elif args.analyze:
        # Set directory for analysis
        os.environ['ANALYZE_DIR'] = args.analyze
        asyncio.run(quick_analyze_project())
    elif args.fix_all:
        # Implement fix-all functionality
        pass
    elif args.web:
        print("\n🌐 Starting web interface...")
        print("   Access at: http://localhost:8001")
        os.system("python manus_web_interface.py")
    elif args.demo:
        from demo_enhanced_manus import main as demo_main
        asyncio.run(demo_main())
    else:
        # Interactive mode
        try:
            asyncio.run(interactive_menu())
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()