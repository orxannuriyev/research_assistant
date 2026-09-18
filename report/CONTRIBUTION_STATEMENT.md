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
| Commits (GitHub Insights) | 12 | 4 | 4 |
| **Lines added** | **1,169** | **2,642** | **944** |
| **Lines deleted** | **386** | **16** | **204** |
| PRs opened | 6 | 3 | 3 |

> 📌 **Lines of code is the most accurate workload metric.** Orkhan's 4 commits contain 2,642 lines of additions — the entire infrastructure layer (config, models, orchestrator, cache, bench). Nazrin's commits are numerous because of iterative fixes and test coverage. Gunel's 944 lines cover the FastAPI endpoint and AI module integration.

> ⚠️ **Note on Nazrin's commit count:** Two branches were merged with regular merge instead of squash-and-merge, preserving all individual commits in `main`'s history. GitHub Insights shows 12, which reflects actual unique commits. PR count and lines added are the accurate workload measures.

### Pull Requests opened

| # | Title | Author | Merged by |
|---|---|---|---|
| #1 | `add: typed Settings with pydantic-settings and core Pydantic models` | Orkhan | Orkhan |
| #2 | `add: orchestrator with asyncio.gather + semaphore, cache backends, bench script` | Orkhan | Orkhan |
| #3 | `Orhan/orchestrator cache` | Orkhan | Orkhan |
| #4 | `fix: resolve wiki/DDG provider errors, sync dependencies, and add README` | Gunel | Gunel |
| #5 | `Nazrin/pipeline integration` | Nazrin | Nazrin |
| #6 | `Nazrin/tests and quality` | Nazrin | Nazrin |
| #8 | `Nazrin/docs` | Nazrin | Nazrin |
| #9 | `build: add docker and environment config` | Nazrin | Nazrin |
| #10 | `refactor: update ai folder and integrate new AI module structure` | Gunel | Nazrin |
| #11 | `Add FastAPI endpoint for research assistant` | Gunel | Gunel |
| #12 | `Nazrin/final fixes` | Nazrin | Nazrin |
| #13 | `Nazrin/align with api` | Nazrin | Nazrin |

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

*Orkhan laid the foundational architecture and infrastructure, ensuring the project's concurrency and data flow was robust from day one.*

**PRs opened:** #1, #2, #3 (+ initial direct push: repo structure)

**Reviewed / merged (as repo owner):**
- PRs #4, #5, #6, #8, #9, #10, #11, #12, #13 — all incoming PRs reviewed as repository maintainer

**Approximate share of commits:** ~21% (4 of 19 non-merge commits) | **PRs: 3**

---

## Member 2 — Nazrin Burziyeva (`@nazrinburz`)

**Role:** Service Layer, CLI, Robustness, Testing & DevOps Lead

### Requirement coverage

| Requirement (TOPIC.md) | File delivered | Lines |
|---|---|---|
| Retries — `tenacity` exponential backoff, timeout, logging on all AI calls | `src/services/ai_service.py` | 121 |
| Business logic — integrates ai_service, cache, orchestrator | `src/engine.py` | 95 |
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

*Nazrin drove the reliability of the system, taking on massive refactoring, CLI robustness, and building a comprehensive test suite to guarantee correctness.*

**PRs opened:** #5, #6, #8, #9, #12, #13

**Reviewed / merged:**
- PRs #10, #11 — reviewed Gunel's AI module refactor and FastAPI endpoint

**Approximate share of commits:** ~63% (12 of 19 non-merge commits) | **PRs: 6**

> Note: Higher commit count reflects the iterative bug-fixing nature of the CLI/service integration work (env loading, arXiv redirect, query normalisation, benchmark alignment), not inflated effort.

---

## Member 3 — Gunel Garayzade (`@gunelrafig`)

**Role:** API Layer, AI Module Integration & Architecture Documentation

### Requirement coverage

| Requirement (TOPIC.md) | File delivered | Lines |
|---|---|---|
| FastAPI `/research` POST endpoint — OOP Pydantic models, Swagger UI, clean error handling | `api.py` | 75 |
| AI module integration — refactored `ai/` folder to mirror provided structure | PR #10 (`gunel-ai-update`) | Integration |
| Provider fix — resolved wiki/DuckDuckGo provider errors, synced dependencies | PR #4 | Core fixes |
| Architecture documentation — component diagram | `docs/architecture.md` | 40 |
| README — initial setup instructions | contributed via PR #4 | Documentation |

**Total: ~115 lines of production code owned + provider/AI integration work**

*Gunel bridged the gap between the core engine and external consumers by implementing the FastAPI layer and ensuring the provider integrations worked flawlessly.*

**PRs opened:** #4, #10, #11

**Reviewed:**
- Requested reviewer on PR #12 (Nazrin's final-fixes)

**Approximate share of commits:** ~16% (3 of 19 non-merge commits) | **PRs: 3**

---

## Full Rubric → Owner Mapping

| Rubric Category | Weight | Owner(s) | Key deliverables |
|---|---|---|---|
| Correctness & Functionality | 22% | Nazrin (engine, CLI, validation) + Gunel (API) | `src/engine.py`, `src/cli.py`, `api.py` |
| Architecture & OOP Design | 13% | Orkhan (models, config, orchestrator) | `src/models.py`, `src/config.py`, `src/concurrency/orchestrator.py` |
| Concurrency & Performance | 10% | Orkhan | `src/concurrency/orchestrator.py`, `scripts/bench.py` |
| Robustness & Error Handling | 8% | Nazrin | `src/services/ai_service.py`, `src/validation.py`, PRs #12, #13 |
| Testing & Code Quality | 7% | Nazrin (tests) + Orkhan (cache/storage infra) | `tests/` — 8 test files, 50 tests passed |
| Report | 25% | All members | Section authors per area of ownership |
| Presentation | 15% | All members | Each member presents their owned components |

---

## AI Tool Disclosure

| Module / file | Assistant | What we did with it |
|---|---|---|
| `tests/test_api.py` | AI assistant (disclosed in PR #13) | Drafted initial test structure; author verified offline-only behavior, confirmed all 50 tests passed locally before merging. |
| `tests/` (normalisation, cache) | AI assistant (disclosed in PR #12) | Suggested test cases; team kept those matching actual behavior and hand-wrote additional edge cases. |
| `api.py` | AI assistant | Scaffolded Pydantic models and Swagger handling; author refactored OOP structure, tested via `/docs`, verified `200 OK` responses with Uvicorn. |

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
