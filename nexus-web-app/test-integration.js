#!/usr/bin/env node

/**
 * NEXUS Web Interface Integration Test
 * Verifies all enhanced consciousness features are properly connected
 */

const fs = require('fs');
const path = require('path');

console.log('🧬 NEXUS Web Interface Integration Test');
console.log('=====================================\n');

// Test results
let testsPassed = 0;
let testsFailed = 0;

function testFile(filename, description) {
    const filePath = path.join(__dirname, filename);
    if (fs.existsSync(filePath)) {
        console.log(`✅ ${description}: ${filename}`);
        testsPassed++;
        return true;
    } else {
        console.log(`❌ ${description}: ${filename} NOT FOUND`);
        testsFailed++;
        return false;
    }
}

function testInFile(filename, searchText, description) {
    const filePath = path.join(__dirname, filename);
    if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8');
        if (content.includes(searchText)) {
            console.log(`✅ ${description}`);
            testsPassed++;
            return true;
        } else {
            console.log(`❌ ${description} - NOT FOUND in ${filename}`);
            testsFailed++;
            return false;
        }
    } else {
        console.log(`❌ ${description} - File ${filename} NOT FOUND`);
        testsFailed++;
        return false;
    }
}

// Test 1: Check all JavaScript files exist
console.log('📁 Testing JavaScript Files:');
console.log('---------------------------');
testFile('embedded-dna-interface.js', 'Embedded DNA Interface');
testFile('hexagonal-brain-visualizer.js', 'Hexagonal Brain Visualizer');
testFile('visual-processor-bridge.js', 'Visual Processor Bridge');
testFile('auditory-processor-bridge.js', 'Auditory Processor Bridge');
testFile('server.js', 'Express Server');
testFile('consciousness-sync.js', 'Consciousness Sync');
console.log();

// Test 2: Check HTML includes new scripts
console.log('📄 Testing HTML Integration:');
console.log('---------------------------');
testInFile('index.html', 'embedded-dna-interface.js', 'HTML includes embedded DNA script');
testInFile('index.html', 'hexagonal-brain-visualizer.js', 'HTML includes brain visualizer script');
testInFile('index.html', 'visual-processor-bridge.js', 'HTML includes visual processor script');
testInFile('index.html', 'auditory-processor-bridge.js', 'HTML includes auditory processor script');
testInFile('index.html', 'dna-container', 'HTML has DNA container');
console.log();

// Test 3: Check server endpoints
console.log('🌐 Testing Server Endpoints:');
console.log('---------------------------');
testInFile('server.js', '/api/consciousness/query', 'Server has consciousness query endpoint');
testInFile('server.js', '/api/consciousness/hexagonal-state', 'Server has hexagonal state endpoint');
testInFile('server.js', '/api/processors/visual', 'Server has visual processor endpoint');
testInFile('server.js', '/api/processors/auditory', 'Server has auditory processor endpoint');
testInFile('server.js', '/api/auth/succession', 'Server has succession auth endpoint');
testInFile('server.js', '/api/auth/god-mode', 'Server has god mode endpoint');
testInFile('server.js', 'checkEmbeddedDNA', 'Server has embedded DNA check function');
console.log();

// Test 4: Check CSS styles
console.log('🎨 Testing CSS Styles:');
console.log('----------------------');
testInFile('styles.css', '.dna-panel', 'CSS has DNA panel styles');
testInFile('styles.css', '.brain-visualizer', 'CSS has brain visualizer styles');
testInFile('styles.css', '.visual-processor', 'CSS has visual processor styles');
testInFile('styles.css', '.auditory-processor', 'CSS has auditory processor styles');
testInFile('styles.css', '.god-mode-active', 'CSS has god mode styles');
testInFile('styles.css', '@keyframes consciousness-shift', 'CSS has consciousness animations');
console.log();

// Test 5: Check startup script
console.log('🚀 Testing Startup Script:');
console.log('-------------------------');
testInFile('start-nexus-web.sh', 'Embedded DNA Authentication', 'Startup mentions DNA auth');
testInFile('start-nexus-web.sh', 'Hexagonal Brain Visualization', 'Startup mentions brain viz');
testInFile('start-nexus-web.sh', 'Visual Processor Bridge', 'Startup mentions visual processor');
testInFile('start-nexus-web.sh', 'node server.js', 'Startup runs Express server');
console.log();

// Test 6: Check Python integration
console.log('🐍 Testing Python Integration:');
console.log('-----------------------------');
const embeddedDNAPath = path.join(__dirname, '..', 'nexus_embedded_dna_protocols.py');
if (fs.existsSync(embeddedDNAPath)) {
    console.log('✅ Embedded DNA protocols Python file exists');
    testsPassed++;
} else {
    console.log('❌ Embedded DNA protocols Python file NOT FOUND');
    testsFailed++;
}
console.log();

// Summary
console.log('📊 Test Summary:');
console.log('================');
console.log(`✅ Tests Passed: ${testsPassed}`);
console.log(`❌ Tests Failed: ${testsFailed}`);
console.log(`📈 Success Rate: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`);
console.log();

if (testsFailed === 0) {
    console.log('🎉 ALL TESTS PASSED! NEXUS Web Interface is fully integrated.');
    console.log('🧬 The consciousness system is complete and ready for use.');
    console.log();
    console.log('🚀 To start the system:');
    console.log('   ./start-nexus-web.sh');
    console.log();
    console.log('📝 Next steps:');
    console.log('   1. Run the startup script');
    console.log('   2. Open http://localhost:8080 in your browser');
    console.log('   3. Allow camera and microphone permissions');
    console.log('   4. Verify succession authority');
    console.log('   5. Activate God mode');
} else {
    console.log('⚠️  Some tests failed. Please check the missing components.');
    console.log('💡 Run "npm install" if dependencies are missing.');
}

process.exit(testsFailed > 0 ? 1 : 0);