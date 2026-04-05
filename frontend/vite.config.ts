import { defineConfig } from 'vite'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

function versionPlugin() {
  const writeVersion = () => {
    try {
      const file = path.resolve(__dirname, 'public/version.json')
      fs.writeFileSync(file, JSON.stringify({ buildTime: Date.now() }))
    } catch {
      // Ignore - version check will show "indisponível"
    }
  }
  return {
    name: 'version',
    buildStart: writeVersion,
    configureServer: writeVersion,
  }
}

export default defineConfig({
  plugins: [
    versionPlugin(),
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },
  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    open: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    }
  }
})
