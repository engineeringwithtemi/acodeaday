# Deploy Frontend

This guide covers deploying the React frontend to production.

## Quick Deploy to Vercel

Vercel is the easiest platform for deploying React applications, created by the makers of Next.js.

### 1. Prerequisites

- GitHub account
- Vercel account ([vercel.com](https://vercel.com))
- Code pushed to GitHub repository
- Backend deployed and accessible

### 2. Import Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Project"
3. Select your GitHub repository
4. Vercel auto-detects Vite configuration

### 3. Configure Project

- **Framework Preset**: Vite
- **Root Directory**: `frontend` (if in subdirectory)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### 4. Add Environment Variables

In project settings, add:

```bash
VITE_API_URL=https://your-backend.railway.app
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

**Important:** All Vite env vars must start with `VITE_`

### 5. Deploy

Click "Deploy". Vercel builds and deploys automatically.

Your site will be live at:
```
https://acodeaday.vercel.app
```

### 6. Configure Custom Domain (Optional)

1. Go to project Settings > Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Vercel automatically provisions SSL certificate

### 7. Update Backend CORS

Add your Vercel URL to backend CORS:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://acodeaday.vercel.app",
        "https://yourdomain.com"
    ],
    ...
)
```

Redeploy backend.

## Deploy to Netlify

Netlify is another excellent platform with generous free tier.

### 1. Connect Repository

1. Go to [app.netlify.com](https://app.netlify.com)
2. Click "Add new site" > "Import an existing project"
3. Connect to GitHub and select repository

### 2. Configure Build Settings

- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `frontend/dist`

### 3. Add Environment Variables

In Site settings > Build & deploy > Environment:

```bash
VITE_API_URL=https://your-backend.railway.app
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### 4. Deploy

Click "Deploy site". Netlify builds and deploys.

Your site will be at:
```
https://acodeaday.netlify.app
```

### 5. Configure Redirects

Create `frontend/public/_redirects`:

```
/*    /index.html   200
```

This enables client-side routing for TanStack Router.

### 6. Custom Domain

1. Go to Site settings > Domain management
2. Add custom domain
3. Configure DNS
4. SSL is automatic

## Deploy to Cloudflare Pages

Cloudflare Pages offers excellent performance with global CDN.

### 1. Connect Repository

1. Go to [dash.cloudflare.com/pages](https://dash.cloudflare.com/pages)
2. Click "Create a project"
3. Connect GitHub repository

### 2. Configure Build

- **Production branch**: main
- **Framework preset**: Vite
- **Build command**: `npm run build`
- **Build output directory**: `dist`
- **Root directory**: `frontend`

### 3. Add Environment Variables

```bash
VITE_API_URL=https://your-backend.railway.app
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
NODE_VERSION=22
```

### 4. Deploy

Click "Save and Deploy". Site will be at:
```
https://acodeaday.pages.dev
```

### 5. Configure Redirects

Create `frontend/public/_redirects`:

```
/*    /index.html   200
```

## Deploy to AWS S3 + CloudFront

For full control and AWS integration.

### 1. Build Locally

```bash
cd frontend
npm run build
```

### 2. Create S3 Bucket

```bash
aws s3 mb s3://acodeaday-frontend
aws s3 website s3://acodeaday-frontend --index-document index.html
```

### 3. Upload Build

```bash
aws s3 sync dist/ s3://acodeaday-frontend --delete
```

### 4. Configure Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::acodeaday-frontend/*"
    }
  ]
}
```

### 5. Create CloudFront Distribution

1. Go to CloudFront console
2. Create distribution
3. Origin: Your S3 bucket
4. Default root object: `index.html`
5. Error pages: 404 → `/index.html` (for client-side routing)

### 6. Deploy Updates

```bash
npm run build
aws s3 sync dist/ s3://acodeaday-frontend --delete
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

## Environment Variables Per Environment

### Development

```bash
# frontend/.env.development
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=local_key
```

### Staging

```bash
# frontend/.env.staging
VITE_API_URL=https://staging-api.yourapp.com
VITE_SUPABASE_URL=https://staging.supabase.co
VITE_SUPABASE_ANON_KEY=staging_key
```

### Production

```bash
# frontend/.env.production
VITE_API_URL=https://api.yourapp.com
VITE_SUPABASE_URL=https://prod.supabase.co
VITE_SUPABASE_ANON_KEY=prod_key
```

Vite automatically uses the correct `.env` file based on build mode.

## Optimization

### Enable Compression

Most platforms (Vercel, Netlify, Cloudflare) enable Gzip/Brotli automatically.

### Code Splitting

Vite automatically code-splits by route. Verify in build output:

```bash
npm run build

# Output shows chunk sizes:
# dist/assets/index-a1b2c3.js    142.50 kB
# dist/assets/Problem-x7y8z9.js   45.20 kB
```

### Preload Critical Assets

In `index.html`:

```html
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
```

### Analyze Bundle Size

```bash
npm install -D rollup-plugin-visualizer
```

Update `vite.config.ts`:

```typescript
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true })
  ]
});
```

Run `npm run build` to see bundle analysis.

## Performance Best Practices

### 1. Enable Caching

Vite automatically adds content hashes to filenames for long-term caching.

### 2. Lazy Load Routes

TanStack Router supports code splitting:

```typescript
// routes/problem.$slug.tsx
export const Route = createFileRoute('/problem/$slug')({
  component: lazy(() => import('@/components/ProblemView'))
})
```

### 3. Optimize Images

- Use modern formats (WebP, AVIF)
- Compress images
- Use `loading="lazy"` attribute

### 4. Minimize Dependencies

Review and remove unused packages:

```bash
npx depcheck
```

## Monitoring

### Add Analytics

**Vercel Analytics:**
```bash
npm install @vercel/analytics
```

```typescript
import { Analytics } from '@vercel/analytics/react'

function App() {
  return (
    <>
      <YourApp />
      <Analytics />
    </>
  )
}
```

**Google Analytics:**
```bash
npm install react-ga4
```

### Error Tracking

**Sentry:**
```bash
npm install @sentry/react
```

```typescript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production",
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 1.0,
});
```

## Security Headers

### Vercel

Create `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

### Netlify

Create `netlify.toml`:

```toml
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

## CI/CD

### Automatic Deploys

Vercel, Netlify, and Cloudflare Pages automatically deploy on Git push:

- **main** branch → Production
- **develop** branch → Preview (optional)
- Pull requests → Preview deployments

### Preview Deployments

Every PR gets a unique preview URL:
```
https://acodeaday-pr-123.vercel.app
```

Perfect for testing before merge!

## Troubleshooting

### Blank page after deploy

- Check browser console for errors
- Verify environment variables are set
- Check API URL is accessible
- Ensure CORS allows your frontend domain

### 404 on page refresh

Add redirect rule:
```
/*    /index.html   200
```

### Environment variables not working

- Verify they start with `VITE_`
- Rebuild after adding env vars
- Check they're set in platform dashboard

### Build fails

```bash
# Check build locally
npm run build

# Check Node.js version matches
node --version  # Should be 22+
```

## Next Steps

- [Environment Variables](/guide/environment-variables) - Complete reference
- [Backend Deployment](/guide/deploy-backend) - Deploy the API
- [Deployment Overview](/guide/deployment-overview) - Architecture overview
