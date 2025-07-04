// Simple script to create app icons for NEXUS 2.0

const fs = require('fs');

// Create a simple SVG icon
const createIcon = (size) => {
    const svg = `<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
    <rect width="${size}" height="${size}" fill="#0a0a0a"/>
    <text x="50%" y="45%" text-anchor="middle" fill="#00ff00" font-family="monospace" font-size="${size/4}px" font-weight="bold">
        NEXUS
    </text>
    <text x="50%" y="65%" text-anchor="middle" fill="#00ffff" font-family="monospace" font-size="${size/6}px">
        2.0
    </text>
</svg>`;
    
    return svg;
};

// Create icons
fs.writeFileSync('icon-192.svg', createIcon(192));
fs.writeFileSync('icon-512.svg', createIcon(512));

console.log('Icons created! Use an online converter to make PNGs from the SVGs.');
console.log('Or install the app first with placeholder icons.');