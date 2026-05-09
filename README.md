# HappyMeal

A meal analysis app for the Taiwan market. Users photograph their food, receive AI-identified candidates with portion estimates, manually confirm or correct items, and get personalized nutrition targets and exercise recommendations.

**Live:** deployed on AWS Lightsail · **Auth:** LINE OAuth 2.0

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), SQLAlchemy, Alembic |
| Database | PostgreSQL (psycopg3) |
| Frontend | React + TypeScript (Vite) |
| AI | OpenAI Responses API (Vision) |
| Auth | LINE OAuth 2.0 + server-side session |
| Deploy | Docker Compose → AWS Lightsail Container Service |
| CI/CD | GitHub Actions |

---

## AI System Design

The core of HappyMeal is a two-stage AI pipeline: vision-based food recognition followed by nutrition resolution with structured fallback.

### Stage 1 — Food Recognition (Vision API)

`backend/app/services/recognition_openai.py`

- Sends a base64-encoded meal photo to OpenAI with `temperature=0` and `max_output_tokens=400`
- Prompt enforces a strict JSON schema — the model cannot free-form; only a `candidates[]` list with typed fields is accepted
- Response is parsed field-by-field with clamping (`confidence_score` → `[0, 1]`, `portion_default` → positive only); malformed items are dropped rather than passed downstream

**Structured Output prompt contract:**
```
{
  "candidates": [
    {
      "food_name": "display name",
      "normalized_food_name": "snake_case_english_name",
      "confidence_score": 0.0–1.0,
      "portion_default": positive number,
      "portion_unit": "bowl | plate | cup | pcs | ..."
    }
  ]
}
```

**Candidate review flow** (`backend/app/services/analysis_recognition.py`):

| Outcome | Condition | `manual_review_required` |
|---|---|---|
| `success` | ≥1 candidate with `confidence_score ≥ 0.6` | `false` |
| `partial` | Candidates exist but all below threshold | `true` |
| `complete_failure` | Provider error or empty response | `true` / `false` |

Low-confidence candidates still surface for user review rather than being silently dropped. The user can correct names, adjust portions, or re-estimate.

**Error handling** — each provider error maps to a specific `reason` tag in structured JSON logs:

| Exception | `reason` | User message |
|---|---|---|
| `RateLimitError` | `quota_exceeded` | quota message |
| `BadRequestError` | `invalid_image` | image quality message |
| `APITimeoutError` | `provider_timeout` | retry message |
| `APIConnectionError` | `provider_unavailable` | retry message |

### Stage 1b — Re-estimation

When a user wants AI to revise the candidate list (e.g. "this is actually half a portion" or "it's pork, not chicken"), a second API call sends the current items plus the user's free-text instruction. The re-estimation prompt treats `user_instruction` as high-priority correction context, preventing the model from re-inventing items the user already corrected.

### Stage 2 — Nutrition Resolution

`backend/app/services/nutrition_resolution.py`

Nutrition is resolved through a priority cascade — not a single lookup:

```
official_source → canonical_mapping → fallback_estimate
        ↓ (special guard)
  packaged drinks → drink_fallback
```

1. **`official_source`** — curated catalog with per-item macros (Taiwan Health Promotion Administration data)
2. **`canonical_mapping`** — keyword/alias normalization to a known food key, then preset lookup
3. **`fallback_estimate`** — `generic_mixed_meal` preset when no match exists

Every resolved item carries:
- `nutrition_source` — which layer was used
- `is_estimated: true` when the result is an estimate, not an official figure
- `is_anomalous` flag on the response layer (computed, not stored) for outlier detection

This makes the data lineage traceable at the item level. The front end can surface "estimated value" warnings without coupling to internal source logic.

---

## Observability

Structured JSON logs flow to stdout and are read from AWS Lightsail container logs. All events carry `request_id`, `path`, and `user_id` via request-scoped context injection.

| Log event | Key fields |
|---|---|
| `openai_recognition` | `outcome`, `reason`, `candidate_count`, `latency_ms` |
| `openai_reestimate` | `outcome`, `reason`, `candidate_count`, `latency_ms` |
| `recognition_result` | `outcome`, `candidate_count`, `manual_review_required` |
| `analysis_upload` | `outcome`, `latency_ms` |
| `analysis_confirm` | `outcome`, `item_count`, `edited_item_count`, `latency_ms` |
| `reestimate_result` | `outcome`, `has_instruction`, `used_fallback`, `latency_ms` |

Baseline thresholds (P5 verified post-deploy): upload latency < 20 s, confirm latency < 1 s, provider error rate < 10%, manual fallback rate < 30%.

---

## Key Architecture Decisions

**Why not RAG / vector DB (yet)?**  
The current nutrition resolution pipeline deliberately uses a curated catalog and keyword mapping rather than embedding-based retrieval. The catalog approach is deterministic, fully auditable, and has zero retrieval latency. The `is_estimated` flag already surfaces uncertainty to users. RAG would be the right next step once catalog coverage becomes the binding constraint.

**Why `temperature=0`?**  
Nutrition data is factual. Any stochasticity in the output format would break downstream JSON parsing. Deterministic sampling also makes prompt iteration testable — same image should produce the same candidates.

**Why session cookie over JWT?**  
LINE OAuth returns a short-lived token; the app only needs a server-issued session to track the authenticated user. Server-side sessions allow instant revocation and avoid token refresh complexity at the current scale.

**Why store a `recommendation_snapshot` instead of computing on the fly?**  
Recommendations depend on profile data (weight, goal, activity) that the user may later change. Snapshotting at confirm time means history detail always shows the recommendation the user actually received, not a recomputed version based on today's profile.

---

## Running Locally

**Prerequisites:** Docker Desktop, a `.env` file at repo root (see `.env.example` if present, or set `DATABASE_URL`, `LINE_CHANNEL_ID`, `LINE_CHANNEL_SECRET`, `LINE_CALLBACK_URL`, `SESSION_SECRET_KEY`, `AI_API_KEY`).

```bash
# Full stack with hot reload
docker compose -f docker-compose.yml -f docker-compose.override.yml up

# Frontend only (Vite dev server → http://localhost:5173)
cd frontend && npm run dev

# Backend tests (in-memory SQLite, no Postgres required)
cd backend
uv run pytest -v
```

---

## Project Structure

```
backend/
  app/
    api/routes/       # FastAPI route handlers (analyses, auth, profile, consents)
    services/         # Business logic
      recognition_openai.py   # OpenAI Vision API integration
      analysis_recognition.py # Candidate review flow
      nutrition_resolution.py # Nutrition source priority cascade
      food_mapping.py         # Canonical food name resolution
      portion_resolution.py   # Unit conversion (bowl → g, ml, etc.)
      analysis_confirm.py     # Confirm flow + recommendation snapshot
    db/models.py      # All SQLAlchemy ORM models
    core/
      logging_filters.py  # JSON formatter + request context injection
  logging.json        # uvicorn structured logging config
frontend/
  src/
    App.tsx           # All pages and state machine (~2500 lines)
    api.ts            # Typed fetch wrappers for every endpoint
```
