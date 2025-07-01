# Plugin Development Guide

Create powerful extensions for NEXUS to add new features, integrate external tools, or customize the development experience. This guide covers everything you need to know about developing NEXUS plugins.

## Table of Contents
- [Getting Started](#getting-started)
- [Plugin Architecture](#plugin-architecture)
- [Creating Your First Plugin](#creating-your-first-plugin)
- [Extension Points](#extension-points)
- [API Reference](#api-reference)
- [Voice Command Integration](#voice-command-integration)
- [AI Model Integration](#ai-model-integration)
- [UI Components](#ui-components)
- [Testing Plugins](#testing-plugins)
- [Publishing Plugins](#publishing-plugins)

## Getting Started

### Prerequisites

- Node.js 16+ or Python 3.9+
- NEXUS SDK
- Basic understanding of NEXUS architecture
- Git for version control

### Development Setup

1. **Install NEXUS SDK**
   ```bash
   npm install -g @nexus-mind/sdk
   # or
   pip install nexus-sdk
   ```

2. **Create Plugin Workspace**
   ```bash
   nexus-sdk create-plugin my-awesome-plugin
   cd my-awesome-plugin
   ```

3. **Install Dependencies**
   ```bash
   npm install
   # or
   pip install -r requirements.txt
   ```

### Plugin Structure

```
my-awesome-plugin/
├── package.json          # Plugin manifest
├── src/
│   ├── index.ts         # Main entry point
│   ├── commands/        # Command implementations
│   ├── providers/       # Service providers
│   ├── ui/             # UI components
│   └── tests/          # Unit tests
├── resources/
│   ├── icons/          # Plugin icons
│   └── styles/         # CSS styles
├── README.md
└── LICENSE
```

## Plugin Architecture

### Plugin Manifest

Every plugin requires a manifest file (`package.json` or `plugin.yaml`):

```json
{
  "name": "my-awesome-plugin",
  "displayName": "My Awesome Plugin",
  "version": "1.0.0",
  "description": "Adds awesome features to NEXUS",
  "author": "Your Name",
  "license": "MIT",
  "engines": {
    "nexus": "^2.0.0"
  },
  "main": "./dist/index.js",
  "activationEvents": [
    "onCommand:myPlugin.doSomething",
    "onLanguage:python",
    "onStartup"
  ],
  "contributes": {
    "commands": [{
      "command": "myPlugin.doSomething",
      "title": "Do Something Awesome",
      "category": "My Plugin"
    }],
    "configuration": {
      "title": "My Plugin Settings",
      "properties": {
        "myPlugin.enableFeature": {
          "type": "boolean",
          "default": true,
          "description": "Enable awesome feature"
        }
      }
    }
  }
}
```

### Plugin Lifecycle

```typescript
import { ExtensionContext } from '@nexus-mind/sdk';

export async function activate(context: ExtensionContext) {
    console.log('My Awesome Plugin is now active!');
    
    // Register commands
    context.subscriptions.push(
        nexus.commands.registerCommand('myPlugin.doSomething', async () => {
            await doSomethingAwesome();
        })
    );
    
    // Initialize services
    const myService = new MyService();
    context.subscriptions.push(myService);
}

export async function deactivate() {
    console.log('My Awesome Plugin is deactivating');
    // Cleanup resources
}
```

## Creating Your First Plugin

### Step 1: Define Functionality

Let's create a plugin that adds code snippet management:

```typescript
// src/index.ts
import * as nexus from '@nexus-mind/sdk';

export async function activate(context: nexus.ExtensionContext) {
    // Register snippet command
    const disposable = nexus.commands.registerCommand(
        'snippets.insert',
        async () => {
            const snippets = await loadSnippets();
            const selected = await nexus.window.showQuickPick(
                snippets.map(s => s.name),
                { placeHolder: 'Select a snippet to insert' }
            );
            
            if (selected) {
                const snippet = snippets.find(s => s.name === selected);
                const editor = nexus.window.activeTextEditor;
                if (editor && snippet) {
                    await editor.insertSnippet(snippet.content);
                }
            }
        }
    );
    
    context.subscriptions.push(disposable);
}
```

### Step 2: Add Voice Commands

```typescript
// src/commands/voice-commands.ts
export function registerVoiceCommands(context: nexus.ExtensionContext) {
    // Register voice command
    context.subscriptions.push(
        nexus.voice.registerCommand({
            phrase: "insert snippet",
            variations: [
                "add snippet",
                "use snippet",
                "insert code snippet"
            ],
            handler: async (args) => {
                await nexus.commands.executeCommand('snippets.insert');
            }
        })
    );
    
    // Voice command with parameters
    context.subscriptions.push(
        nexus.voice.registerCommand({
            phrase: "insert {snippetName} snippet",
            parameters: {
                snippetName: {
                    type: 'string',
                    suggestions: async () => {
                        const snippets = await loadSnippets();
                        return snippets.map(s => s.name);
                    }
                }
            },
            handler: async (args) => {
                await insertSnippet(args.snippetName);
            }
        })
    );
}
```

### Step 3: Create UI Components

```typescript
// src/ui/snippet-panel.ts
export class SnippetPanel implements nexus.WebviewViewProvider {
    constructor(private context: nexus.ExtensionContext) {}
    
    resolveWebviewView(
        webviewView: nexus.WebviewView,
        context: nexus.WebviewViewResolveContext,
        token: nexus.CancellationToken
    ) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.context.extensionUri]
        };
        
        webviewView.webview.html = this.getHtmlContent(webviewView.webview);
        
        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'insertSnippet':
                    await insertSnippet(message.snippetId);
                    break;
                case 'createSnippet':
                    await this.createNewSnippet();
                    break;
            }
        });
    }
    
    private getHtmlContent(webview: nexus.Webview): string {
        return `<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                .snippet-item {
                    padding: 10px;
                    cursor: pointer;
                    border-bottom: 1px solid var(--nexus-border);
                }
                .snippet-item:hover {
                    background: var(--nexus-hover);
                }
            </style>
        </head>
        <body>
            <div id="snippet-list"></div>
            <button onclick="createSnippet()">Create New Snippet</button>
            <script>
                const vscode = acquireVsCodeApi();
                
                function insertSnippet(id) {
                    vscode.postMessage({
                        command: 'insertSnippet',
                        snippetId: id
                    });
                }
                
                function createSnippet() {
                    vscode.postMessage({
                        command: 'createSnippet'
                    });
                }
            </script>
        </body>
        </html>`;
    }
}
```

## Extension Points

### Commands

Register commands that users can execute:

```typescript
nexus.commands.registerCommand('myPlugin.greet', async () => {
    const name = await nexus.window.showInputBox({
        prompt: 'What is your name?',
        placeHolder: 'John Doe'
    });
    
    if (name) {
        nexus.window.showInformationMessage(`Hello, ${name}!`);
    }
});
```

### Language Support

Add support for new languages:

```typescript
// Register language configuration
nexus.languages.registerLanguageConfiguration('mylang', {
    comments: {
        lineComment: '//',
        blockComment: ['/*', '*/']
    },
    brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')']
    ],
    autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" }
    ]
});

// Register language server
const serverModule = context.asAbsolutePath('server/out/server.js');
const serverOptions: ServerOptions = {
    run: { module: serverModule, transport: TransportKind.ipc },
    debug: { module: serverModule, transport: TransportKind.ipc }
};

const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: 'file', language: 'mylang' }]
};

const client = new LanguageClient(
    'mylangLanguageServer',
    'MyLang Language Server',
    serverOptions,
    clientOptions
);

client.start();
```

### Themes

Create custom themes:

```json
{
  "contributes": {
    "themes": [{
      "label": "My Awesome Theme",
      "uiTheme": "vs-dark",
      "path": "./themes/awesome-dark.json"
    }]
  }
}
```

### Debugging

Add debugger support:

```typescript
nexus.debug.registerDebugAdapterDescriptorFactory('mylang', {
    createDebugAdapterDescriptor(session: DebugSession): DebugAdapterDescriptor {
        return new DebugAdapterServer(4711);
    }
});

nexus.debug.registerDebugConfigurationProvider('mylang', {
    resolveDebugConfiguration(folder, config) {
        if (!config.type && !config.request && !config.name) {
            const editor = nexus.window.activeTextEditor;
            if (editor && editor.document.languageId === 'mylang') {
                config.type = 'mylang';
                config.name = 'Launch';
                config.request = 'launch';
                config.program = '${file}';
                config.stopOnEntry = true;
            }
        }
        return config;
    }
});
```

## API Reference

### Core APIs

#### Window API
```typescript
// Show messages
nexus.window.showInformationMessage('Hello World!');
nexus.window.showWarningMessage('Warning!');
nexus.window.showErrorMessage('Error occurred!');

// Input boxes
const input = await nexus.window.showInputBox({
    prompt: 'Enter your name',
    value: 'default value',
    validateInput: (value) => {
        return value.length < 3 ? 'Too short!' : null;
    }
});

// Quick pick
const selected = await nexus.window.showQuickPick(['Option 1', 'Option 2'], {
    placeHolder: 'Select an option'
});

// Progress
await nexus.window.withProgress({
    location: nexus.ProgressLocation.Notification,
    title: "Processing...",
    cancellable: true
}, async (progress, token) => {
    progress.report({ increment: 0 });
    // Do work
    progress.report({ increment: 50, message: "Half way there..." });
    // More work
    progress.report({ increment: 50 });
});
```

#### Workspace API
```typescript
// Get workspace folders
const folders = nexus.workspace.workspaceFolders;

// Watch for file changes
const watcher = nexus.workspace.createFileSystemWatcher('**/*.js');
watcher.onDidCreate(uri => console.log('File created:', uri));
watcher.onDidChange(uri => console.log('File changed:', uri));
watcher.onDidDelete(uri => console.log('File deleted:', uri));

// Find files
const files = await nexus.workspace.findFiles('**/*.ts', '**/node_modules/**');

// Read/write files
const doc = await nexus.workspace.openTextDocument(uri);
const content = doc.getText();
await nexus.workspace.fs.writeFile(uri, Buffer.from('new content'));
```

#### Configuration API
```typescript
// Get configuration
const config = nexus.workspace.getConfiguration('myPlugin');
const enabled = config.get<boolean>('enableFeature', true);

// Update configuration
await config.update('enableFeature', false, nexus.ConfigurationTarget.Global);

// Listen for changes
nexus.workspace.onDidChangeConfiguration(e => {
    if (e.affectsConfiguration('myPlugin.enableFeature')) {
        // React to change
    }
});
```

## Voice Command Integration

### Advanced Voice Commands

```typescript
// Context-aware voice commands
nexus.voice.registerCommand({
    phrase: "refactor this {refactorType}",
    parameters: {
        refactorType: {
            type: 'enum',
            values: ['function', 'class', 'variable', 'method']
        }
    },
    when: 'editorHasSelection',
    handler: async (args, context) => {
        const selection = context.editor.selection;
        const text = context.editor.document.getText(selection);
        
        switch (args.refactorType) {
            case 'function':
                await refactorFunction(text, selection);
                break;
            case 'class':
                await refactorClass(text, selection);
                break;
            // ...
        }
    }
});

// Multi-language support
nexus.voice.registerCommand({
    phrase: {
        en: "create new file",
        es: "crear nuevo archivo",
        fr: "créer un nouveau fichier"
    },
    handler: async () => {
        await nexus.commands.executeCommand('workbench.action.files.newUntitledFile');
    }
});
```

### Voice Feedback

```typescript
// Provide voice feedback
nexus.voice.speak("File created successfully");

// With different voices
nexus.voice.speak("Operation completed", {
    voice: 'assistant',
    rate: 1.2,
    pitch: 1.0
});
```

## AI Model Integration

### Custom AI Models

```typescript
// Register custom AI model
nexus.ai.registerModel({
    id: 'myPlugin.customModel',
    name: 'My Custom Model',
    type: 'completion',
    endpoint: 'https://api.myservice.com/complete',
    authentication: {
        type: 'bearer',
        token: process.env.MY_API_KEY
    }
});

// Use custom model
const completion = await nexus.ai.complete({
    model: 'myPlugin.customModel',
    prompt: 'Generate a function that...',
    maxTokens: 150,
    temperature: 0.7
});
```

### AI-Powered Features

```typescript
// Code suggestions
nexus.languages.registerInlineCompletionItemProvider('javascript', {
    async provideInlineCompletionItems(document, position, context, token) {
        const linePrefix = document.lineAt(position).text.substr(0, position.character);
        
        if (shouldSuggest(linePrefix)) {
            const suggestion = await nexus.ai.complete({
                prompt: getPromptFromContext(document, position),
                maxTokens: 50
            });
            
            return [{
                text: suggestion,
                range: new nexus.Range(position, position)
            }];
        }
        return [];
    }
});
```

## UI Components

### Custom Views

```typescript
// Register tree view
class MyTreeDataProvider implements nexus.TreeDataProvider<MyTreeItem> {
    getTreeItem(element: MyTreeItem): nexus.TreeItem {
        return element;
    }
    
    getChildren(element?: MyTreeItem): MyTreeItem[] {
        if (!element) {
            return this.getRootItems();
        }
        return element.children;
    }
}

const treeDataProvider = new MyTreeDataProvider();
nexus.window.createTreeView('myPlugin.treeView', {
    treeDataProvider,
    showCollapseAll: true
});
```

### Status Bar

```typescript
// Create status bar item
const statusBarItem = nexus.window.createStatusBarItem(
    nexus.StatusBarAlignment.Right,
    100
);
statusBarItem.text = '$(check) Ready';
statusBarItem.tooltip = 'My Plugin Status';
statusBarItem.command = 'myPlugin.showStatus';
statusBarItem.show();
```

### Custom Editors

```typescript
// Register custom editor
nexus.window.registerCustomEditorProvider('myPlugin.customEditor', {
    async openCustomDocument(uri, openContext, token) {
        const data = await nexus.workspace.fs.readFile(uri);
        return new MyCustomDocument(uri, data);
    },
    
    async resolveCustomEditor(document, webviewPanel, token) {
        webviewPanel.webview.options = {
            enableScripts: true
        };
        
        webviewPanel.webview.html = getEditorHtml(document);
        
        // Handle save
        webviewPanel.webview.onDidReceiveMessage(async e => {
            if (e.type === 'save') {
                await document.save(e.data);
            }
        });
    }
});
```

## Testing Plugins

### Unit Testing

```typescript
// tests/extension.test.ts
import * as assert from 'assert';
import * as nexus from '@nexus-mind/sdk';
import * as myExtension from '../src/extension';

suite('Extension Test Suite', () => {
    nexus.window.showInformationMessage('Start all tests.');
    
    test('Sample test', async () => {
        const result = await myExtension.doSomething();
        assert.strictEqual(result, 'expected value');
    });
    
    test('Command registration', async () => {
        const commands = await nexus.commands.getCommands();
        assert.ok(commands.includes('myPlugin.doSomething'));
    });
});
```

### Integration Testing

```typescript
// tests/integration.test.ts
suite('Integration Test Suite', () => {
    test('Full workflow test', async () => {
        // Create test file
        const uri = nexus.Uri.file('/tmp/test.js');
        await nexus.workspace.fs.writeFile(uri, Buffer.from('console.log("test");'));
        
        // Open file
        const doc = await nexus.workspace.openTextDocument(uri);
        await nexus.window.showTextDocument(doc);
        
        // Execute command
        await nexus.commands.executeCommand('myPlugin.format');
        
        // Verify result
        const formatted = doc.getText();
        assert.ok(formatted.includes('formatted'));
        
        // Cleanup
        await nexus.workspace.fs.delete(uri);
    });
});
```

### Debugging Plugins

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [{
        "name": "Run Extension",
        "type": "extensionHost",
        "request": "launch",
        "args": [
            "--extensionDevelopmentPath=${workspaceFolder}"
        ],
        "outFiles": [
            "${workspaceFolder}/out/**/*.js"
        ],
        "preLaunchTask": "${defaultBuildTask}"
    }]
}
```

## Publishing Plugins

### Prepare for Publishing

1. **Update Metadata**
   ```json
   {
     "publisher": "your-publisher-id",
     "repository": {
       "type": "git",
       "url": "https://github.com/you/your-plugin"
     },
     "icon": "resources/icon.png",
     "galleryBanner": {
       "color": "#5c2d91",
       "theme": "dark"
     },
     "keywords": ["nexus", "ai", "productivity"]
   }
   ```

2. **Create README**
   - Features overview
   - Installation instructions
   - Usage examples
   - Configuration options
   - Known issues

3. **Add CHANGELOG**
   ```markdown
   # Change Log
   
   ## [1.0.0] - 2024-01-15
   ### Added
   - Initial release
   - Voice command support
   - Custom snippets
   ```

### Build and Package

```bash
# Build plugin
npm run compile

# Package plugin
nexus-sdk package

# This creates: my-awesome-plugin-1.0.0.nexuspkg
```

### Publish to Marketplace

```bash
# Login to publisher account
nexus-sdk login

# Publish plugin
nexus-sdk publish

# Or publish specific version
nexus-sdk publish 1.0.0
```

### Automated Publishing

```yaml
# .github/workflows/publish.yml
name: Publish Plugin
on:
  push:
    tags:
      - v*
      
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v1
        with:
          node-version: 16
      - run: npm ci
      - run: npm run compile
      - run: npm test
      - run: nexus-sdk publish
        env:
          NEXUS_TOKEN: ${{ secrets.NEXUS_TOKEN }}
```

## Best Practices

### Performance

1. **Lazy Loading**: Load resources only when needed
2. **Debouncing**: Throttle frequent operations
3. **Caching**: Cache expensive computations
4. **Async Operations**: Don't block the UI thread

### Security

1. **Input Validation**: Always validate user input
2. **Secure Storage**: Use NEXUS's secure storage API for secrets
3. **Permissions**: Request only necessary permissions
4. **Updates**: Keep dependencies updated

### User Experience

1. **Progress Indication**: Show progress for long operations
2. **Error Handling**: Provide helpful error messages
3. **Customization**: Allow users to configure behavior
4. **Documentation**: Include comprehensive docs

### Code Quality

1. **TypeScript**: Use TypeScript for better type safety
2. **Linting**: Follow NEXUS coding standards
3. **Testing**: Maintain good test coverage
4. **Logging**: Add appropriate logging for debugging

Remember: Great plugins enhance NEXUS without overwhelming users. Focus on solving real problems elegantly!