# TenderMatch — AI-Powered Public Tender Matching

SiviHack Track 2 submission. Matches a construction/engineering company's
profile against live German public tenders (from oeffentlichevergabe.de)
using Claude, and presents the best fits in a Next.js UI.

## How it works

1. You fill in a company profile (line of work, place of performance,
   target contract value, exclusions, etc.) in the frontend.
2. The backend runs a live pipeline: Claude turns the profile into a
   CPV/NUTS/value filter → the filter is used to search
   oeffentlichevergabe.de for matching tenders → Claude picks and explains
   the best 3.
3. The frontend shows the 3 picks as scrollable "reel" cards. Dismissing a
   tender ("Not this one") tells the backend to nudge the filter away from
   it and fetch a fresh replacement for that slot.

Nothing is mocked or pre-seeded — every run calls the real Claude API and
fetches real, current tender data, so a full match can take roughly
30 seconds to a couple of minutes.

## Repository layout

```
backend/    FastAPI app (Python) — orchestrates the pipeline, calls Claude
frontend/   Next.js 15 + React 19 UI
```

## Prerequisites

- Python 3.11+ (developed on 3.13)
- Node.js 20+ and npm
- An Anthropic API key: https://console.anthropic.com/settings/keys

## 1. Run the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-opus-5
TENDERS_DIR=./tenders
ALLOWED_ORIGINS=http://localhost:3000
```

Start it:

```bash
uvicorn main:app --reload --port 8000
```

Check it's up: open http://localhost:8000/health — should return
`{"status": "ok", ...}`.

## 2. Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env.local` is already checked in pointing at
`http://localhost:8000` — edit it if the backend runs elsewhere.

Open http://localhost:3000.

## 3. Using it

1. Fill in at least a couple of fields in the company profile form
   (what the company does, place of performance, target contract value
   range work well as a minimum) and submit.
2. Watch the progress messages while the backend builds a filter, searches
   for tenders, and asks Claude to pick the top matches — this is a real,
   multi-step pipeline, not an instant response.
3. Spin through the 3 reels, click a card for full details, or click
   "Not this one" to have Claude find a fresh replacement for that slot.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'anthropic'`** — the venv isn't
  active. Re-run the `activate` step above, or call
  `.venv/Scripts/python.exe` (Windows) / `.venv/bin/python` directly.
- **CORS error in the browser console** — make sure `ALLOWED_ORIGINS` in
  `backend/.env` includes the frontend's actual origin.
- **401/403 from the match request** — `ANTHROPIC_API_KEY` in
  `backend/.env` is missing or invalid.
- **0 tenders found** — the auto-generated filter may be too narrow for
  the profile you entered; try a broader description or wider value range.
  `backend/logs/latest_summary.log` and `latest_debug.log` show exactly
  why each candidate tender was accepted or rejected.

## More detail

`backend/README.md` (in Vietnamese) documents the backend's internals —
endpoints, the pipeline stage-by-stage, and the incremental-fetch/caching
design — in more depth.
