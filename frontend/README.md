# FinSight AI — React frontend

React (plain JavaScript) + Vite rewrite of the original static frontend.
It talks to the existing FastAPI backend; nothing in `backend/` changes.

## Run locally

```bash
cd frontend
cp .env.example .env      # optional; defaults to the deployed backend
npm install
npm run dev               # http://localhost:5173
```

To test against a local backend, set
`VITE_API_BASE_URL=http://127.0.0.1:8000` in `.env`.

## Build

```bash
npm run build             # outputs to dist/
npm run preview
```

## Deploy on Render (Static Site)

| Setting             | Value                                                  |
|---------------------|--------------------------------------------------------|
| Root Directory      | `frontend`                                             |
| Build Command       | `npm install && npm run build`                         |
| Publish Directory   | `dist`                                                 |
| Environment         | `VITE_API_BASE_URL=https://document-intelligence-538o.onrender.com` |

`VITE_` variables are baked in at build time, so redeploy after changing one.
There is no client-side router, so no rewrite rule is needed.

## Structure

```
src/
  main.jsx            entry point
  App.jsx             layout, tab state, "view stored document" flow
  api.js              all backend calls (API_BASE_URL from env)
  components/         Header, Nav, Dashboard, ProcessForm, ResultView, StatusBadge
  hooks/              useTheme, useApiHealth
  utils/format.js     formatting helpers + document type list
  styles/style.css    unchanged from the original frontend
```
