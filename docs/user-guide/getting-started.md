# Getting Started with NEXUS

Welcome to NEXUS - your AI-powered development assistant with voice control and intelligent code generation capabilities.

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [First Launch](#first-launch)
- [Basic Setup](#basic-setup)
- [Your First Project](#your-first-project)
- [Voice Control Setup](#voice-control-setup)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Processor**: Dual-core 2.0 GHz or faster
- **Memory**: 8GB RAM
- **Storage**: 5GB available space
- **Network**: Stable internet connection
- **Microphone**: Required for voice control features

### Recommended Specifications
- **Processor**: Quad-core 3.0 GHz or faster
- **Memory**: 16GB RAM or more
- **Storage**: 10GB available space (SSD recommended)
- **GPU**: NVIDIA GPU with CUDA support (for enhanced AI features)

## Installation

### Quick Install (All Platforms)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/nexus-mind/nexus-repository.git
   cd nexus-repository
   ```

2. **Install Dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   
   # Node.js dependencies
   cd nexus-web-app
   npm install
   cd ..
   ```

3. **Initialize Configuration**
   ```bash
   python nexus_cli.py init
   ```

### Platform-Specific Instructions

#### Windows
1. Install Python 3.9+ from [python.org](https://python.org)
2. Install Node.js 16+ from [nodejs.org](https://nodejs.org)
3. Run the Windows installer:
   ```powershell
   .\install_windows.ps1
   ```

#### macOS
1. Install Homebrew if not already installed
2. Install dependencies:
   ```bash
   brew install python@3.9 node
   ```
3. Run the installation script:
   ```bash
   ./install_macos.sh
   ```

#### Linux (Ubuntu/Debian)
1. Update package manager:
   ```bash
   sudo apt update
   ```
2. Install dependencies:
   ```bash
   sudo apt install python3.9 python3-pip nodejs npm
   ```
3. Run the installation script:
   ```bash
   ./install_linux.sh
   ```

## First Launch

### Starting NEXUS

1. **Launch the Application**
   ```bash
   python launch_nexus_enhanced.py
   ```

2. **Access the Web Interface**
   - Open your browser to `http://localhost:3000`
   - You'll see the NEXUS welcome screen

3. **Initial Configuration**
   - Set your preferred language
   - Choose your theme (light/dark/auto)
   - Configure voice control preferences
   - Set up API keys (optional for enhanced features)

### Interface Overview

The NEXUS interface consists of several key areas:

1. **Command Bar** (Top)
   - Voice control toggle
   - Quick commands
   - Search functionality

2. **Code Editor** (Center)
   - Multi-tab support
   - Syntax highlighting
   - IntelliSense
   - Real-time collaboration

3. **AI Assistant** (Right Panel)
   - Chat interface
   - Voice commands
   - Code suggestions
   - Documentation lookup

4. **Project Explorer** (Left Panel)
   - File browser
   - Project structure
   - Quick actions

5. **Terminal** (Bottom)
   - Integrated terminal
   - Command execution
   - Output logs

## Basic Setup

### Configuring Your Workspace

1. **Create a Workspace**
   - Click "New Workspace" or say "Create new workspace"
   - Choose a location for your projects
   - Name your workspace

2. **Import Existing Projects**
   - Click "Import Project" or say "Import project"
   - Navigate to your project folder
   - NEXUS will analyze and index your codebase

3. **Set Preferences**
   ```
   Voice Command: "Open settings"
   Or: Press Ctrl/Cmd + ,
   ```
   
   Configure:
   - Editor preferences (font, size, theme)
   - Voice control sensitivity
   - AI assistance level
   - Keyboard shortcuts

## Your First Project

### Creating a New Project

1. **Using Voice Commands**
   ```
   Say: "Create new Python project called my-app"
   ```

2. **Using the Interface**
   - Click "New Project" button
   - Select project type (Python, JavaScript, etc.)
   - Enter project name
   - Choose template (optional)

3. **Project Structure**
   NEXUS automatically creates:
   ```
   my-app/
   ├── src/
   │   └── main.py
   ├── tests/
   │   └── test_main.py
   ├── docs/
   │   └── README.md
   ├── .gitignore
   ├── requirements.txt
   └── setup.py
   ```

### Writing Your First Code

1. **Voice-Driven Development**
   ```
   Say: "Create a function to calculate fibonacci numbers"
   ```
   
   NEXUS will generate:
   ```python
   def fibonacci(n):
       """Calculate the nth Fibonacci number."""
       if n <= 0:
           return 0
       elif n == 1:
           return 1
       else:
           return fibonacci(n-1) + fibonacci(n-2)
   ```

2. **AI-Assisted Coding**
   - Start typing and NEXUS suggests completions
   - Ask questions in the chat panel
   - Request code reviews and improvements

## Voice Control Setup

### Enabling Voice Control

1. **Check Microphone**
   - Ensure your microphone is connected
   - Grant microphone permissions when prompted

2. **Calibrate Voice Recognition**
   ```
   Say: "Start voice calibration"
   ```
   - Follow the on-screen prompts
   - Read the sample phrases
   - NEXUS will optimize for your voice

3. **Voice Control Basics**
   - **Activation**: Say "Hey NEXUS" or press the voice button
   - **Commands**: Speak naturally, e.g., "Open file app.py"
   - **Dictation**: Say "Start dictation" to enter code by voice
   - **Stop**: Say "Stop listening" or press Escape

### Essential Voice Commands

**File Operations**
- "Create new file [filename]"
- "Open file [filename]"
- "Save file"
- "Close file"

**Navigation**
- "Go to line [number]"
- "Find [text]"
- "Go to definition"
- "Show references"

**Code Generation**
- "Create function [description]"
- "Add comments"
- "Generate tests"
- "Refactor this code"

**Project Management**
- "Run project"
- "Debug application"
- "Show terminal"
- "Git commit with message [message]"

## Next Steps

Now that you have NEXUS up and running:

1. **Explore Voice Commands**: See our [Voice Commands Reference](voice-commands.md)
2. **Learn Keyboard Shortcuts**: Check the [Keyboard Shortcuts Guide](keyboard-shortcuts.md)
3. **Try Common Workflows**: Follow our [Common Workflows Guide](common-workflows.md)
4. **Watch Tutorials**: View our [Video Tutorials](../tutorials/video-tutorials.md)

## Getting Help

- **In-App Help**: Say "Show help" or press F1
- **Documentation**: Say "Open documentation"
- **Community Forum**: Visit [community.nexus-mind.ai](https://community.nexus-mind.ai)
- **Support**: Email support@nexus-mind.ai

## Tips for Success

1. **Start Simple**: Begin with basic voice commands before trying complex operations
2. **Use Natural Language**: NEXUS understands conversational requests
3. **Combine Methods**: Use voice, keyboard, and mouse together for maximum efficiency
4. **Customize**: Tailor NEXUS to your workflow with custom commands and shortcuts
5. **Practice**: The more you use voice control, the better NEXUS adapts to your speech patterns

Welcome to the future of AI-assisted development with NEXUS!