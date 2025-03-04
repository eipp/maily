#!/usr/bin/env node

/**
 * Script to generate PNG icons from SVG
 * This script converts the favicon.svg to PNG icons of various sizes
 * 
 * Usage: node scripts/generate-icons.js
 * 
 * Requirements: 
 * - sharp package (npm install sharp --save-dev)
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// Define paths
const SVG_PATH = path.join(__dirname, '../apps/web/public/favicon.svg');
const OUTPUT_DIR = path.join(__dirname, '../apps/web/public');

// Define icon sizes
const ICON_SIZES = [
  { name: 'icon-16.png', size: 16 },
  { name: 'icon-32.png', size: 32 },
  { name: 'icon-48.png', size: 48 },
  { name: 'icon-64.png', size: 64 },
  { name: 'icon-96.png', size: 96 },
  { name: 'icon-128.png', size: 128 },
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-256.png', size: 256 },
  { name: 'icon-384.png', size: 384 },
  { name: 'icon-512.png', size: 512 },
  { name: 'apple-touch-icon.png', size: 180 },
  { name: 'favicon.ico', size: 32 }
];

// Check if SVG file exists
if (!fs.existsSync(SVG_PATH)) {
  console.error(`Error: SVG file not found at ${SVG_PATH}`);
  process.exit(1);
}

// Create output directory if it doesn't exist
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Generate icons
async function generateIcons() {
  console.log('Generating icons from SVG...');
  
  try {
    // Read SVG file
    const svgBuffer = fs.readFileSync(SVG_PATH);
    
    // Process each icon size
    for (const icon of ICON_SIZES) {
      const outputPath = path.join(OUTPUT_DIR, icon.name);
      
      console.log(`Generating ${icon.name} (${icon.size}x${icon.size})...`);
      
      // Convert SVG to PNG with specified size
      if (icon.name === 'favicon.ico') {
        // For favicon.ico, we need to use a different approach
        await sharp(svgBuffer)
          .resize(icon.size, icon.size)
          .toFormat('png')
          .toBuffer()
          .then(buffer => {
            // Use sharp to convert PNG to ICO
            return sharp(buffer)
              .toFormat('ico')
              .toFile(outputPath);
          });
      } else {
        await sharp(svgBuffer)
          .resize(icon.size, icon.size)
          .toFormat('png')
          .toFile(outputPath);
      }
    }
    
    console.log('All icons generated successfully!');
  } catch (error) {
    console.error('Error generating icons:', error);
    process.exit(1);
  }
}

// Run the icon generation
generateIcons();
