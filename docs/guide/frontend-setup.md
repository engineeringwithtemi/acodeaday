# Frontend Setup

This guide walks you through setting up the React frontend for acodeaday.

## Prerequisites

Before starting, ensure you have:
- Node.js 22+ installed
- Backend running on `http://localhost:8000`
- Supabase credentials

See [Prerequisites](/guide/prerequisites) for installation instructions.

## Navigate to Frontend Directory

```bash
cd acodeaday/frontend
```

## Install Dependencies

Install all npm packages:

```bash
npm install
```

This will install:
- React and TanStack Router
- Monaco Editor for code editing
- Supabase client for authentication
- UI libraries (shadcn/ui, Tailwind CSS)
- Other dependencies from `package.json`

## Configure Environment Variables

Create a `.env` file in the `frontend` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# API Backend URL
VITE_API_URL=http://localhost:8000

# Supabase Configuration
VITE_SUPABASE_URL=https://[PROJECT_ID].supabase.co
VITE_SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
```

**Important:**
- `VITE_API_URL` should match where your backend is running
- Supabase credentials must match the backend configuration
- All env vars for Vite must start with `VITE_`

## Start the Development Server

Start the Vite dev server with hot module replacement:

```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

### Access the App

Open `http://localhost:5173` in your browser. You should see the acodeaday login page.

## Default Login Credentials

Use the credentials configured in your backend `.env`:

- **Username**: Value of `AUTH_USERNAME` (default: `admin`)
- **Password**: Value of `AUTH_PASSWORD`

## Build for Production

Create an optimized production build:

```bash
npm run build
```

This creates a `dist/` folder with static assets ready for deployment.

### Preview Production Build

Test the production build locally:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── ui/            # shadcn/ui components
│   │   ├── CodeEditor.tsx # Monaco editor wrapper
│   │   ├── ProblemView.tsx
│   │   └── ...
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useProblems.ts
│   │   └── ...
│   ├── routes/            # TanStack Router routes
│   │   ├── index.tsx      # Dashboard
│   │   ├── problem.$slug.tsx
│   │   ├── progress.tsx
│   │   └── ...
│   ├── types/             # TypeScript types
│   ├── lib/               # Utilities and API client
│   ├── App.tsx            # Root component
│   └── main.tsx           # Entry point
├── public/                # Static assets
├── package.json
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS config
└── tsconfig.json          # TypeScript config
```

## Key Technologies

### TanStack Router

File-based routing for React applications. Routes are defined in `src/routes/`:

- `/` → `routes/index.tsx` (Dashboard)
- `/problem/:slug` → `routes/problem.$slug.tsx` (Problem view)
- `/progress` → `routes/progress.tsx` (Progress overview)
- `/mastered` → `routes/mastered.tsx` (Mastered problems)

### Monaco Editor

The same code editor used in VS Code, configured for Python syntax highlighting and IntelliSense.

Located in `src/components/CodeEditor.tsx`.

### shadcn/ui + Tailwind CSS

UI component library built on Radix UI primitives with Tailwind CSS styling.

Components are in `src/components/ui/`.

### Supabase Auth

Authentication is handled via Supabase client:

```typescript
import { supabase } from '@/lib/supabase'

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: username,
  password: password
})

// Get current session
const session = await supabase.auth.getSession()
```

## Common Commands

```bash
# Install dependencies
npm install

# Add new package
npm install package-name

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run type checking
npm run type-check

# Lint code
npm run lint

# Format code
npm run format
```

## Development Workflow

### 1. Create Component

```bash
# Create new component
touch src/components/MyComponent.tsx
```

### 2. Add shadcn/ui Component

```bash
# Add UI component (e.g., button)
npx shadcn-ui@latest add button
```

### 3. Create Route

```bash
# Create new route
touch src/routes/my-route.tsx
```

### 4. Test Component

```bash
npm run dev
# Open http://localhost:5173
```

## Troubleshooting

### "Failed to fetch" errors

- Ensure backend is running on `http://localhost:8000`
- Check `VITE_API_URL` in `.env`
- Verify CORS is configured in backend (`app/main.py`)

### Authentication errors

- Verify Supabase credentials in `.env`
- Check that backend has same Supabase configuration
- Clear browser localStorage: `localStorage.clear()`

### Monaco Editor not loading

- Check browser console for errors
- Verify `@monaco-editor/react` is installed
- Ensure `public/` directory is accessible

### Hot reload not working

- Restart dev server: `npm run dev`
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check for port conflicts (default: 5173)

### TypeScript errors

```bash
# Run type checking
npm run type-check

# Check specific file
npx tsc --noEmit src/components/MyComponent.tsx
```

## Environment-Specific Configuration

### Development

```bash
VITE_API_URL=http://localhost:8000
```

### Production

```bash
VITE_API_URL=https://api.yourapp.com
```

### Staging

```bash
VITE_API_URL=https://staging-api.yourapp.com
```

## Next Steps

- [Judge0 Setup](/guide/judge0-setup) - Configure code execution
- [Database Setup](/guide/database-setup) - Set up PostgreSQL
- [Deployment](/guide/deployment-overview) - Deploy to production
- [API Reference](/api/overview) - Explore API endpoints
