# Contribution Statement

**Team:** M503
**Topic:** Topic 4 — Async Research Assistant
**Repository:** [https://github.com/orxannuriyev/research_assistant](https://github.com/orxannuriyev/research_assistant)
**Final tag:** `v1.0-final`
**Submission date:** 2026-09-19

---

## GitHub Statistics (as of 2026-09-18)

### Commit & lines of code (from GitHub Insights)

| Metric | Nazrin Burziyeva | Orkhan Nuriyev | Gunel Garayzade |
|---|---|---|---|
| Commits (GitHub Insights) | 13 | 5 | 6 |
| **Lines added** | **1,278** | **2,642** | **1,395** |
| **Lines deleted** | **542** | **16** | **373** |
| PRs opened | 6 | 3 | 3 |

> 📌 **Lines of code is the most accurate workload metric.** Orkhan's 5 commits contain 2,642 lines of additions — the entire infrastructure layer (config, models, orchestrator, cache, bench). Nazrin's commits are numerous because of iterative fixes, test coverage, Docker, and service integration. Gunel's 1,395 lines cover the FastAPI endpoint, AI module integration, and completed Streamlit UI.

> ⚠️ **Note on commit counts:** GitHub Insights reflects the commits present in the merged repository history. PR count and lines added provide additional workload context.

### Pull Requests opened

| # | Title | Author |
|---|---|---|
| #1 | `add: typed Settings with pydantic-settings and core Pydantic models` | Orkhan |
| #2 | `add: orchestrator with asyncio.gather + semaphore, cache backends, bench script` | Orkhan |
| #3 | `Orhan/orchestrator cache` | Orkhan |
| #4 | `fix: resolve wiki/DDG provider errors, sync dependencies, and add README` | Gunel |
| #5 | `Nazrin/pipeline integration` | Nazrin |
| #6 | `Nazrin/tests and quality` | Nazrin |
| #8 | `Nazrin/docs` | Nazrin |
| #9 | `build: add docker and environment config` | Nazrin |
| #10 | `refactor: update ai folder and integrate new AI module structure` | Gunel |
| #11 | `Add FastAPI endpoint for research assistant` | Gunel |
| #12 | `Nazrin/final fixes` | Nazrin |
| #13 | `Nazrin/align with api` | Nazrin |
| #15 | `feat: Add bilingual support (Azerbaijani/English) and Streamlit UI` | Gunel |

---

## Member 1 — Orkhan Nuriyev (`@orxannuriyev`)

**Role:** Infrastructure & Concurrency | Project Lead / Repository Owner

### Requirement coverage

| Requirement (TOPIC.md) | File delivered | Lines |
|---|---|---|
| `config.py` — typed settings from env | `src/config.py` | 117 |
| Pydantic models — `ResearchSession`, `CacheEntry` | `src/models.py` | 107 |
| Concurrent orchestration — `asyncio.gather`, per-source timeouts, `asyncio.Semaphore`, graceful degradation | `src/concurrency/orchestrator.py` | 199 |
| Caching — filesystem JSON, TTL support | `src/storage/cache_store.py` | 141 |
| Cache service — `(source, query)` key, canonical query normalisation | `src/services/cache.py` | 118 |
| Benchmark — sequential vs parallel timings | `scripts/bench.py` | 85 |
| `requirements.txt` — all deps pinned | `requirements.txt` | Configuration |

**Total: ~767 lines of production code owned**

**Owned:** `src/config.py`, `src/models.py`, `src/concurrency/orchestrator.py`, `src/storage/cache_store.py`, `src/services/cache.py`, `scripts/bench.py`, and `requirements.txt`.

**Co-owned:** Overall architecture and integration decisions.

*Orkhan laid the foundational architecture and infrastructure, ensuring the project's concurrency and data flow was robust from day one.*

**PRs opened:** #1, #2, #3 (+ initial direct push: repo structure)

**Reviewed:** Incoming repository work, including PRs #4, #5, #6, #8, #9, #10, #11, #12, and #13.

**Approximate share of commits:** ~21% (5 of 24 non-merge commits) | **PRs: 3**

---

## Member 2 — Nazrin Burziyeva (`@nazrinburz`)

**Role:** Service Integration, CLI, Robustness, Testing & DevOps Lead

### Requirement coverage

| Requirement (TOPIC.md) | File delivered | Lines |
|---|---|---|
| Service and engine integration completed after initial collaborative AI/API work | `src/services/ai_service.py`, `src/engine.py` | Shared ownership |
| Retries — `tenacity` exponential backoff, timeout, logging on AI calls | `src/services/ai_service.py` | 121 |
| CLI — `python -m researcher ask "..."`, `--sources`, `--no-cache`, citation rendering | `src/cli.py` | 99 |
| Validation — reject empty/oversized questions, sanitise output | `src/validation.py` | 92 |
| Tests — shared fixtures, mocks | `tests/conftest.py` | 88 |
| Tests — orchestrator concurrency (one source fail, others continue) | `tests/test_orchestrator.py` | 145 |
| Tests — cache TTL, `--no-cache`, canonical key | `tests/test_cache.py` | 63 |
| Tests — AI service retry + timeout + logging | `tests/test_ai_service.py` | 92 |
| Tests — CLI happy path + invalid input (offline, mocked) | `tests/test_cli.py` | 54 |
| Tests — end-to-end happy path over `data/research_questions.json` | `tests/test_end_to_end.py` | 75 |
| Tests — API tests (offline, source forwarding, `no_cache`, validation) | `tests/test_api.py` | 131 |
| Docker — multi-stage build, includes `api.py`, FastAPI/Uvicorn | `Dockerfile` | 36 |
| Env loading fixes, arXiv redirect handling, query normalisation | PRs #12, #13 | Core fixes |

**Total: ~1,055 lines of production + test code owned**

**Owned:** `src/engine.py`, `src/services/ai_service.py`, `src/validation.py`, `src/cli.py`, project tests, `Dockerfile`, and integration fixes documented in PRs #12 and #13.

**Co-owned:** Engine and AI-service integration with Gunel.

*Nazrin completed the surrounding service and engine integration, reliability work, CLI, tests, and Docker packaging after the initial collaborative AI/API integration. Gunel completed the Streamlit UI workflow.*

**PRs opened:** #5, #6, #8, #9, #12, #13

**Reviewed:** PRs #10 and #11 — Gunel's AI module refactor and FastAPI endpoint.

**Approximate share of commits:** ~54% (13 of 24 non-merge commits) | **PRs: 6**

> Note: Higher commit count reflects the iterative bug-fixing nature of the CLI/service integration work (env loading, arXiv redirect, query normalisation, benchmark alignment), not inflated effort.

---

## Member 3 — Gunel Garayzade (`@gunelrafig`)

**Role:** Initial API Layer, AI Module Integration & Completed Streamlit UI

### Requirement coverage

| Requirement (TOPIC.md) | File delivered | Lines |
|---|---|---|
| FastAPI `/research` POST endpoint — OOP Pydantic models, Swagger UI, clean error handling | `api.py` | 75 |
| Initial AI module integration — refactored `ai/` folder to mirror provided structure | PR #10 (`gunel-ai-update`) | Integration |
| Streamlit browser UI, LLM-provider selection, and API-facing workflow | `app.py` | UI / provider configuration |
| Bilingual UI/API iteration and English UI cleanup | PR #15 (`feat: Add bilingual support (Azerbaijani/English) and Streamlit UI`) | Historical UI/API iteration; final merged version retained English UI and provider selection |
| Provider fix — resolved wiki/DuckDuckGo provider errors, synced dependencies | PR #4 | Core fixes |
| Architecture documentation — component diagram | `docs/architecture.md` | 40 |
| README — initial setup instructions | contributed via PR #4 | Documentation |

**Total: ~115 lines of production code owned + provider/AI integration work**

**Owned:** `api.py`, `app.py`, the initial AI/API integration, provider selection, Streamlit UI, and PR #15's bilingual UI/API iteration.

**Co-owned:** AI and engine integration with Nazrin.

*Gunel established the initial AI/API integration, completed the Streamlit UI and provider-selection workflow, and contributed the bilingual UI/API iteration in PR #15. The final merged version retained the English UI and provider selection after the temporary Azerbaijani option was removed. Nazrin subsequently completed the surrounding pipeline integration, robustness, tests, and Docker packaging.*

**PRs opened:** #4, #10, #11

**Reviewed:** Requested reviewer on PR #12 (Nazrin's final fixes).

**Approximate share of commits:** ~25% (6 of 24 non-merge commits) | **PRs: 3**

---

## Full Rubric → Owner Mapping

| Rubric Category | Weight | Owner(s) | Key deliverables |
|---|---|---|---|
| Correctness & Functionality | 22% | Nazrin (engine, CLI, validation) + Gunel (API) | `src/engine.py`, `src/cli.py`, `api.py` |
| Architecture & OOP Design | 13% | Orkhan (models, config, orchestrator) | `src/models.py`, `src/config.py`, `src/concurrency/orchestrator.py` |
| Concurrency & Performance | 10% | Orkhan | `src/concurrency/orchestrator.py`, `scripts/bench.py` |
| Robustness & Error Handling | 8% | Nazrin | `src/services/ai_service.py`, `src/validation.py`, PRs #12, #13 |
| Testing & Code Quality | 7% | Nazrin (tests) + Orkhan (cache/storage infra) | `tests/` — 9 test files, 51 tests passed |
| Report | 25% | All members | Section authors per area of ownership |
| Presentation | 15% | All members | Each member presents their owned components |

---

## AI Tool Disclosure

| Module / file | Assistant | What we did with it |
|---|---|---|
| `tests/test_api.py` | AI assistant (disclosed in PR #13) | Drafted initial test structure; author verified offline-only behavior, confirmed all 51 tests passed locally before merging. |
| `tests/` (normalisation, cache) | AI assistant (disclosed in PR #12) | Suggested test cases; team kept those matching actual behavior and hand-wrote additional edge cases. |
| `api.py` | AI assistant | Scaffolded Pydantic models and Swagger handling; author refactored OOP structure, tested via `/docs`, verified `200 OK` responses with Uvicorn. |
| `report/` and contribution metrics | AI assistant | Helped format LaTeX tables, correct title-page `tabularx` layout overflow, and extract exact GitHub LOC metrics. All project data and architectural claims were verified by the team. |
| Orkhan's project work and documentation | AI assistant | Used for limited formatting, documentation, and GitHub LOC-metric assistance; all implementation decisions and project facts were reviewed by Orkhan. |

We affirm that we **can defend every line of code** in this repository during the oral defense.

---

## Signatures

By signing below, we affirm that:
- The contributions described above are accurate.
- The commit percentages reflect actual work, not artificially split commits.
- Every line of code in the repository can be defended by at least one team member.
- AI assistant usage has been disclosed as described above.

| Member | Signature | Date |
|---|---|---|
| Orkhan Nuriyev | __________________________ | 2026-09-19 |
| Nazrin Burziyeva | __________________________ | 2026-09-19 |
| Gunel Garayzade | __________________________ | 2026-09-19 |