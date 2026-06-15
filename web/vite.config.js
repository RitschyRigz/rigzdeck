import { defineConfig } from 'vite'
import preact from '@preact/preset-vite'
import { resolve } from 'path'

// RigzDeck frontend (Multi-Page: index.html = Editor, touch.html = Panel).
// Zieht die Deck-UI-Module aus dem geteilten deckcore (Submodul) via Alias @deckcore.
export default defineConfig(() => ({
  base: '/',
  plugins: [preact()],
  resolve: {
    // deckcore/web/ liegt außerhalb von web/ → preact-Einstiegspunkte explizit aufs lokale
    // node_modules mappen (sonst scheitert Rollup an preact/jsx[-dev]-runtime aus den Deck-Modulen).
    alias: [
      { find: '@deckcore', replacement: resolve(__dirname, '../deckcore/web') },
      { find: 'preact/jsx-dev-runtime', replacement: resolve(__dirname, 'node_modules/preact/jsx-runtime') },
      { find: 'preact/jsx-runtime', replacement: resolve(__dirname, 'node_modules/preact/jsx-runtime') },
      { find: 'preact/hooks', replacement: resolve(__dirname, 'node_modules/preact/hooks') },
      // gridstack (Frei-Editor in deckcore/web/StreamDeck.jsx) — out-of-tree-Import braucht den expliziten Alias.
      { find: 'gridstack', replacement: resolve(__dirname, 'node_modules/gridstack') },
    ],
    dedupe: ['preact'],
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        touch: resolve(__dirname, 'touch.html'),
      },
    },
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:7990' },
    fs: { allow: [resolve(__dirname, '..'), resolve(__dirname, '../deckcore')] },
  },
}))
