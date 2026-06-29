# SpectralBridge — Cross-Platform Algorithmic Recommender

<!-- Replace <your-username> with your GitHub username everywhere below, and set LIVE_URL after deploying. -->
[![CI](https://github.com/<your-username>/spectralbridge/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/spectralbridge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Live demo](https://img.shields.io/badge/LIVE-LIVE_URL-22c55e?style=flat-square)](LIVE_URL)

> A statistical machine-learning engine that bridges **Codeforces** and **LeetCode** by
> projecting problems into a unified geometric space using **Latent Semantic Analysis (LSA)**
> and **Spectral Graph Theory**, then recommending *slightly-easier* problems that reuse the
> **exact same algorithmic logic**.

Paste a problem you're stuck on → get 3 "bridge" problems 100–300 rating points easier that
train the same concept. Built as a portfolio-grade, full-stack, hostable application.

<!-- Add screenshots here once captured (see the checklist in CONTRIBUTING.md / the repo-prep notes) -->
<!-- <p align="center"><img src="./assets/hero.png" width="700" alt="SpectralBridge hero"></p> -->

---

## Screenshots

> Add `assets/hero.png`, `assets/results.png`, and an `assets/demo.gif` of the live app,
> then uncomment the block above. Visuals are what make a CV repo stand out.

---

## What it does

Given a Codeforces or LeetCode URL, SpectralBridge:

1. Looks the problem up in a unified, rating-normalized corpus (**9,100 real problems**).
2. Computes its position in a **fused embedding** (semantic + structural).
3. Ranks every other problem by cosine similarity.
4. Applies a **difficulty mask** and returns the top 3 problems that are easier but
   algorithmically equivalent — **guaranteed to include at least one from each platform**.

Example — `https://codeforces.com/contest/580/problem/C` (Kefa and Park, DFS + Trees):

| Bridge | Platform | Rating | Match |
| --- | --- | --- | --- |
| Send the Fool Further! (easy) | Codeforces | 1400 | Near-identical logic |
| Count Nodes With the Highest Score | LeetCode | 1500 | Same-level practice |
| Reposts | Codeforces | 1200 | Strong match |

---

## The ML pipeline

| Phase | Technique | Library |
| --- | --- | --- |
| 1 · Corpus | Tag-canonicalized, rating-normalized scrape | `httpx` |
| 2 · Semantics | TF-IDF → TruncatedSVD (LSA), 150 dims | `scikit-learn` |
| 3 · Structure | IDF-weighted tag graph → Laplacian `L = D − A` → eigenmaps | `scipy.sparse` |
| 4 · Fusion | Concatenate + L2-normalize, cosine rank, bridge filter | `numpy` |

```
X ≈ U_k Σ_k V_kᵀ                 (LSA / semantic vectors)
L = D − A ,  f = eigvec(λ_min)   (spectral / structural vectors)
target − 300 ≤ R_candidate ≤ target − 100   (the bridge constraint)
```

The two embedding halves are individually L2-normalized before concatenation, so **semantic**
and **structural** signals contribute *equally* to the final cosine similarity.

**Cross-platform guarantee.** Because LeetCode problems only exist at three discrete ratings
(900/1500/2100), the candidate pool is gathered **per-platform** and the final 3 picks are
selected with a diversity rule that always includes at least one Codeforces AND one LeetCode
problem (whenever both exist), while still preferring easier, high-similarity matches.

---

## Engineering reality checks (and how they're solved)

These are the hard problems that come up when you actually build this — and exactly the kind of
thing worth discussing in an interview.

### 1. The semantic "story" problem
Codeforces statements hide simple algorithms behind stories ("Farmer John placing cows in
stalls" == binary search). Naive TF-IDF clusters problems by *flavour* (cows vs spaceships),
not by *algorithm*.

**Solution — `app/ml/preprocessing.py`**
- **Tag boosting**: algorithmic tags (the reliable signal) are repeated ×6 and prepended to the
  document, so the latent space is dominated by algorithmic concepts rather than story nouns.
- **Algorithmic keyword dictionary**: story vocabulary is mapped to canonical tokens
  (`maze`/`grid` → `graph`, `shortest path`/`distance` → `bfs shortest-path`).
- **Code/math stripping** so input/output format doesn't pollute term statistics.

### 2. Graph sparsity
The adjacency graph relies on overlapping tags. Tags like `implementation` / `math` are overly
broad and inconsistent, which can produce **disconnected components** that make
eigen-decomposition degenerate.

**Solution — `app/ml/spectral.py`**
- **Specificity weighting**: generic tags are excluded from the graph; remaining tags are
  weighted by **IDF**, so a rare tag (`heavy-light decomposition`) matters far more than a
  common one.
- **Semantic backbone edges**: after the tag-overlap graph is built, disjoint components are
  stitched together using top-k LSA nearest neighbours — guaranteeing a connected graph so the
  smallest-eigenvalue eigenvectors always form a meaningful global embedding.
- **Robust eigensolver**: shift-invert `eigsh` with an automatic dense `eigh` fallback.

### 3. API rate limits
LeetCode's GraphQL endpoint is aggressive against scrapers; a cold start could get IP-banned.

**Solution — `app/scraper/http_client.py`**
- **Exponential backoff with full jitter** and a polite base delay between requests.
- **SQLite caching** + a **bundled 9,100-problem dataset** so the hosted demo starts instantly
  and runs with **zero** outbound network calls.
- Live single-problem lookup as a graceful fallback for URLs outside the bundled corpus.

---

## Architecture

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app (API + SPA serving)
│   │   ├── config.py          # settings (env-driven)
│   │   ├── database.py        # SQLite layer
│   │   ├── models.py          # unified Problem + rating math
│   │   ├── data_loader.py     # DB → fallback → live scrape
│   │   ├── url_parser.py      # CF / LC URL → canonical id
│   │   ├── state.py           # recommender singleton lifecycle
│   │   ├── schemas.py         # Pydantic I/O models
│   │   ├── scraper/           # CF + LC scrapers, resilient HTTP client
│   │   ├── ml/
│   │   │   ├── preprocessing.py  # tag-boost, keyword dict (kills the story problem)
│   │   │   ├── lsa.py            # TF-IDF + TruncatedSVD
│   │   │   ├── spectral.py       # graph Laplacian eigenmaps + backbone edges
│   │   │   └── recommender.py    # fusion + bridge filter
│   │   └── routers/           # /recommend /search /stats /tags /random
│   ├── scripts/
│   │   ├── build_dataset.py   # scrape → normalize → SQLite + fallback JSON
│   │   └── train_models.py    # fit pipeline → artifacts
│   ├── tests/                 # pytest suite
│   ├── data/                  # bundled fallback_dataset.json (+ SQLite)
│   └── artifacts/             # saved LSA model + fused matrix (committed)
├── frontend/                  # React + TypeScript + Tailwind (Vite)
│   └── src/components/        # Hero, Results, Explore, HowItWorks, Stats …
├── render.yaml                # one-click deploy to Render
└── docker-compose.yml
```

---

## Run locally

### Prerequisites
- **Python 3.10+** (tested on 3.12) — `python --version`
- **Node.js 18+** with npm — `node --version`
- Internet access is **optional**: ML artifacts and a bundled dataset ship in the repo,
  so the app runs fully offline once dependencies are installed.

> The ML artifacts (`backend/artifacts/`) and dataset (`backend/data/`) are committed, so
> you can skip straight to **Option A** without any scraping or training.

---

### Option A — Single command, one port (recommended)

Runs the whole app (FastAPI **API + the built React UI**) on **http://localhost:8001**.
Best for testing the real, deployed experience.

```bash
# 1) one-time: build the frontend
cd frontend
npm install
npm run build          # outputs frontend/dist/
cd ..

# 2) one-time: set up the Python backend
cd backend
python -m venv .venv

# activate the virtualenv (pick your OS):
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt

# 3) run (serves API + UI on one port)
uvicorn app.main:app --port 8001
```

Then open **http://localhost:8001**. Done — that's the same setup that gets containerized.

---

### Option B — Dev mode with hot reload (two terminals)

Use this while editing code: the backend reloads on Python changes, the frontend reloads on
TS/CSS changes with HMR, and Vite proxies `/api/*` to the backend.

**Terminal 1 — backend:**
```bash
cd backend
python -m venv .venv
# activate (see Option A for the command for your OS)
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173  (proxies /api → :8001)
```

Open **http://localhost:5173** (the dev UI). API docs live at **http://localhost:8001/docs**.

---

### Rebuilding the dataset & models (optional)

The bundled data is pre-generated. To refresh it from the live Codeforces + LeetCode APIs
and retrain the pipeline:

```bash
cd backend
# activate your venv first
python -m scripts.build_dataset --cf-limit 2400 --lc-limit 1200
python -m scripts.train_models
```

`build_dataset` writes `data/problems.db` + `data/fallback_dataset.json`; `train_models`
writes `artifacts/lsa.joblib`, `artifacts/fused_matrix.npy`, `artifacts/problems.json`.
The backend loads these on startup automatically.

---

### Tests
```bash
cd backend
# activate your venv first
pytest -q
```

---

## Deploy

### One file → Render
`render.yaml` defines a single Docker web service. Push to GitHub, create a new site on Render
pointing at the repo → "Apply". The image builds the frontend, bakes in the ML artifacts, and
serves both API and SPA on one port with a `/api/health` check.

### Any Docker host
```bash
docker build -f backend/Dockerfile -t spectralbridge .
docker run -p 8000:8000 spectralbridge      # open http://localhost:8000
```

---

## API reference

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/recommend` | Body `{ "url": "…" }` → target + 3 bridges |
| `GET`  | `/api/search?q=` | Full-text problem search |
| `GET`  | `/api/random?limit=` | Sample problems |
| `GET`  | `/api/problem/{id}` | Problem detail |
| `GET`  | `/api/stats` | Corpus + model statistics |
| `GET`  | `/api/tags` | Top tags by frequency |
| `GET`  | `/api/health` | Liveness probe |

```bash
curl -X POST http://localhost:8001/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://leetcode.com/problems/word-break/"}'
```

---

## Tech stack

**Backend:** FastAPI · scikit-learn (TF-IDF, TruncatedSVD) · scipy.sparse (Graph Laplacian,
eigsh) · NumPy · SQLite · httpx
**Frontend:** React · TypeScript · Tailwind CSS · Vite
**Ops:** Docker (multi-stage) · Render

---

## Rating normalization

LeetCode exposes only Easy/Medium/Hard, so they're mapped to a numeric scale *before* the
project's shift `R_unified = R_lc − 400`; Codeforces ratings are the reference scale
(`R_unified = R_cf`).

```
R_unified = { R_cf                 (Codeforces)
            { R_lc − 400           (LeetCode)
```

The bridge filter then selects candidates in `[target − 300, target − 100]`.
