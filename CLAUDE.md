# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Backend

```powershell
# Run all tests (from repo root)
$env:PYTHONPATH='D:\code\HappyMeal\backend'
uv run pytest -v

# Run a single test file
uv run pytest tests/test_analysis_metadata.py -v

# Run a single test by name
uv run pytest tests/test_analysis_draft.py -v -k "test_post_analysis_confirm_persists_totals"
```

> Tests use an in-memory SQLite DB — no running Postgres required.

```powershell
# Apply DB migrations (requires running Postgres)
cd backend
alembic upgrade head
```

### Frontend

```powershell
cd frontend
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # tsc + vite build (use this to check for TS errors)
npm run preview  # Serve built dist → http://localhost:4173
```

### Full Stack (Docker)

```powershell
# Dev (hot reload for both frontend and backend)
docker compose -f docker-compose.yml -f docker-compose.override.yml up

# Production build
docker compose up
```

---

## 編輯檔案後的清理

每次用 Edit 工具修改檔案後，檢查並刪除同目錄下的 `.tmp.*` 殘留暫存檔：

```powershell
Remove-Item D:\code\HappyMeal\frontend\src\*.tmp.* -ErrorAction SilentlyContinue
Remove-Item D:\code\HappyMeal\backend\app\**\*.tmp.* -ErrorAction SilentlyContinue
```

---

## Git Commits

訊息用中文，格式 `type(scope): 簡短描述`，一行為主。

---

## Architecture

### Backend — FastAPI + SQLAlchemy

**Entry:** `backend/app/main.py`  
**Routes:** `backend/app/api/routes/` — one file per domain (`analyses`, `auth`, `profile`, `consents`, `health`)  
**Services:** `backend/app/services/` — all business logic, called directly from route handlers  
**Schemas:** `backend/app/schemas/` — Pydantic request/response models  
**Models:** `backend/app/db/models.py` — all SQLAlchemy ORM models in one file  
**Migrations:** `backend/alembic/versions/`

**Key service modules:**

| Module | Responsibility |
|--------|---------------|
| `food_mapping.py` | `resolve_canonical_food()` — single entry point for normalising food names to canonical keys |
| `portion_resolution.py` | Convert user-supplied units (bowl, can, ml…) to grams; packaged drink detection |
| `nutrition_catalog.py` | Local curated `official_source` catalog lookup |
| `nutrition_resolution.py` | `resolve_item_nutrition()` — orchestrates food mapping → portion → source selection into one result |
| `analysis_confirm.py` | Confirm flow: resolves nutrition per item, builds recommendation snapshot, writes to DB |
| `analysis_views.py` | Formats DB records → API response shapes; computes `is_anomalous` flag |

**Nutrition source priority** (defined in `nutrition_resolution.py`):
`official_source → canonical_mapping → fallback_estimate`, with a `special_guard` pass for packaged drinks.

**Test fixtures** (`tests/conftest.py`):
- `client` — authenticated `TestClient` with in-memory SQLite, auto-creates a test user
- `raw_client` — unauthenticated `TestClient`
- `db_session` — bare SQLAlchemy session

### Frontend — React + TypeScript + Vite

**All pages and routing live in a single file:** `frontend/src/App.tsx` (~2500 lines).  
**API client:** `frontend/src/api.ts` — typed fetch wrappers for every endpoint.  
**Styles:** `frontend/src/styles.css` — single global stylesheet with responsive breakpoints at 1024px and 720px.

**Analysis flow state machine** (managed in `App.tsx`):

```
draft → upload → loading (preparing → recognizing) → candidate_review → result
```

The `analysisStage` string drives which JSX block renders. Re-estimate lives inside the `candidate_review` stage.

**Auth:** Session cookie set by backend; `useAuth` hook polls `/auth/me` via React Query (5 min stale time).

---

## Key Constraints

- **No new DB migrations without a corresponding Alembic file.** Computed/derived fields (e.g. `is_anomalous`) are generated at the response layer in `analysis_views.py`, not stored.
- **`food_mapping.py` is the single authority** for canonical food name resolution. Do not add food-name logic elsewhere.
- **`portion_resolution.py` is the single authority** for unit conversion and packaged drink detection.
- **Backend tests run against SQLite** — avoid PostgreSQL-specific SQL in service code.
- **Frontend has no test suite.** Validate with `npm run build` (TypeScript errors) and manual browser testing at 375px width for mobile flows.
