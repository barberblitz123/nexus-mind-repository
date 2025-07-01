# Voice Commands Reference

NEXUS supports natural language voice commands for all development tasks. This guide covers all available voice commands organized by category.

## Table of Contents
- [Activation & Control](#activation--control)
- [File Operations](#file-operations)
- [Code Navigation](#code-navigation)
- [Code Generation](#code-generation)
- [Editing Commands](#editing-commands)
- [Project Management](#project-management)
- [Git Operations](#git-operations)
- [Testing & Debugging](#testing--debugging)
- [AI Assistant](#ai-assistant)
- [Custom Commands](#custom-commands)

## Activation & Control

### Starting Voice Control
- **"Hey NEXUS"** - Activate voice control
- **"Start listening"** - Begin voice input
- **"Wake up"** - Alternative activation

### Stopping Voice Control
- **"Stop listening"** - Pause voice input
- **"Go to sleep"** - Deactivate voice control
- **"Cancel"** - Cancel current voice operation

### Voice Settings
- **"Increase sensitivity"** - Make voice detection more sensitive
- **"Decrease sensitivity"** - Make voice detection less sensitive
- **"Voice settings"** - Open voice configuration
- **"Calibrate voice"** - Run voice calibration wizard

## File Operations

### Creating Files
- **"Create new file"** - Create untitled file
- **"Create file [name]"** - Create named file
  - Example: "Create file utils.py"
- **"Create [type] file called [name]"** - Create specific file type
  - Example: "Create Python file called helpers"
- **"New [language] file"** - Create file with language template
  - Example: "New JavaScript file"

### Opening Files
- **"Open file [name]"** - Open specific file
  - Example: "Open file main.py"
- **"Open [name]"** - Smart file search and open
- **"Show file [name]"** - Display file in editor
- **"Switch to [file]"** - Change active file

### Saving Files
- **"Save file"** - Save current file
- **"Save all files"** - Save all open files
- **"Save as [name]"** - Save with new name
- **"Save and close"** - Save then close file

### File Management
- **"Close file"** - Close current file
- **"Close all files"** - Close all open files
- **"Delete file"** - Delete current file (with confirmation)
- **"Rename file to [name]"** - Rename current file
- **"Duplicate file"** - Create copy of current file

## Code Navigation

### Moving Cursor
- **"Go to line [number]"** - Jump to specific line
  - Example: "Go to line 42"
- **"Go to start"** - Move to beginning of file
- **"Go to end"** - Move to end of file
- **"Go to function [name]"** - Jump to function definition
  - Example: "Go to function calculateTotal"

### Finding Code
- **"Find [text]"** - Search for text
  - Example: "Find TODO"
- **"Find next"** - Go to next search result
- **"Find previous"** - Go to previous result
- **"Find and replace [old] with [new]"** - Replace text
  - Example: "Find and replace getName with getUserName"

### Code Structure Navigation
- **"Show outline"** - Display file structure
- **"Go to definition"** - Jump to definition of symbol at cursor
- **"Show references"** - Find all references to current symbol
- **"Go back"** - Return to previous location
- **"Go forward"** - Move forward in navigation history

### Bookmarks
- **"Add bookmark"** - Bookmark current line
- **"Remove bookmark"** - Remove bookmark from current line
- **"Next bookmark"** - Jump to next bookmark
- **"Previous bookmark"** - Jump to previous bookmark
- **"Clear all bookmarks"** - Remove all bookmarks

## Code Generation

### Functions & Methods
- **"Create function"** - Generate function template
- **"Create function called [name]"** - Generate named function
  - Example: "Create function called validateEmail"
- **"Create function to [description]"** - Generate function from description
  - Example: "Create function to calculate the area of a circle"
- **"Generate method [name]"** - Create class method
- **"Add constructor"** - Generate constructor/init method

### Classes & Structures
- **"Create class [name]"** - Generate class
  - Example: "Create class User"
- **"Create interface [name]"** - Generate interface (TypeScript/Java)
- **"Create struct [name]"** - Generate struct (C/C++/Go)
- **"Add property [name]"** - Add property to class

### Code Patterns
- **"Generate getter and setter"** - Create accessor methods
- **"Create singleton"** - Generate singleton pattern
- **"Add error handling"** - Wrap code in try-catch
- **"Create async function"** - Generate async function template

### Documentation
- **"Add comments"** - Generate comments for current code
- **"Document function"** - Add docstring/JSDoc
- **"Generate README"** - Create README for project
- **"Add TODO comment"** - Insert TODO comment

## Editing Commands

### Text Manipulation
- **"Select all"** - Select entire file
- **"Select line"** - Select current line
- **"Select word"** - Select current word
- **"Select function"** - Select entire function
- **"Copy"** - Copy selection
- **"Cut"** - Cut selection
- **"Paste"** - Paste from clipboard
- **"Duplicate line"** - Duplicate current line

### Code Formatting
- **"Format code"** - Auto-format current file
- **"Format selection"** - Format selected code
- **"Fix indentation"** - Correct indentation
- **"Convert tabs to spaces"** - Replace tabs with spaces

### Refactoring
- **"Rename symbol"** - Rename variable/function everywhere
- **"Extract method"** - Extract selection to new method
- **"Extract variable"** - Extract expression to variable
- **"Inline variable"** - Replace variable with its value

### Multi-cursor Editing
- **"Add cursor above"** - Add cursor on line above
- **"Add cursor below"** - Add cursor on line below
- **"Select next occurrence"** - Select next matching text
- **"Select all occurrences"** - Select all matching text

## Project Management

### Project Operations
- **"Create new project"** - Start project creation wizard
- **"Open project"** - Open project browser
- **"Close project"** - Close current project
- **"Switch to project [name]"** - Change active project
- **"Show project structure"** - Display project tree

### Building & Running
- **"Run project"** - Execute current project
- **"Build project"** - Compile/build project
- **"Clean build"** - Clean and rebuild
- **"Run tests"** - Execute test suite
- **"Debug application"** - Start debugger

### Dependencies
- **"Install dependencies"** - Install project dependencies
- **"Update dependencies"** - Update to latest versions
- **"Add package [name]"** - Install specific package
  - Example: "Add package express"
- **"Remove package [name]"** - Uninstall package

### Terminal Commands
- **"Open terminal"** - Show terminal panel
- **"Run command [command]"** - Execute terminal command
  - Example: "Run command npm start"
- **"Clear terminal"** - Clear terminal output
- **"New terminal"** - Open new terminal instance

## Git Operations

### Basic Git Commands
- **"Git status"** - Show working tree status
- **"Git add all"** - Stage all changes
- **"Git add file"** - Stage current file
- **"Git commit"** - Open commit dialog
- **"Git commit with message [message]"** - Quick commit
  - Example: "Git commit with message fix navigation bug"

### Branching
- **"Create branch [name]"** - Create new branch
  - Example: "Create branch feature-login"
- **"Switch to branch [name]"** - Checkout branch
- **"Show branches"** - List all branches
- **"Merge branch [name]"** - Merge branch into current

### Remote Operations
- **"Git push"** - Push to remote
- **"Git pull"** - Pull from remote
- **"Git fetch"** - Fetch remote changes
- **"Git clone [url]"** - Clone repository

### History & Diffs
- **"Show git log"** - Display commit history
- **"Show changes"** - Display uncommitted changes
- **"Git diff"** - Show detailed differences
- **"Revert changes"** - Discard local changes

## Testing & Debugging

### Running Tests
- **"Run tests"** - Execute all tests
- **"Run test file"** - Test current file
- **"Run test [name]"** - Run specific test
  - Example: "Run test userAuthentication"
- **"Run failed tests"** - Re-run only failed tests

### Debugging
- **"Start debugging"** - Launch debugger
- **"Add breakpoint"** - Set breakpoint at current line
- **"Remove breakpoint"** - Remove breakpoint
- **"Toggle breakpoint"** - Toggle breakpoint on/off
- **"Continue"** - Resume execution
- **"Step over"** - Step over current line
- **"Step into"** - Step into function
- **"Step out"** - Step out of function
- **"Stop debugging"** - End debug session

### Code Analysis
- **"Run linter"** - Check code quality
- **"Fix linting errors"** - Auto-fix linting issues
- **"Check syntax"** - Validate syntax
- **"Find problems"** - Run code analysis

## AI Assistant

### Code Help
- **"Explain this code"** - Get explanation of selected code
- **"How do I [task]"** - Ask how to implement something
  - Example: "How do I connect to MongoDB"
- **"What does this error mean"** - Explain error message
- **"Suggest improvements"** - Get code improvement suggestions

### Code Generation with AI
- **"Generate code to [description]"** - AI creates code
  - Example: "Generate code to validate email addresses"
- **"Complete this function"** - AI finishes incomplete function
- **"Write tests for this"** - AI generates test cases
- **"Optimize this code"** - AI suggests optimizations

### Learning & Documentation
- **"Show documentation for [topic]"** - Display docs
  - Example: "Show documentation for Array.map"
- **"Explain [concept]"** - Get concept explanation
  - Example: "Explain recursion"
- **"Show examples of [pattern]"** - See code examples
  - Example: "Show examples of observer pattern"

## Custom Commands

### Creating Custom Commands
- **"Create custom command"** - Open command creator
- **"Record macro"** - Start recording actions
- **"Stop recording"** - End macro recording
- **"Save macro as [name]"** - Save recorded macro

### Using Custom Commands
- **"Run command [name]"** - Execute custom command
- **"List custom commands"** - Show all custom commands
- **"Edit command [name]"** - Modify existing command
- **"Delete command [name]"** - Remove custom command

### Command Shortcuts
You can create voice shortcuts for complex operations:

```
"Deploy to production" → 
  1. Run tests
  2. Build project  
  3. Git commit
  4. Git push
  5. Deploy script
```

## Advanced Voice Features

### Natural Language Understanding
NEXUS understands variations and context:
- "Make a new Python file" = "Create Python file"
- "Can you create a function that sorts an array" = "Create function to sort array"
- "I need to see the project files" = "Show project structure"

### Contextual Commands
Commands work based on context:
- In Python file: "Create function" generates Python syntax
- In JavaScript: "Create function" generates JS syntax
- With text selected: "Comment" adds language-specific comments

### Chaining Commands
Combine multiple operations:
- **"Save all files and run tests"**
- **"Format code and commit changes"**
- **"Create new branch and switch to it"**

### Dictation Mode
- **"Start dictation"** - Enter free-form text/code
- **"Stop dictation"** - Exit dictation mode
- **"New line"** - Insert line break while dictating
- **"Tab"** - Insert tab character
- **"Delete last word"** - Remove last dictated word

## Tips for Effective Voice Control

1. **Speak Clearly**: Enunciate commands clearly
2. **Use Pauses**: Brief pause after "Hey NEXUS" before command
3. **Be Specific**: Include file names and function names when possible
4. **Learn Shortcuts**: Memorize frequently used commands
5. **Customize**: Create custom commands for your workflow
6. **Practice**: Regular use improves recognition accuracy

## Troubleshooting Voice Commands

### Command Not Recognized
- Check microphone connection
- Speak more clearly/slowly
- Use alternative phrasing
- Run voice calibration

### Wrong Action Performed
- Be more specific in commands
- Check context (correct file type)
- Use exact command syntax
- Report ambiguous commands for improvement

### Voice Control Not Responding
- Check activation phrase volume
- Verify microphone permissions
- Restart voice service
- Check system audio settings

## Language Support

NEXUS supports voice commands in multiple languages:
- English (US/UK/AU)
- Spanish
- French  
- German
- Japanese
- Mandarin Chinese

Switch language with: **"Change language to [language]"**