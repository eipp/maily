const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

const PUBLIC_DIR = path.join(process.cwd(), 'public');
const QUALITY = 80; // Adjust quality as needed

async function optimizeImage(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const fileName = path.basename(filePath, ext);
  const outputPath = path.join(path.dirname(filePath), `${fileName}.webp`);

  try {
    // Skip if WebP version already exists and is newer
    try {
      const [srcStat, destStat] = await Promise.all([fs.stat(filePath), fs.stat(outputPath)]);
      if (destStat.mtime > srcStat.mtime) {
        console.log(`Skipping ${filePath} (already optimized)`);
        return;
      }
    } catch (e) {
      // Destination doesn't exist, continue with optimization
    }

    // Process image
    const image = sharp(filePath);
    const metadata = await image.metadata();

    // Convert to WebP with optimizations
    await image
      .webp({
        quality: QUALITY,
        effort: 6, // Maximum compression effort
      })
      .resize({
        width: Math.min(metadata.width, 1920), // Max width 1920px
        withoutEnlargement: true,
        fit: 'inside',
      })
      .toFile(outputPath);

    console.log(`Optimized: ${filePath} -> ${outputPath}`);

    // If original is larger than WebP version, replace it
    const [origSize, webpSize] = await Promise.all([
      fs.stat(filePath).then(s => s.size),
      fs.stat(outputPath).then(s => s.size),
    ]);

    if (webpSize < origSize && ext !== '.webp') {
      await fs.unlink(filePath);
      console.log(`Replaced ${filePath} with WebP version`);
    }
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error);
  }
}

async function processDirectory(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      await processDirectory(fullPath);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (['.jpg', '.jpeg', '.png', '.gif', '.svg'].includes(ext)) {
        await optimizeImage(fullPath);
      }
    }
  }
}

// Add script to package.json:
// "scripts": {
//   "optimize-images": "node scripts/optimize-images.js"
// }

async function main() {
  try {
    await processDirectory(PUBLIC_DIR);
    console.log('Image optimization complete!');
  } catch (error) {
    console.error('Error during image optimization:', error);
    process.exit(1);
  }
}

main();
