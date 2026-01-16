# acodeaday Documentation

This directory contains the VitePress documentation site for acodeaday.

## Quick Start

### Development

Start the local dev server:

```bash
npm run dev
```

Site will be available at `http://localhost:5173`

### Build

Build the static site:

```bash
npm run build
```

Output will be in `.vitepress/dist/`

### Preview

Preview the production build:

```bash
npm run preview
```

## Project Structure

```
docs/
├── .vitepress/
│   ├── config.js          # VitePress configuration
│   ├── cache/             # Build cache (ignored)
│   └── dist/              # Build output (ignored)
├── guide/                 # User guides
│   ├── introduction.md
│   ├── quick-start.md
│   ├── backend-setup.md
│   ├── frontend-setup.md
│   └── ...
├── api/                   # API reference
│   ├── overview.md
│   ├── authentication.md
│   ├── problems.md
│   └── ...
├── index.md               # Homepage
├── package.json
└── README.md              # This file
```

## Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add it to the sidebar in `.vitepress/config.js`
3. Test locally with `npm run dev`

## Deployment

The documentation can be deployed to:

- **Vercel**: Connect GitHub repo, set root directory to `docs`, build command to `npm run build`
- **Netlify**: Same as Vercel
- **GitHub Pages**: Build locally and push `dist/` folder
- **Any static host**: Upload contents of `.vitepress/dist/`

## Content Sources

Documentation content is derived from:

- `/Users/to/tee/acodeaday/.claude/CLAUDE.md` - Project overview
- `/Users/to/tee/acodeaday/backend/README.md` - Backend setup
- `/Users/to/tee/acodeaday/backend/data/problems/README.md` - Problem format
- `/Users/to/tee/acodeaday/spec.md` - Detailed specification

## Technology

Built with [VitePress](https://vitepress.dev/), a static site generator powered by Vite and Vue.
