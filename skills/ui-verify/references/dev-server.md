---
title: Dev server detection
tags: [ui-verify, dev-server, react, next]
---

# Dev server detection

Infer how to reach the running app before browser verification.

## Detection order

1. **Project docs**: `CONTRIBUTING.md`, the consumer repo's `docs/llm/` onboarding docs, the README dev section.
2. **Package scripts**: `package.json` `scripts`:
   - `dev`, `start`, `serve`, `web` are common dev entry points.
   - Monorepos: check `apps/*/package.json` or `packages/*/package.json` for the app being changed.
3. **Framework defaults**: after starting, try these URLs if not documented.

| Stack | Start (typical) | Default URL |
|-------|-----------------|-------------|
| Next.js | `npm run dev` / `pnpm dev` | `http://localhost:3000` |
| Vite | `npm run dev` | `http://localhost:5173` |
| Create React App | `npm start` | `http://localhost:3000` |
| Remix | `npm run dev` | `http://localhost:5173` or `3000` |
| Angular | `ng serve` | `http://localhost:4200` |

4. **Env files**: `.env`, `.env.local` for `PORT`, `VITE_*`, `NEXT_PUBLIC_*` base URLs.
5. **User**: one concise question, "Which URL should I verify?", with your best guess.

## Starting the server

- Run from the **app root** (where the relevant `package.json` lives), not always the monorepo root.
- Use background terminal execution; poll until HTTP responds:
  - Bash/Git Bash: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`
  - PowerShell: `Invoke-WebRequest -UseBasicParsing http://localhost:3000 | Select-Object -ExpandProperty StatusCode`
- Prefer the same package manager the repo uses (`pnpm-lock.yaml` means `pnpm`, and so on).

## Auth and test data

- Look for the repo's testing docs, seed scripts, or Storybook-only flows.
- If login is required, check for test credentials in docs (never commit secrets); ask the user if they are absent.
- For Storybook-isolated components, the URL may be `http://localhost:6006/?path=/story/...` when full app integration is out of scope. Confirm with the user.

## When not to start a server

- The change is docs-only, types-only, or server-only with no UI surface, so skip **ui-verify**.
- The user explicitly said "skip browser check".
