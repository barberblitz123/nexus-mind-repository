# NEXUS API Reference

Comprehensive API documentation for NEXUS development. This reference covers all public APIs available for plugin development and integration.

## Table of Contents
- [Core APIs](#core-apis)
- [Window API](#window-api)
- [Workspace API](#workspace-api)
- [Editor API](#editor-api)
- [Language API](#language-api)
- [Debug API](#debug-api)
- [Voice API](#voice-api)
- [AI API](#ai-api)
- [Extension API](#extension-api)
- [Event API](#event-api)
- [Command API](#command-api)
- [Types Reference](#types-reference)

## Core APIs

### nexus namespace

The main entry point for all NEXUS APIs.

```typescript
import * as nexus from '@nexus-mind/sdk';
```

### Version Information

```typescript
// Get NEXUS version
const version: string = nexus.version;

// Check minimum version
if (nexus.version.compare('2.0.0') >= 0) {
    // Use v2 features
}
```

### Environment

```typescript
// Get environment information
const env: Environment = nexus.env;

interface Environment {
    appName: string;          // "NEXUS"
    appRoot: string;          // Application root directory
    language: string;         // UI language (e.g., "en-US")
    machineId: string;        // Unique machine identifier
    sessionId: string;        // Current session ID
    isNewAppInstall: boolean; // First run after installation
    isTelemetryEnabled: boolean;
    shell: string;           // Default shell
    uiKind: UIKind;         // Desktop or Web
}

enum UIKind {
    Desktop = 1,
    Web = 2
}
```

## Window API

### Messages and Notifications

```typescript
// Information message
nexus.window.showInformationMessage('Operation completed!');

// With actions
const selection = await nexus.window.showInformationMessage(
    'File saved successfully',
    'Open File',
    'Close'
);
if (selection === 'Open File') {
    // Handle action
}

// Warning message
nexus.window.showWarningMessage('This action cannot be undone');

// Error message
nexus.window.showErrorMessage('Failed to save file');

// With detailed error
nexus.window.showErrorMessage('Compilation failed', {
    detail: 'Syntax error on line 42',
    modal: true
});
```

### Input and Selection

```typescript
// Input box
const name = await nexus.window.showInputBox({
    prompt: 'Enter your name',
    placeHolder: 'John Doe',
    value: 'Default',
    ignoreFocusOut: true,
    password: false,
    validateInput: (value: string) => {
        if (value.length < 3) {
            return 'Name must be at least 3 characters';
        }
        return null;
    }
});

// Quick pick (single selection)
const fruit = await nexus.window.showQuickPick(
    ['Apple', 'Banana', 'Orange'],
    {
        placeHolder: 'Select a fruit',
        canPickMany: false,
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    }
);

// Quick pick (multiple selection)
const languages = await nexus.window.showQuickPick(
    [
        { label: 'JavaScript', description: 'JS/TS files', picked: true },
        { label: 'Python', description: 'PY files' },
        { label: 'Java', description: 'JAVA files' }
    ],
    {
        placeHolder: 'Select languages',
        canPickMany: true
    }
);

// Quick pick with custom items
interface MyQuickPickItem extends nexus.QuickPickItem {
    id: string;
    data: any;
}

const items: MyQuickPickItem[] = [
    {
        label: '$(file) Document.txt',
        description: 'Text file',
        detail: 'Modified 2 hours ago',
        id: 'doc1',
        data: { size: 1024 }
    }
];
```

### Progress Indication

```typescript
// Simple progress
nexus.window.withProgress({
    location: nexus.ProgressLocation.Notification,
    title: "Processing files...",
    cancellable: true
}, async (progress, token) => {
    // Check for cancellation
    token.onCancellationRequested(() => {
        console.log("User canceled the operation");
    });
    
    // Report progress
    progress.report({ increment: 0, message: "Starting..." });
    
    for (let i = 0; i < 100; i++) {
        if (token.isCancellationRequested) {
            break;
        }
        
        await doWork();
        progress.report({ 
            increment: 1, 
            message: `Processing ${i + 1} of 100` 
        });
    }
});

// Window progress (in status bar)
nexus.window.withProgress({
    location: nexus.ProgressLocation.Window,
    title: "Loading project"
}, async (progress) => {
    progress.report({ message: "Resolving dependencies..." });
    await resolveDependencies();
    
    progress.report({ message: "Building..." });
    await build();
});
```

### Output Channels

```typescript
// Create output channel
const output = nexus.window.createOutputChannel('My Plugin');

// Write to output
output.appendLine('Starting process...');
output.append('Processing: ');
output.appendLine('Done!');

// Show output panel
output.show(true); // true = preserve focus

// Clear output
output.clear();

// Dispose when done
output.dispose();
```

### Status Bar

```typescript
// Create status bar item
const item = nexus.window.createStatusBarItem(
    nexus.StatusBarAlignment.Left,
    100 // priority
);

// Configure item
item.text = '$(sync~spin) Syncing...';
item.tooltip = 'Synchronizing with server';
item.color = '#00FF00';
item.backgroundColor = new nexus.ThemeColor('statusBarItem.errorBackground');
item.command = {
    command: 'myPlugin.showSyncStatus',
    arguments: ['arg1', 'arg2']
};

// Show/hide
item.show();
item.hide();

// Dispose when done
item.dispose();
```

### Terminals

```typescript
// Create terminal
const terminal = nexus.window.createTerminal({
    name: 'My Terminal',
    cwd: '/path/to/directory',
    env: { MY_VAR: 'value' },
    shellPath: '/bin/bash',
    shellArgs: ['-l'],
    iconPath: new nexus.ThemeIcon('terminal')
});

// Send text to terminal
terminal.sendText('npm install');
terminal.sendText('npm start', true); // true = add newline

// Show terminal
terminal.show(true); // true = preserve focus

// Listen to terminal events
nexus.window.onDidOpenTerminal((terminal: Terminal) => {
    console.log(`Terminal opened: ${terminal.name}`);
});

nexus.window.onDidCloseTerminal((terminal: Terminal) => {
    console.log(`Terminal closed: ${terminal.name}`);
});

// Get active terminal
const activeTerminal = nexus.window.activeTerminal;

// Get all terminals
const terminals = nexus.window.terminals;
```

## Workspace API

### Workspace Information

```typescript
// Get workspace folders
const folders = nexus.workspace.workspaceFolders;
if (folders) {
    folders.forEach(folder => {
        console.log(`Folder: ${folder.name} at ${folder.uri.fsPath}`);
    });
}

// Get workspace root (first folder)
const root = nexus.workspace.rootPath;

// Workspace name
const name = nexus.workspace.name;

// Check if file is in workspace
const isInWorkspace = nexus.workspace.getWorkspaceFolder(fileUri);
```

### File System Operations

```typescript
// Read file
const fileUri = nexus.Uri.file('/path/to/file.txt');
const fileData = await nexus.workspace.fs.readFile(fileUri);
const content = Buffer.from(fileData).toString('utf8');

// Write file
const encoder = new TextEncoder();
await nexus.workspace.fs.writeFile(
    fileUri, 
    encoder.encode('Hello World')
);

// Create directory
await nexus.workspace.fs.createDirectory(nexus.Uri.file('/path/to/new/dir'));

// Delete file/directory
await nexus.workspace.fs.delete(fileUri, { recursive: true });

// Copy file
await nexus.workspace.fs.copy(
    sourceUri,
    targetUri,
    { overwrite: true }
);

// Rename/Move file
await nexus.workspace.fs.rename(
    oldUri,
    newUri,
    { overwrite: false }
);

// Check if file exists
try {
    await nexus.workspace.fs.stat(fileUri);
    // File exists
} catch {
    // File doesn't exist
}
```

### File Watching

```typescript
// Create file watcher
const watcher = nexus.workspace.createFileSystemWatcher(
    '**/*.js',
    false, // ignoreCreateEvents
    false, // ignoreChangeEvents
    false  // ignoreDeleteEvents
);

// Watch for events
watcher.onDidCreate((uri: Uri) => {
    console.log(`File created: ${uri.fsPath}`);
});

watcher.onDidChange((uri: Uri) => {
    console.log(`File changed: ${uri.fsPath}`);
});

watcher.onDidDelete((uri: Uri) => {
    console.log(`File deleted: ${uri.fsPath}`);
});

// Dispose watcher
watcher.dispose();
```

### Find Files

```typescript
// Find all TypeScript files
const files = await nexus.workspace.findFiles(
    '**/*.ts',
    '**/node_modules/**', // exclude pattern
    10 // max results
);

// Find with multiple includes/excludes
const configs = await nexus.workspace.findFiles(
    '{**/*.json,**/*.yaml,**/*.yml}',
    '{**/node_modules/**,**/.git/**}'
);
```

### Configuration

```typescript
// Get configuration
const config = nexus.workspace.getConfiguration('myPlugin');
const enabled = config.get<boolean>('enabled', true);
const settings = config.get<MySettings>('settings');

// Update configuration
await config.update('enabled', false, nexus.ConfigurationTarget.Global);
await config.update('enabled', true, nexus.ConfigurationTarget.Workspace);
await config.update('enabled', true, nexus.ConfigurationTarget.WorkspaceFolder);

// Inspect configuration
const inspection = config.inspect<boolean>('enabled');
console.log(inspection?.defaultValue);
console.log(inspection?.globalValue);
console.log(inspection?.workspaceValue);
console.log(inspection?.workspaceFolderValue);

// Listen for configuration changes
nexus.workspace.onDidChangeConfiguration((e: ConfigurationChangeEvent) => {
    if (e.affectsConfiguration('myPlugin')) {
        // Reload settings
    }
});
```

## Editor API

### Active Editor

```typescript
// Get active editor
const editor = nexus.window.activeTextEditor;
if (editor) {
    // Get document
    const document = editor.document;
    console.log(`Editing: ${document.fileName}`);
    
    // Get selection
    const selection = editor.selection;
    const text = document.getText(selection);
    
    // Get visible ranges
    const visibleRanges = editor.visibleRanges;
}

// Get all visible editors
const editors = nexus.window.visibleTextEditors;
```

### Text Editing

```typescript
// Make edits
const success = await editor.edit((editBuilder: TextEditorEdit) => {
    // Insert text
    editBuilder.insert(position, 'Hello World');
    
    // Replace text
    editBuilder.replace(range, 'New Text');
    
    // Delete text
    editBuilder.delete(range);
    
    // Multiple edits
    editBuilder.insert(new nexus.Position(0, 0), 'Start\n');
    editBuilder.insert(new nexus.Position(10, 0), 'End\n');
});

// Insert snippet
await editor.insertSnippet(new nexus.SnippetString(
    'function ${1:name}($2) {\n\t$0\n}'
));

// Complex snippet
const snippet = new nexus.SnippetString();
snippet.appendText('class ');
snippet.appendPlaceholder('Name');
snippet.appendText(' {\n\tconstructor(');
snippet.appendPlaceholder('params');
snippet.appendText(') {\n\t\t');
snippet.appendTabstop();
snippet.appendText('\n\t}\n}');
await editor.insertSnippet(snippet);
```

### Selections and Cursors

```typescript
// Single selection
editor.selection = new nexus.Selection(
    new nexus.Position(0, 0),
    new nexus.Position(0, 10)
);

// Multiple selections (multi-cursor)
editor.selections = [
    new nexus.Selection(0, 0, 0, 10),
    new nexus.Selection(1, 0, 1, 10),
    new nexus.Selection(2, 0, 2, 10)
];

// Reveal position in editor
editor.revealRange(
    new nexus.Range(10, 0, 10, 0),
    nexus.TextEditorRevealType.InCenter
);

// Set cursor position
const position = new nexus.Position(5, 10);
editor.selection = new nexus.Selection(position, position);
```

### Decorations

```typescript
// Create decoration type
const decorationType = nexus.window.createTextEditorDecorationType({
    backgroundColor: 'rgba(255,0,0,0.3)',
    border: '1px solid red',
    borderRadius: '2px',
    color: 'white',
    fontWeight: 'bold',
    overviewRulerColor: 'red',
    overviewRulerLane: nexus.OverviewRulerLane.Full,
    after: {
        contentText: ' ⚠️',
        color: 'red'
    }
});

// Apply decorations
const decorations: nexus.DecorationOptions[] = [
    {
        range: new nexus.Range(0, 0, 0, 10),
        hoverMessage: 'This is an error',
        renderOptions: {
            before: {
                contentText: '⚠️ '
            }
        }
    }
];

editor.setDecorations(decorationType, decorations);

// Remove decorations
editor.setDecorations(decorationType, []);

// Dispose decoration type
decorationType.dispose();
```

## Language API

### Language Configuration

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
        { open: '"', close: '"', notIn: ['string'] },
        { open: "'", close: "'", notIn: ['string', 'comment'] }
    ],
    surroundingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" }
    ],
    folding: {
        markers: {
            start: new RegExp("^\\s*//\\s*#region\\b"),
            end: new RegExp("^\\s*//\\s*#endregion\\b")
        }
    },
    wordPattern: /(-?\d*\.\d\w*)|([^\`\~\!\@\#\%\^\&\*\(\)\-\=\+\[\{\]\}\\\|\;\:\'\"\,\.\<\>\/\?\s]+)/g,
    indentationRules: {
        increaseIndentPattern: /^((?!\/).)*(\{[^}\"'`]*|\([^)\"'`]*|\[[^\]\"'`]*)$/,
        decreaseIndentPattern: /^((?!.*?\/\*).*\*/)?.*[\}\]\)].*$/
    }
});
```

### Completion Provider

```typescript
// Register completion provider
const provider = nexus.languages.registerCompletionItemProvider(
    'javascript',
    {
        provideCompletionItems(document, position, token, context) {
            // Create completion items
            const items: nexus.CompletionItem[] = [];
            
            // Simple completion
            const simpleCompletion = new nexus.CompletionItem('console');
            simpleCompletion.kind = nexus.CompletionItemKind.Module;
            items.push(simpleCompletion);
            
            // Complex completion
            const methodCompletion = new nexus.CompletionItem('log', nexus.CompletionItemKind.Method);
            methodCompletion.detail = 'Log message to console';
            methodCompletion.documentation = new nexus.MarkdownString('Outputs a message to the console');
            methodCompletion.insertText = new nexus.SnippetString('log(${1:message})');
            methodCompletion.sortText = '0';
            methodCompletion.filterText = 'log';
            methodCompletion.preselect = true;
            methodCompletion.command = {
                command: 'editor.action.triggerParameterHints',
                title: 'Trigger Parameter Hints'
            };
            items.push(methodCompletion);
            
            return items;
        },
        
        resolveCompletionItem(item, token) {
            // Resolve additional information
            if (item.label === 'console') {
                item.documentation = new nexus.MarkdownString('The console object provides access to debugging console');
            }
            return item;
        }
    },
    '.', // Trigger characters
    '('
);
```

### Hover Provider

```typescript
const hoverProvider = nexus.languages.registerHoverProvider('javascript', {
    provideHover(document, position, token) {
        const range = document.getWordRangeAtPosition(position);
        const word = document.getText(range);
        
        if (word === 'console') {
            const contents = new nexus.MarkdownString();
            contents.appendCodeblock('const console: Console', 'typescript');
            contents.appendMarkdown('\n\nThe `console` object provides debugging functionality');
            
            return new nexus.Hover(contents, range);
        }
        
        return undefined;
    }
});
```

### Definition Provider

```typescript
nexus.languages.registerDefinitionProvider('javascript', {
    provideDefinition(document, position, token) {
        const wordRange = document.getWordRangeAtPosition(position);
        const word = document.getText(wordRange);
        
        // Search for definition
        const definition = findDefinition(word);
        if (definition) {
            return new nexus.Location(
                nexus.Uri.file(definition.file),
                new nexus.Position(definition.line, definition.column)
            );
        }
        
        // Multiple definitions
        return [
            new nexus.Location(uri1, position1),
            new nexus.Location(uri2, position2)
        ];
    }
});
```

### Code Actions Provider

```typescript
nexus.languages.registerCodeActionsProvider('javascript', {
    provideCodeActions(document, range, context, token) {
        const actions: nexus.CodeAction[] = [];
        
        // Quick fix for diagnostics
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.code === 'no-var') {
                const fix = new nexus.CodeAction(
                    'Convert to let',
                    nexus.CodeActionKind.QuickFix
                );
                fix.edit = new nexus.WorkspaceEdit();
                fix.edit.replace(
                    document.uri,
                    diagnostic.range,
                    document.getText(diagnostic.range).replace('var', 'let')
                );
                fix.diagnostics = [diagnostic];
                actions.push(fix);
            }
        }
        
        // Refactoring action
        const refactor = new nexus.CodeAction(
            'Extract Method',
            nexus.CodeActionKind.RefactorExtract
        );
        refactor.command = {
            command: 'myPlugin.extractMethod',
            arguments: [document.uri, range]
        };
        actions.push(refactor);
        
        return actions;
    }
});
```

## Debug API

### Debug Configuration

```typescript
// Register debug configuration provider
nexus.debug.registerDebugConfigurationProvider('node', {
    resolveDebugConfiguration(folder, config, token) {
        // Fill in missing values
        if (!config.type) {
            config.type = 'node';
        }
        if (!config.request) {
            config.request = 'launch';
        }
        if (!config.name) {
            config.name = 'Launch Program';
        }
        if (!config.program) {
            config.program = '${file}';
        }
        
        return config;
    },
    
    provideDebugConfigurations(folder, token) {
        return [
            {
                type: 'node',
                request: 'launch',
                name: 'Launch Program',
                program: '${workspaceFolder}/index.js'
            },
            {
                type: 'node',
                request: 'attach',
                name: 'Attach to Process',
                port: 9229
            }
        ];
    }
});
```

### Debug Adapter

```typescript
// Register debug adapter
nexus.debug.registerDebugAdapterDescriptorFactory('mylang', {
    createDebugAdapterDescriptor(session, executable) {
        // Use executable
        return new nexus.DebugAdapterExecutable(
            '/path/to/debug-adapter',
            ['--port', '1234'],
            { env: { DEBUG: 'true' } }
        );
        
        // Use server
        return new nexus.DebugAdapterServer(1234, 'localhost');
        
        // Use inline implementation
        return new nexus.DebugAdapterInlineImplementation(new MyDebugAdapter());
    }
});
```

### Debug Session

```typescript
// Start debugging
const folder = nexus.workspace.workspaceFolders?.[0];
await nexus.debug.startDebugging(folder, 'Launch Program');

// Start with configuration
await nexus.debug.startDebugging(folder, {
    type: 'node',
    request: 'launch',
    name: 'Debug Script',
    program: '${workspaceFolder}/script.js',
    args: ['--verbose']
});

// Get active debug session
const session = nexus.debug.activeDebugSession;
if (session) {
    console.log(`Debugging: ${session.name}`);
    console.log(`Type: ${session.type}`);
}

// Custom request to debug adapter
await session.customRequest('evaluate', {
    expression: 'myVariable',
    frameId: 1
});

// Listen to debug events
nexus.debug.onDidStartDebugSession((session) => {
    console.log(`Started debugging: ${session.name}`);
});

nexus.debug.onDidTerminateDebugSession((session) => {
    console.log(`Stopped debugging: ${session.name}`);
});

nexus.debug.onDidChangeActiveDebugSession((session) => {
    console.log(`Active session: ${session?.name || 'none'}`);
});

// Breakpoints
nexus.debug.onDidChangeBreakpoints((event) => {
    event.added.forEach(bp => {
        console.log(`Breakpoint added at ${bp.location.uri}:${bp.location.range.start.line}`);
    });
    event.removed.forEach(bp => {
        console.log(`Breakpoint removed`);
    });
});
```

## Voice API

### Voice Commands

```typescript
// Register simple voice command
nexus.voice.registerCommand({
    phrase: 'open file',
    handler: async () => {
        await nexus.commands.executeCommand('workbench.action.files.openFile');
    }
});

// Voice command with parameters
nexus.voice.registerCommand({
    phrase: 'go to line {lineNumber}',
    parameters: {
        lineNumber: {
            type: 'number',
            min: 1,
            max: 10000
        }
    },
    handler: async (args) => {
        const editor = nexus.window.activeTextEditor;
        if (editor) {
            const position = new nexus.Position(args.lineNumber - 1, 0);
            editor.selection = new nexus.Selection(position, position);
            editor.revealRange(new nexus.Range(position, position));
        }
    }
});

// Context-aware voice command
nexus.voice.registerCommand({
    phrase: 'delete this {element}',
    parameters: {
        element: {
            type: 'enum',
            values: ['line', 'word', 'function', 'class', 'block']
        }
    },
    when: 'editorTextFocus',
    handler: async (args, context) => {
        const editor = context.editor;
        switch (args.element) {
            case 'line':
                await nexus.commands.executeCommand('editor.action.deleteLines');
                break;
            case 'word':
                await nexus.commands.executeCommand('deleteWordRight');
                break;
            // ... handle other cases
        }
    }
});

// Multi-language voice commands
nexus.voice.registerCommand({
    phrase: {
        en: 'save file',
        es: 'guardar archivo',
        fr: 'enregistrer le fichier',
        de: 'datei speichern'
    },
    handler: async () => {
        await nexus.commands.executeCommand('workbench.action.files.save');
    }
});
```

### Voice Recognition

```typescript
// Start voice recognition
const recognition = await nexus.voice.startRecognition({
    continuous: true,
    interimResults: true,
    language: 'en-US',
    maxAlternatives: 3
});

// Handle results
recognition.onResult((result) => {
    console.log(`Transcript: ${result.transcript}`);
    console.log(`Confidence: ${result.confidence}`);
    console.log(`Is final: ${result.isFinal}`);
    
    // Handle alternatives
    result.alternatives.forEach((alt, index) => {
        console.log(`Alternative ${index}: ${alt.transcript} (${alt.confidence})`);
    });
});

// Handle errors
recognition.onError((error) => {
    console.error(`Recognition error: ${error.message}`);
});

// Stop recognition
await recognition.stop();
```

### Text-to-Speech

```typescript
// Speak text
await nexus.voice.speak('Operation completed successfully');

// Speak with options
await nexus.voice.speak('Hello, how can I help you?', {
    voice: 'assistant',      // Voice selection
    rate: 1.0,              // Speech rate (0.1 - 10)
    pitch: 1.0,             // Pitch (0 - 2)
    volume: 1.0,            // Volume (0 - 1)
    language: 'en-US'       // Language
});

// Get available voices
const voices = await nexus.voice.getVoices();
voices.forEach(voice => {
    console.log(`${voice.name} (${voice.language})`);
});

// Stop speaking
nexus.voice.stopSpeaking();
```

## AI API

### Completion

```typescript
// Simple completion
const completion = await nexus.ai.complete({
    prompt: 'Write a function that calculates fibonacci numbers',
    maxTokens: 150,
    temperature: 0.7
});

console.log(completion.text);

// Completion with context
const contextualCompletion = await nexus.ai.complete({
    prompt: 'Complete this function',
    context: {
        language: 'javascript',
        currentFile: document.getText(),
        cursorPosition: position,
        imports: getImports(),
        symbols: getAvailableSymbols()
    },
    model: 'nexus-code-v2',
    maxTokens: 200,
    temperature: 0.3,
    topP: 0.95,
    stop: ['\n\n', 'function', 'class']
});
```

### Chat

```typescript
// Create chat session
const chat = await nexus.ai.createChat({
    model: 'nexus-chat',
    systemPrompt: 'You are a helpful coding assistant'
});

// Send message
const response = await chat.sendMessage('How do I sort an array in JavaScript?');
console.log(response.text);

// Continue conversation
const followUp = await chat.sendMessage('What about sorting objects by a property?');

// Stream response
await chat.streamMessage('Explain async/await in detail', {
    onToken: (token) => {
        process.stdout.write(token);
    },
    onComplete: (fullResponse) => {
        console.log('\nComplete response received');
    }
});

// Clear history
chat.clearHistory();

// Dispose session
chat.dispose();
```

### Code Analysis

```typescript
// Analyze code
const analysis = await nexus.ai.analyzeCode({
    code: functionCode,
    language: 'javascript',
    analyses: ['complexity', 'performance', 'security', 'quality']
});

console.log(`Complexity: ${analysis.complexity.score}`);
console.log(`Issues found: ${analysis.issues.length}`);

analysis.issues.forEach(issue => {
    console.log(`${issue.severity}: ${issue.message} at line ${issue.line}`);
});

// Get suggestions
const suggestions = await nexus.ai.suggestImprovements({
    code: functionCode,
    language: 'javascript',
    focus: ['performance', 'readability']
});

suggestions.forEach(suggestion => {
    console.log(`${suggestion.title}: ${suggestion.description}`);
    if (suggestion.example) {
        console.log(`Example:\n${suggestion.example}`);
    }
});
```

### Embeddings

```typescript
// Generate embeddings
const embedding = await nexus.ai.generateEmbedding({
    text: 'Function to calculate the area of a circle',
    model: 'nexus-embed'
});

console.log(`Embedding dimensions: ${embedding.values.length}`);

// Batch embeddings
const embeddings = await nexus.ai.generateEmbeddings({
    texts: [
        'Sort an array',
        'Filter array elements',
        'Map array values'
    ],
    model: 'nexus-embed'
});

// Find similar code
const similar = await nexus.ai.findSimilar({
    embedding: embedding,
    searchIn: 'workspace', // or 'project', 'file'
    limit: 10,
    threshold: 0.8
});

similar.forEach(match => {
    console.log(`${match.file}:${match.line} (similarity: ${match.score})`);
});
```

## Extension API

### Extension Context

```typescript
export function activate(context: nexus.ExtensionContext) {
    // Extension path
    const extensionPath = context.extensionPath;
    const resourcePath = context.asAbsolutePath('resources/icon.png');
    
    // Extension URI
    const extensionUri = context.extensionUri;
    const resourceUri = nexus.Uri.joinPath(extensionUri, 'resources', 'data.json');
    
    // Storage
    const globalState = context.globalState;
    const workspaceState = context.workspaceState;
    
    // Store data
    await globalState.update('myKey', 'myValue');
    const value = globalState.get<string>('myKey');
    
    // Secret storage
    await context.secrets.store('apiKey', 'secret-key-value');
    const apiKey = await context.secrets.get('apiKey');
    await context.secrets.delete('apiKey');
    
    // Environment
    const isDevelopment = context.extensionMode === nexus.ExtensionMode.Development;
    
    // Subscriptions
    context.subscriptions.push(
        nexus.commands.registerCommand(...),
        nexus.window.createStatusBarItem(...),
        // ... other disposables
    );
}
```

### Extension Management

```typescript
// Get extension
const myExtension = nexus.extensions.getExtension('publisher.extension-name');
if (myExtension) {
    console.log(`Version: ${myExtension.packageJSON.version}`);
    
    // Activate if needed
    if (!myExtension.isActive) {
        await myExtension.activate();
    }
    
    // Access exports
    const api = myExtension.exports;
    api.doSomething();
}

// Get all extensions
const allExtensions = nexus.extensions.all;
allExtensions.forEach(ext => {
    console.log(`${ext.id}: ${ext.isActive ? 'active' : 'inactive'}`);
});

// Extension events
nexus.extensions.onDidChange(() => {
    console.log('Extensions changed');
});
```

## Event API

### Event Emitter

```typescript
// Create event emitter
class MyClass {
    private _onDidChange = new nexus.EventEmitter<string>();
    readonly onDidChange = this._onDidChange.event;
    
    doSomething() {
        // Fire event
        this._onDidChange.fire('something changed');
    }
    
    dispose() {
        this._onDidChange.dispose();
    }
}

// Use events
const instance = new MyClass();
const disposable = instance.onDidChange((value) => {
    console.log(`Changed: ${value}`);
});

// Dispose listener
disposable.dispose();
```

### Cancellation

```typescript
// Create cancellation token
const tokenSource = new nexus.CancellationTokenSource();
const token = tokenSource.token;

// Check cancellation
async function longRunningOperation(token: nexus.CancellationToken) {
    for (let i = 0; i < 1000; i++) {
        if (token.isCancellationRequested) {
            throw new Error('Operation cancelled');
        }
        await doWork();
    }
}

// Cancel operation
setTimeout(() => {
    tokenSource.cancel();
}, 5000);

// Use in async operation
try {
    await longRunningOperation(token);
} catch (e) {
    if (e.message === 'Operation cancelled') {
        console.log('Operation was cancelled');
    }
}
```

## Command API

### Registering Commands

```typescript
// Simple command
const disposable = nexus.commands.registerCommand('myExtension.helloWorld', () => {
    nexus.window.showInformationMessage('Hello World!');
});

// Command with arguments
nexus.commands.registerCommand('myExtension.doSomething', (arg1: string, arg2: number) => {
    console.log(`Arguments: ${arg1}, ${arg2}`);
});

// Text editor command
nexus.commands.registerTextEditorCommand('myExtension.transformText', 
    (textEditor, edit, ...args) => {
        const selection = textEditor.selection;
        const text = textEditor.document.getText(selection);
        edit.replace(selection, text.toUpperCase());
    }
);
```

### Executing Commands

```typescript
// Execute command without arguments
await nexus.commands.executeCommand('workbench.action.files.save');

// Execute command with arguments
await nexus.commands.executeCommand('editor.action.insertSnippet', {
    snippet: 'console.log($1);$0'
});

// Get all commands
const allCommands = await nexus.commands.getCommands();
console.log(`Total commands: ${allCommands.length}`);

// Check if command exists
const commands = await nexus.commands.getCommands();
const exists = commands.includes('myExtension.myCommand');
```

## Types Reference

### Common Types

```typescript
// Position
class Position {
    readonly line: number;      // 0-based
    readonly character: number; // 0-based
    
    constructor(line: number, character: number);
    
    isAfter(other: Position): boolean;
    isAfterOrEqual(other: Position): boolean;
    isBefore(other: Position): boolean;
    isBeforeOrEqual(other: Position): boolean;
    isEqual(other: Position): boolean;
    
    compareTo(other: Position): number;
    translate(lineDelta?: number, characterDelta?: number): Position;
    translate(change: { lineDelta?: number; characterDelta?: number }): Position;
    
    with(line?: number, character?: number): Position;
    with(change: { line?: number; character?: number }): Position;
}

// Range
class Range {
    readonly start: Position;
    readonly end: Position;
    readonly isEmpty: boolean;
    readonly isSingleLine: boolean;
    
    constructor(start: Position, end: Position);
    constructor(startLine: number, startCharacter: number, endLine: number, endCharacter: number);
    
    contains(positionOrRange: Position | Range): boolean;
    isEqual(other: Range): boolean;
    intersection(range: Range): Range | undefined;
    union(other: Range): Range;
    
    with(start?: Position, end?: Position): Range;
    with(change: { start?: Position; end?: Position }): Range;
}

// Selection
class Selection extends Range {
    readonly anchor: Position;
    readonly active: Position;
    readonly isReversed: boolean;
    
    constructor(anchor: Position, active: Position);
    constructor(anchorLine: number, anchorCharacter: number, activeLine: number, activeCharacter: number);
}

// Uri
class Uri {
    static file(path: string): Uri;
    static parse(value: string, strict?: boolean): Uri;
    static joinPath(base: Uri, ...pathSegments: string[]): Uri;
    
    readonly scheme: string;
    readonly authority: string;
    readonly path: string;
    readonly query: string;
    readonly fragment: string;
    readonly fsPath: string;
    
    toString(skipEncoding?: boolean): string;
    toJSON(): any;
    
    with(change: {
        scheme?: string;
        authority?: string;
        path?: string;
        query?: string;
        fragment?: string;
    }): Uri;
}

// Location
class Location {
    readonly uri: Uri;
    readonly range: Range;
    
    constructor(uri: Uri, rangeOrPosition: Range | Position);
}

// Diagnostic
class Diagnostic {
    range: Range;
    message: string;
    source?: string;
    severity: DiagnosticSeverity;
    code?: string | number;
    relatedInformation?: DiagnosticRelatedInformation[];
    tags?: DiagnosticTag[];
    
    constructor(range: Range, message: string, severity?: DiagnosticSeverity);
}

enum DiagnosticSeverity {
    Error = 0,
    Warning = 1,
    Information = 2,
    Hint = 3
}

enum DiagnosticTag {
    Unnecessary = 1,
    Deprecated = 2
}
```

### Workspace Types

```typescript
interface WorkspaceFolder {
    readonly uri: Uri;
    readonly name: string;
    readonly index: number;
}

interface WorkspaceConfiguration {
    get<T>(section: string): T | undefined;
    get<T>(section: string, defaultValue: T): T;
    has(section: string): boolean;
    inspect<T>(section: string): ConfigurationInspection<T> | undefined;
    update(section: string, value: any, configurationTarget?: ConfigurationTarget | boolean): Thenable<void>;
}

enum ConfigurationTarget {
    Global = 1,
    Workspace = 2,
    WorkspaceFolder = 3
}

interface ConfigurationChangeEvent {
    affectsConfiguration(section: string, scope?: Uri): boolean;
}
```

### Extension Types

```typescript
interface Extension<T> {
    readonly id: string;
    readonly extensionUri: Uri;
    readonly extensionPath: string;
    readonly isActive: boolean;
    readonly packageJSON: any;
    readonly exports?: T;
    activate(): Thenable<T>;
}

interface ExtensionContext {
    readonly subscriptions: { dispose(): any }[];
    readonly extensionUri: Uri;
    readonly extensionPath: string;
    readonly extensionMode: ExtensionMode;
    readonly globalState: Memento;
    readonly workspaceState: Memento;
    readonly secrets: SecretStorage;
    readonly storageUri: Uri | undefined;
    readonly globalStorageUri: Uri;
    readonly logUri: Uri;
    
    asAbsolutePath(relativePath: string): string;
}

enum ExtensionMode {
    Production = 1,
    Development = 2,
    Test = 3
}

interface Memento {
    get<T>(key: string): T | undefined;
    get<T>(key: string, defaultValue: T): T;
    update(key: string, value: any): Thenable<void>;
}
```

This API reference provides the foundation for building powerful NEXUS extensions. For more examples and tutorials, see the [Plugin Development Guide](plugin-development.md).