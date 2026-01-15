#!/bin/bash
set -e

# Runtime environment variable injection
# Replaces placeholder values with actual env vars in compiled JS files

echo "Injecting runtime environment variables..."

# Replace placeholders with actual runtime env vars in all JS files
find /app/.output -type f \( -name "*.js" -o -name "*.mjs" \) | while read file; do
  sed -i "s|__VITE_API_URL_PLACEHOLDER__|${VITE_API_URL:-http://localhost:8000}|g" "$file"
  sed -i "s|__VITE_SUPABASE_URL_PLACEHOLDER__|${VITE_SUPABASE_URL:-}|g" "$file"
  sed -i "s|__VITE_SUPABASE_KEY_PLACEHOLDER__|${VITE_SUPABASE_KEY:-}|g" "$file"
done

echo "Environment variables injected successfully"
echo "  VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}"
echo "  VITE_SUPABASE_URL: ${VITE_SUPABASE_URL:-(not set)}"

# Execute the main command
exec "$@"
