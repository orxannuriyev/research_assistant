# Topic 4: Async Research Assistant

This project wraps the supplied `ai/` package with a software-engineering layer. A question is sent to Wikipedia, arXiv, and a configurable web-search provider concurrently; the excerpts are cached and synthesized into one answer with numbered citations.

## Quick start

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

The offline demo needs no API keys or network:

```powershell
python demo_ai.py --offline --limit 5
pytest -q
pytest --cov=src --cov-report=term-missing
```

The project uses Python 3.11 or newer. Python 3.11 is recommended because the pinned NumPy dependency has a compatible Windows wheel there.

## Live CLI

Set `LLM_PROVIDER`, its matching API key, and `WEB_SEARCH_PROVIDER` in `.env`, then run:

```powershell
python -m researcher ask "What is photosynthesis?"
python -m researcher ask "What is CRISPR?" --sources wiki,arxiv
python -m researcher ask "Neural networks" --no-cache
```

The CLI prints the synthesized answer followed by only the numeric references used in the answer. `--no-cache` disables cache reads and writes for that request.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, or `gemini` |
| `LLM_MODEL` | provider default | Model identifier |
| `WEB_SEARCH_PROVIDER` | `tavily` | `tavily`, `serper`, or `duckduckgo` |
| `CACHE_BACKEND` | `filesystem` | `filesystem` or `memory` |
| `CACHE_DIR` | `.cache` | Filesystem cache directory |
| `CACHE_TTL_SECONDS` | `3600` | Cache lifetime; `0` means no expiry |
| `SOURCE_TIMEOUT_SECONDS` | `10` | Timeout applied to each source |
| `AI_TIMEOUT_SECONDS` | `30` | Timeout applied to AI synthesis |
| `ARXIV_MIN_INTERVAL_SECONDS` | `1` | Minimum interval between arXiv requests |
| `MAX_CONCURRENT_SOURCES` | `5` | Semaphore limit |
| `LOG_LEVEL` | `INFO` | Logging level |

Copy `.env.example` to `.env` for the provider key list. Never commit `.env`.

## Architecture

`ResearchEngine` owns the request workflow. `Orchestrator` runs source fetchers through `asyncio.gather`, per-source timeouts, `asyncio.Semaphore`, and an arXiv request interval limiter. `CacheService` canonicalizes source/query keys and delegates storage to the `CacheBackend` interface. `AIService` calls the provided `ai.synthesize` function with retry and exponential backoff; the engine applies an explicit AI timeout. See [docs/architecture.md](docs/architecture.md).

The provided `ai/` package and `tests/test_ai_smoke.py` are unchanged contracts.

## Tests and benchmark

All project tests are offline. Run:

```powershell
pytest -q
pytest --cov=src --cov-report=term-missing
python -m compileall -q ai src tests researcher.py
python scripts/bench.py
```

The benchmark requires live provider access. Parallel time should approach the slowest individual source rather than the sum of all three. The following values were measured locally with the command above. In this run, Wikipedia returned HTTP 403, so four source results were counted; timings and source counts vary with provider availability, network latency, and rate limits.

| Mode | Sources | Time | Speedup |
|---|---:|---:|---:|
| Sequential | 4 | 3.03 s | 1.00x |
| Parallel | 4 | 2.38 s | 1.28x |

The exact values vary with network latency and provider rate limits.

## Docker

The image runs the five-question offline demo by default:

```powershell
docker build --platform linux/amd64 -t finalproj .
docker run --rm finalproj
```

For live research:

```powershell
docker run --rm --env-file .env finalproj python -m researcher ask "What is photosynthesis?"
```

To run and test the HTTP API locally without Docker:

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`. From another PowerShell terminal, send a request with:

```powershell
$body = @{ question = "What is photosynthesis?"; sources = "wiki,arxiv"; no_cache = $true } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/research" -Method Post -ContentType "application/json" -Body $body
```

To run the HTTP API in Docker:

```powershell
docker run --rm --env-file .env -p 8000:8000 finalproj `
	python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Project layout

```text
ai/                         provided AI module; do not modify
src/config.py               typed environment settings
src/models.py               CacheEntry and ResearchSession models
src/concurrency/            async source orchestration
src/services/               AI and cache services
src/storage/                filesystem and memory cache backends
src/engine.py               end-to-end application service
src/cli.py                  argument parsing and citation rendering
tests/                      offline project and provided smoke tests
scripts/bench.py            sequential versus parallel benchmark
docs/architecture.md        architecture diagram and flow
artefacts/                  offline demo JSON outputs
```

## Submission deliverables

Before creating the final tag, prepare these files or folders:

- `report/report.pdf` generated from the course LaTeX template.
- Slides PDF generated from the course Beamer template.
- Signed contribution statement.
- `artefacts/` containing the five offline demo answer JSON files.
- A reviewed GitHub repository state and the final `v1.0-final` tag.

## Known limitations

- Live source fetches depend on third-party availability and rate limits.
- A failed source is omitted; there is no secondary LLM failover yet.
- The report, slides, and signed contribution statement still need to be prepared for submission.