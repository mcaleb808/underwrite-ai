# apps/web — UnderwriteAI dashboard

Next.js 16 (App Router) + React 19 + Tailwind 4. The landing page lists seed
applicants and recent runs; clicking one starts the underwriting pipeline and
opens a live timeline backed by an SSE stream from the API.

See the [root README](../../README.md) for setup. Run with:

```bash
pnpm install
pnpm dev   # → http://localhost:3000
```

The dev server expects the API at `http://localhost:8000` by default — override
with `NEXT_PUBLIC_API_URL` in `.env.local` (see `.env.example`).

Architecture and design notes: [`docs/architecture.md`](../../docs/architecture.md).
