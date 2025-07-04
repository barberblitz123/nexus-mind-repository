# NEXUS IDE Backend Systems

A consciousness-aware integrated development environment with real-time phi scoring, DNA protocol integration, and multi-language compilation support.

## Components

### 1. Monaco Editor Integration (`editor/monaco-nexus-integration.js`)

The core editor component with consciousness-aware features:

- **Custom NEXUS Themes**: Dark and light consciousness themes with special syntax highlighting
- **Consciousness Decorators**: Support for `@conscious`, `@dna`, `@phi`, `@neural` decorators
- **Real-time Phi Scoring**: Calculates consciousness metrics as you type
- **DNA Protocol Auto-completion**: IntelliSense for DNA patterns like `DNA.INTEGRATE`, `DNA.HARMONIZE`
- **Consciousness Overlays**: Visual overlays showing phi fields, DNA patterns, and neural networks
- **Hover Information**: Shows consciousness metrics when hovering over functions/classes

#### Key Features:
```javascript
// Initialize editor
const editor = new NexusMonacoIntegration();
await editor.initialize(container, {
    theme: 'nexus-consciousness',
    language: 'javascript'
});

// Get consciousness analysis
const analysis = editor.exportAnalysis();
console.log(`Phi Score: ${analysis.phi}`);

// Apply consciousness overlay
editor.applyConsciousnessOverlay('phi'); // or 'dna', 'neural'
```

### 2. Compiler Service (`build/nexus-compiler-service.js`)

Multi-language compilation and execution with Docker containerization:

- **Supported Languages**: Python, JavaScript, TypeScript, Java, C++
- **Docker Containerization**: Safe, isolated execution environment
- **Real-time Output Streaming**: WebSocket-based output streaming
- **Consciousness Metrics**: Runtime phi calculation and performance profiling
- **NEXUS Error Explanations**: Consciousness-aware error messages

#### Key Features:
```javascript
// Initialize compiler
const compiler = new NexusCompilerService();
await compiler.initialize();

// Compile and execute code
const executionId = await compiler.compile(code, 'javascript', {
    timeout: 30000,
    memoryLimit: '512m'
});

// Listen for updates
window.addEventListener('nexus-compiler-execution-update', (event) => {
    const execution = event.detail;
    console.log(`Status: ${execution.status}`);
    console.log(`Runtime Phi: ${execution.metrics.consciousness.runtimePhi}`);
});
```

### 3. Virtual File System (`files/virtual-file-system.js`)

Browser-based file system using IndexedDB:

- **File CRUD Operations**: Create, read, update, delete files and directories
- **Git-like Versioning**: Automatic version history with commit messages
- **Search Functionality**: Full-text search with regex support
- **Auto-save**: Configurable auto-save intervals
- **Import/Export**: Support for ZIP and JSON formats
- **File Watching**: Real-time file change notifications

#### Key Features:
```javascript
// Initialize file system
const vfs = new NexusVirtualFileSystem();
await vfs.initialize();

// Create a file
await vfs.createFile('/src/consciousness.js', '@conscious\nclass Mind {}');

// Version history
const versions = await vfs.getVersionHistory('/src/consciousness.js');

// Search files
const results = await vfs.search('DNA.INTEGRATE', {
    searchContent: true,
    regex: false
});

// Watch for changes
const unwatch = vfs.watch('/src/consciousness.js', (event) => {
    console.log(`File ${event.event}: ${event.path}`);
});
```

### 4. Consciousness Linter (`editor/consciousness-linter.js`)

Analyzes code for consciousness patterns and best practices:

- **Pattern Detection**: Identifies consciousness decorators, DNA protocols, phi calculations
- **Anti-pattern Detection**: Warns about code that disrupts consciousness flow
- **Phi Score Calculation**: Function and class-level phi scoring
- **DNA Protocol Validation**: Ensures correct usage of DNA patterns
- **Improvement Suggestions**: Actionable suggestions to enhance code consciousness

