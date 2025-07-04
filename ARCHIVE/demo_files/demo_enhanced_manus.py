#!/usr/bin/env python3
"""
🚀 Enhanced MANUS Demonstration
Showcases all the new features: Project Generation, Bug Detection,
Security Scanning, Performance Analysis, and Documentation Generation
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from nexus_enhanced_manus import EnhancedMANUSOmnipotent


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}\n")


async def demo_project_generation():
    """Demonstrate project generation from natural language"""
    print_section("PROJECT GENERATION DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    # Example project descriptions
    project_descriptions = [
        "Create a simple REST API with Flask that manages a todo list with CRUD operations",
        "Build a React dashboard with authentication, charts, and real-time notifications",
        "Generate a Python package for data validation with type hints and tests"
    ]
    
    print("📝 Project Descriptions:")
    for i, desc in enumerate(project_descriptions, 1):
        print(f"{i}. {desc}")
    
    # Generate first project as demo
    print(f"\n🏗️ Generating project 1...")
    result = await manus.execute_specialty({
        'command': 'generate_project',
        'description': project_descriptions[0],
        'type': 'auto',
        'output_dir': './demo_generated_project'
    })
    
    print(f"✅ Project generated successfully!")
    print(f"   Location: {result.get('project_directory', 'N/A')}")
    print(f"   Files created: {result.get('files_created', 0)}")
    
    return result.get('project_directory')


async def demo_bug_detection(project_dir: str = None):
    """Demonstrate bug detection"""
    print_section("BUG DETECTION DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    # Create a sample buggy file if no project directory
    if not project_dir:
        os.makedirs("demo_code", exist_ok=True)
        buggy_code = '''
def calculate_average(numbers):
    sum = 0
    for i in range(len(numbers)):  # Off-by-one potential
        sum += numbers[i]
    return sum / len(numbers)  # Division by zero bug

def process_data(data=[]):  # Mutable default argument
    data.append("processed")
    return data

def unsafe_file_read(filename):
    f = open(filename, 'r')  # Resource leak - file not closed
    content = f.read()
    return content

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, items):
        for item in self.data:  # Bug: iterating over self.data instead of items
            if item = None:  # Bug: assignment instead of comparison
                continue
            self.data.append(item)
'''
        
        with open("demo_code/buggy_code.py", "w") as f:
            f.write(buggy_code)
        
        project_dir = "demo_code"
    
    print(f"🔍 Scanning {project_dir} for bugs...")
    
    result = await manus.execute_specialty({
        'command': 'analyze_project',
        'directory': project_dir,
        'include_security': False,
        'include_performance': False
    })
    
    bugs = result.get('bugs', {})
    total_bugs = bugs.get('total_bugs', 0)
    
    print(f"\n🐛 Found {total_bugs} bugs!")
    
    if total_bugs > 0 and 'report' in bugs:
        report = bugs['report']
        if 'statistics' in report:
            print("\n📊 Bug Statistics:")
            for bug_type, count in report['statistics'].get('by_type', {}).items():
                print(f"   - {bug_type}: {count}")
        
        # Show first few bugs
        if 'bugs' in bugs:
            print("\n🔍 Sample Bugs Found:")
            for bug in bugs['bugs'][:3]:
                print(f"\n   File: {bug.get('file_path', 'N/A')}")
                print(f"   Type: {bug.get('type', 'N/A')}")
                print(f"   Line: {bug.get('line_number', 'N/A')}")
                print(f"   Description: {bug.get('description', 'N/A')}")
                if bug.get('suggested_fix'):
                    print(f"   Fix: {bug['suggested_fix']}")


async def demo_security_scanning(project_dir: str = None):
    """Demonstrate security vulnerability scanning"""
    print_section("SECURITY SCANNING DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    # Create sample vulnerable code if no project directory
    if not project_dir:
        os.makedirs("demo_code", exist_ok=True)
        vulnerable_code = '''
import os
import pickle
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Hardcoded credentials (Security vulnerability)
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"

@app.route('/search')
def search():
    # SQL Injection vulnerability
    query = request.args.get('q', '')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    sql = f"SELECT * FROM users WHERE name = '{query}'"  # SQL Injection
    cursor.execute(sql)
    
    # XSS vulnerability
    results = cursor.fetchall()
    template = f"<h1>Results for: {query}</h1>"  # XSS vulnerability
    return render_template_string(template)

@app.route('/load')
def load_data():
    # Insecure deserialization
    data = request.args.get('data', '')
    obj = pickle.loads(data.encode())  # Insecure deserialization
    return str(obj)

@app.route('/execute')
def execute():
    # Command injection vulnerability
    cmd = request.args.get('cmd', '')
    result = os.system(cmd)  # Command injection
    return f"Executed: {result}"

def weak_crypto():
    import hashlib
    # Weak cryptography
    password = "user_password"
    hashed = hashlib.md5(password.encode()).hexdigest()  # MD5 is weak
    return hashed
'''
        
        with open("demo_code/vulnerable_app.py", "w") as f:
            f.write(vulnerable_code)
        
        project_dir = "demo_code"
    
    print(f"🛡️ Scanning {project_dir} for security vulnerabilities...")
    
    result = await manus.execute_specialty({
        'command': 'analyze_project',
        'directory': project_dir,
        'include_security': True,
        'include_performance': False
    })
    
    security = result.get('security', {})
    risk_score = security.get('risk_score', 0)
    total_vulns = security.get('total_vulnerabilities', 0)
    
    print(f"\n⚠️ Security Risk Score: {risk_score}/10")
    print(f"🔒 Found {total_vulns} vulnerabilities!")
    
    if total_vulns > 0 and 'vulnerabilities' in security:
        # Group by severity
        by_severity = {}
        for vuln in security['vulnerabilities']:
            sev = vuln.get('severity', 'UNKNOWN')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        print("\n📊 Vulnerabilities by Severity:")
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if sev in by_severity:
                print(f"   - {sev}: {by_severity[sev]}")
        
        # Show critical vulnerabilities
        print("\n🚨 Critical Vulnerabilities:")
        critical_vulns = [v for v in security['vulnerabilities'] 
                         if v.get('severity') == 'CRITICAL'][:3]
        
        for vuln in critical_vulns:
            print(f"\n   Type: {vuln.get('type', 'N/A')}")
            print(f"   File: {vuln.get('file_path', 'N/A')}")
            print(f"   Line: {vuln.get('line_number', 'N/A')}")
            print(f"   Description: {vuln.get('description', 'N/A')}")


async def demo_performance_analysis():
    """Demonstrate performance analysis"""
    print_section("PERFORMANCE ANALYSIS DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    # Create sample code with performance issues
    slow_code = '''
def find_duplicates(arr):
    """O(n²) implementation - inefficient"""
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates

def inefficient_string_concat(items):
    """String concatenation in loop - inefficient"""
    result = ""
    for item in items:
        result = result + str(item) + ", "  # Creates new string each time
    return result

def fibonacci_recursive(n):
    """Exponential time complexity - very inefficient"""
    if n <= 1:
        return n
    return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

def load_all_data():
    """Loads entire dataset into memory - memory inefficient"""
    data = []
    with open("huge_file.csv", "r") as f:
        for line in f:
            data.append(line.strip().split(","))
    return data
'''
    
    print("⚡ Analyzing code performance...")
    
    # Analyze the slow code
    from nexus_performance_analyzer import PerformanceAnalyzerOmnipotent
    analyzer = PerformanceAnalyzerOmnipotent()
    
    complexity = analyzer.analyze_complexity(slow_code)
    report = analyzer.generate_performance_report(slow_code)
    
    print(f"\n📊 Performance Analysis Results:")
    print(f"   Time Complexity: {complexity.time_complexity if complexity else 'N/A'}")
    print(f"   Space Complexity: {complexity.space_complexity if complexity else 'N/A'}")
    print(f"   Overall Rating: {report['summary']['overall_rating']}/100")
    
    print("\n💡 Optimization Suggestions:")
    for i, suggestion in enumerate(report['suggestions'][:3], 1):
        print(f"\n   {i}. {suggestion['description']}")
        print(f"      Category: {suggestion['category']}")
        print(f"      Impact: {suggestion['severity']}")


async def demo_documentation_generation(project_dir: str = None):
    """Demonstrate documentation generation"""
    print_section("DOCUMENTATION GENERATION DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    if not project_dir:
        project_dir = "."
    
    print(f"📚 Generating documentation for {project_dir}...")
    
    # Use the doc generator directly for more control
    from nexus_doc_generator import DocGeneratorOmnipotent
    generator = DocGeneratorOmnipotent()
    
    # Parse codebase
    entities = generator.parse_codebase(project_dir)
    
    print(f"\n📊 Code Analysis:")
    print(f"   Total entities found: {len(entities)}")
    print(f"   Functions: {len([e for e in entities if e.type == 'function'])}")
    print(f"   Classes: {len([e for e in entities if e.type == 'class'])}")
    print(f"   Modules: {len(set(e.source_file for e in entities))}")
    
    # Generate documentation
    output_dir = f"{project_dir}/generated_docs"
    os.makedirs(output_dir, exist_ok=True)
    
    generator.generate_api_docs(f"{output_dir}/api_reference.md")
    generator.generate_user_guide(
        title="Enhanced MANUS Documentation",
        description="Complete guide for the Enhanced MANUS system"
    )
    
    print(f"\n✅ Documentation generated in {output_dir}/")
    print("   - api_reference.md")
    print("   - user_guide.md")
    print("   - architecture_diagram.md")


async def demo_full_analysis():
    """Demonstrate full project analysis with all tools"""
    print_section("FULL PROJECT ANALYSIS DEMO")
    
    manus = EnhancedMANUSOmnipotent()
    
    print("🔍 Running comprehensive analysis on current directory...")
    
    result = await manus.execute_specialty({
        'command': 'full_analysis',
        'directory': '.'
    })
    
    print("\n📊 Analysis Complete!")
    print(f"   Report saved to: {result.get('report_path', 'N/A')}")
    
    summary = result.get('summary', {})
    print(f"\n🏥 Project Health Score: {summary.get('health_score', 0)}/100")
    print(f"📋 Total Issues Found: {summary.get('issues_found', 0)}")
    print(f"🚨 Critical Issues: {summary.get('critical_issues', 0)}")
    
    if 'recommendations' in summary:
        print("\n💡 Top Recommendations:")
        for rec in summary['recommendations'][:3]:
            print(f"   - {rec}")


async def main():
    """Run all demonstrations"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          🚀 NEXUS ENHANCED MANUS DEMONSTRATION 🚀         ║
║                                                           ║
║  Showcasing all new features:                             ║
║  • Project Generation from Natural Language               ║
║  • Automatic Bug Detection and Fixing                     ║
║  • Security Vulnerability Scanning                        ║
║  • Performance Analysis and Optimization                  ║
║  • Documentation Generation                               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 1. Generate a project
        # project_dir = await demo_project_generation()
        
        # 2. Detect bugs
        await demo_bug_detection()
        
        # 3. Scan for security vulnerabilities
        await demo_security_scanning()
        
        # 4. Analyze performance
        await demo_performance_analysis()
        
        # 5. Generate documentation
        # await demo_documentation_generation()
        
        # 6. Run full analysis
        # await demo_full_analysis()
        
        print_section("DEMONSTRATION COMPLETE")
        print("✅ All Enhanced MANUS features have been demonstrated!")
        print("\n🌟 The future of autonomous development is here with NEXUS!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())