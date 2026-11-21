# CIVORA AI Platform

Review a residential plan for **structure**, **cost** and **Vastu**. Create a project, upload a plan from your computer, and run three analyzers on the same building model.

```
Browser ──► Node gateway (Express, :8080) ──► Flask API (:5000) ──► SQLite + uploaded plans
              │  security headers, rate limits     │  validation, analysis engines
              │  serves the React build            └─► Anthropic API (assistant "Mistri")
              └─ proxies /api/*
```

| Folder | Stack | Role |
| --- | --- | --- |
| `frontend/` | React 18, React Router, Vite | Intro, Dashboard, Project home, three analyzer pages, Mistri chat |
| `gateway/` | Node 18+, Express, helmet, express-rate-limit, http-proxy-middleware | Single public entry point: headers, rate limiting, API proxy, static hosting |
| `backend/` | Python 3.10+, Flask, SQLite | REST API, upload validation, analysis engines, assistant proxy |

## Quick start (development)

Requirements: Node 18+, Python 3.10+.

```bash
npm install                 # installs the root dev helper (concurrently)
npm run install:all         # frontend, gateway and backend dependencies
cp .env.example backend/.env   # optional: add ANTHROPIC_API_KEY to enable Mistri
npm run dev                 # Flask :5000, gateway :8080, Vite :5173
```

Open http://localhost:5173. Vite forwards `/api` to the gateway, which forwards to Flask.
If your Python command is `python3`, edit `dev:backend` and `install:all` in the root `package.json`.

## Production with Docker

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY if you want the assistant
docker compose up --build   # http://localhost:8080
```

The gateway image builds the React app and serves it. Plans and the database live in the `civora-data` volume.
Without Docker: `npm run build`, start Flask with gunicorn (`gunicorn -b 127.0.0.1:5000 wsgi:app` in `backend/`), then `npm --prefix gateway start`.

## Reading the 2D drawing

When a JPG, PNG or PDF plan is uploaded the backend reads it in the background (local OCR, no API key needed) and fills in
the analyzers: floors from labels such as "GROUND FLOOR PLAN", plan area from the overall dimensions, the rooms and where each
sits on the plan. Vastu zones are worked out from the room positions once you confirm which way north points; north is never
assumed. Anything you type replaces the value read from the drawing, and anything that cannot be read stays "Not provided".
DXF and DWG cannot be read yet; export them as PDF or PNG. Reading takes 20 to 60 seconds on a typical laptop.

If Mistri does not answer, run `python check_mistri.py` in `backend/`. It prints the exact reason (missing key, rejected key, no credit, unknown model, no network).

## Configuration

| Variable | Used by | Default | Purpose |
| --- | --- | --- | --- |
| `ANTHROPIC_API_KEY` | backend | empty | Enables the Mistri assistant. Without it `/api/assistant` returns 503. |
| `ANTHROPIC_MODEL` | backend | `claude-sonnet-5-5` | Model used by the assistant. |
| `ANTHROPIC_FALLBACK_MODELS` | backend | `claude-haiku-5-5` | Comma-separated models tried if `ANTHROPIC_MODEL` is not available to the key. |
| `PLAN_READER` | backend | `ocr` | `ocr` reads the drawing locally. `vision` asks Claude to read it (needs the API key; falls back to OCR on any failure). |
| `MAX_UPLOAD_MB` | backend | `25` | Largest plan upload. |
| `DATA_DIR` | backend | `backend/data` | SQLite file and uploaded plans. |
| `BACKEND_URL` | gateway | `http://127.0.0.1:5000` | Where the gateway proxies `/api`. |
| `PORT` | gateway | `8080` | Gateway port. |
| `FRONTEND_DIST` | gateway | `../frontend/dist` | Folder of the built React app. |
| `TRUST_PROXY` | gateway | unset | Set when running behind a load balancer so rate limits see real client IPs. |

## API

All routes are under `/api`. Errors are JSON: `{"error": "message", "fields": {...}}`.

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Liveness check |
| `GET /projects`, `POST /projects` | List projects, create one (`{"name": "..."}`) |
| `GET /projects/:id`, `DELETE /projects/:id` | Read or delete a project and its plan |
| `POST /projects/:id/plan` | Upload a plan (`multipart/form-data`, field `file`). JPG, PNG, PDF, DXF, DWG. Extension and file signature are both checked. |
| `GET /projects/:id/plan/file` | Download the stored plan |
| `DELETE /projects/:id/plan` | Remove the plan |
| `GET /projects/:id/model` | Saved inputs plus structure, cost and Vastu results |
| `PUT /projects/:id/inputs` | Partial update of inputs, returns the new model. An empty string clears a field. |
| `POST /assistant` | `{"messages": [{"role": "user", "content": "..."}]}` returns `{"reply": "..."}` |

Inputs: `floors` (`G`, `G+1` ... `G+9`), `area` (sq ft per floor), `zone` (`II`-`V`), `soil`, `grade` (`M20`/`M25`/`M30`), `rate` (₹ per sq ft), `range` (`10`/`15`/`20`), `north` (`top`/`right`/`bottom`/`left`), `rooms` (`{"Kitchen": "SE"}`).

## How the analyzers behave

- **Nothing is guessed.** Missing data shows as `Not provided`. Checks the system cannot perform show as `Not evaluated`.
- **Structure:** reports the inputs, the IS 1893 zone factor Z, and advisory notes. Load and code checks are intentionally not simulated.
- **Cost:** built-up area (floors x area) times the rate you enter, with a low-to-high range. No rate is assumed.
- **Vastu:** north must be confirmed. Rooms are checked against the small rule set in `backend/app/engines/vastu.py`. Edit it to match the school you follow.
- All numbers come from the Python engines in `backend/app/engines/`; the React app only renders them.

## Tests

```bash
cd backend && python -m pytest -q     # 18 tests: engines, validation, uploads, API, assistant
cd gateway && npm test                # 6 tests: proxying, headers, SPA fallback, 502s, rate limit
```

## Known limits and next steps

- No user accounts yet. Anyone who can reach the server can see every project. Add authentication before exposing it publicly.
- SQLite and local file storage suit one server. Move to PostgreSQL and object storage to scale out.
- Add a real structural and quantity engine behind the `Not evaluated` rows, plus dated rate tables (CPWD DSR, Gujarat R&B).
- Add PDF and Excel report export.
- The frontend has no automated tests yet.
- Results are decision support, not certified engineering. A licensed professional must review any real project.