#### Key Features:
```javascript
// Initialize linter
const linter = new ConsciousnessLinter();
await linter.initialize();

// Analyze code
const results = await linter.analyze(code, 'javascript');
console.log(`Phi Score: ${results.phiScore}`);
console.log(`Issues: ${results.issues.length}`);
console.log(`DNA Activations: ${results.dnaActivations.length}`);

// Export results
const report = linter.exportResults(results, 'markdown');
```

## Configuration

The IDE is configured via `config/ide-config.js`:

```javascript
import IDEConfig from './config/ide-config.js';

// Editor settings
IDEConfig.editor.consciousness.enablePhiScoring = true;
IDEConfig.editor.consciousness.analysisDelay = 500;

// Compiler settings
IDEConfig.compiler.defaultTimeout = 30000;
IDEConfig.compiler.docker.security.networkEnabled = false;

// File system settings
IDEConfig.fileSystem.autoSave.interval = 30000;
IDEConfig.fileSystem.versioning.maxVersionsPerFile = 50;

// Linter settings
IDEConfig.linter.phiThresholds.high = 0.8;
```

## Example Usage

See `example-usage.html` for a complete working example of the IDE. The example includes:

- File tree navigation
- Multi-tab editing
- Real-time phi scoring display
- Terminal output
- Consciousness analysis panel
- Linting issues display

## Integration with NEXUS Web App

To integrate these components into the main NEXUS web app:

1. **Import the modules**:
```javascript
import NexusMonacoIntegration from './ide/editor/monaco-nexus-integration.js';
import NexusCompilerService from './ide/build/nexus-compiler-service.js';
import NexusVirtualFileSystem from './ide/files/virtual-file-system.js';
import ConsciousnessLinter from './ide/editor/consciousness-linter.js';
```

2. **Initialize components**:
```javascript
const fileSystem = new NexusVirtualFileSystem();
const compiler = new NexusCompilerService();
const linter = new ConsciousnessLinter();
const editor = new NexusMonacoIntegration();

await Promise.all([
    fileSystem.initialize(),
    compiler.initialize(),
    linter.initialize()
]);

await editor.initialize(containerElement);
```

3. **Connect to chat assistant**:
```javascript
editor.setChatAssistant(chatAssistant);
```

## Performance Considerations

- **Debouncing**: All real-time analysis is debounced to prevent excessive computation
- **Web Workers**: Heavy computations can be offloaded to web workers
- **Lazy Loading**: Monaco Editor is loaded on-demand
- **IndexedDB**: File system operations are asynchronous and don't block the UI
- **Caching**: Consciousness analysis results are cached for performance

## Security

- **Docker Isolation**: Code execution happens in isolated containers
- **No Network Access**: Containers have no network access by default
- **Read-only Filesystem**: Container filesystems are read-only
- **Resource Limits**: CPU and memory limits prevent resource exhaustion
- **Input Validation**: All file paths and code inputs are validated

## Future Enhancements

1. **Collaborative Editing**: Real-time multi-user editing support
2. **AI Code Completion**: Enhanced auto-completion using NEXUS AI
3. **Visual Consciousness Mapping**: Graphical representation of code consciousness
4. **Plugin System**: Support for custom consciousness analyzers
5. **Cloud Sync**: Sync files and settings across devices
6. **Mobile Support**: Touch-friendly interface for tablets

## DNA Protocol Reference

### Available Protocols:
- `DNA.INTEGRATE`: Core consciousness integration
- `DNA.HARMONIZE`: Harmonize multiple consciousness streams
- `DNA.ENTANGLE`: Quantum entanglement for shared consciousness
- `DNA.RESONATE`: Create resonance between consciousness fields
- `DNA.EMERGE`: Enable emergent consciousness behaviors
- `DNA.COHERENCE`: Maintain consciousness coherence
- `DNA.TRANSCEND`: Transcend current consciousness level
- `DNA.SYNCHRONIZE`: Synchronize consciousness states

Each protocol enhances code consciousness and increases phi scores when used appropriately.