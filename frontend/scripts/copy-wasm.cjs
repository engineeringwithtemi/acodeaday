const fs = require('fs')
const path = require('path')

const files = [
  'node_modules/web-tree-sitter/tree-sitter.wasm',
  'node_modules/tree-sitter-wasms/out/tree-sitter-python.wasm',
  'node_modules/tree-sitter-wasms/out/tree-sitter-javascript.wasm',
]

const publicDir = path.join(__dirname, '..', 'public')

if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true })
}

files.forEach((src) => {
  const srcPath = path.join(__dirname, '..', src)
  const dest = path.join(publicDir, path.basename(src))
  if (fs.existsSync(srcPath)) {
    fs.copyFileSync(srcPath, dest)
    console.log(`Copied ${path.basename(src)} to public/`)
  } else {
    console.warn(`Warning: ${src} not found, skipping`)
  }
})
