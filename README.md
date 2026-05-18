# VietLegal Traffic RAG

Scoped Vietnamese traffic-law RAG demo for AI engineer / RAG engineer interviews.

[Public demo](https://huggingface.co/spaces/lyhoang0104ls/vietlegal-traffic-rag) | [GitHub](https://github.com/lyhoangai/vietlegal-traffic-rag) | [Benchmark summary](docs/benchmarks/latest_summary.md) | [Demo script](docs/demo-script.md)

![CI workflow](docs/assets/ci-badge.svg)

## One-line pitch

This is a narrow-scope Vietnamese traffic-law assistant with citations, short-term session memory, optional official-source web checks, and reproducible eval artifacts.

Nói ngắn: đây không phải "legal AI biết tất cả". Đây là một demo có phạm vi rõ, có bằng chứng, và có thể deploy thật.

## Why this is worth showing

- scoped problem instead of broad legal-AI claims
- answers are grounded in citations, not silent guessing
- follow-up turns work because short-term memory is part of the flow
- chat history survives refresh
- benchmark package and summary are committed to the repo
- Docker, Render, and Hugging Face deployment paths are included
- a short demo script is ready for live walkthroughs

## Demo

### Current full-page capture

![Current full-page demo](docs/assets/readme-home-current.png)

### Close-up views

![Desktop chat demo](docs/assets/chat-ui.png)

![History sidebar](docs/assets/history-sidebar.png)

Use the walkthrough in [`docs/demo-script.md`](docs/demo-script.md).

What to show in 2-3 minutes:

1. ask a traffic-penalty question
2. ask a follow-up that depends on memory
3. refresh and show history recovery
4. ask an out-of-scope question and show refusal
5. point to the benchmark summary as proof

## Benchmark Highlights

Local benchmark run on `2026-03-27` using [`datasets/vietlegal-traffic-eval-v2/README.md`](datasets/vietlegal-traffic-eval-v2/README.md):

| Mode | Cases | Pass Rate | Errors | Citation Rate | Reference Match | Avg Confidence | Web Usage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 300 | 98.3% | 0 | 100.0% | 99.6% | 0.823 | 70.0% |

Full artifacts:

- [`docs/benchmarks/latest_summary.md`](docs/benchmarks/latest_summary.md)
- [`docs/benchmarks/latest_results.json`](docs/benchmarks/latest_results.json)
- [`datasets/vietlegal-traffic-eval-v2/README.md`](datasets/vietlegal-traffic-eval-v2/README.md)

## Architecture

```mermaid
flowchart LR
    A["User Question"] --> B["Web UI"]
    B --> C["FastAPI API"]
    C --> D["Session Memory<br/>SQLite reload + save"]
    C --> E["RAG Graph"]
    E --> F["Active 2025 Corpus<br/>Manifest + Chroma"]
    E --> G["Optional Official-Source<br/>Web Verification"]
    E --> H["Answer with Citations"]
    H --> I["SSE Streaming Response"]
    I --> B
    B --> J["Vietnamese TTS"]
    C --> K["Benchmark & Eval Artifacts"]
```

This is the real pipeline: browser input goes to FastAPI, the app reloads short-term memory, retrieves from the active traffic-law corpus, optionally verifies official sources, and streams back an answer with citations plus optional Vietnamese TTS.

- Longer walkthrough: [`docs/architecture.md`](docs/architecture.md)
- Scope statement: this is a traffic-law RAG demo, not a general legal chatbot platform

## Why This Feels Trustworthy

- scoped domain instead of "answer everything"
- explicit refusal for out-of-scope topics
- active 2025 corpus policy managed via [`data/manifest.json`](data/manifest.json)
- optional official-source web verification when asked
- session memory for follow-up turns and sidebar-visible history recovery
- benchmarkable pipeline with mode flags for reranker and web fallback

## Quick Start

Clone the public repo:

```powershell
git clone https://github.com/lyhoangai/vietlegal-traffic-rag.git
cd vietlegal-traffic-rag
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and set at least:

- `GROQ_API_KEY`
- `LLM_PROVIDER=groq`
- `EMBEDDING_PROVIDER=local`
- `MEMORY_DB_PATH=./chat_memory.db`

Optional but recommended for stronger web fallback:

- `SERPER_API_KEY`
- `TAVILY_API_KEY`

Build the vector database:

```powershell
.\.venv\Scripts\python.exe -m src.ingest.build_db
```

Run the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Open the web UI:

```text
http://127.0.0.1:8000/
```

## Run with Docker

Build and run the app in a container:

```powershell
docker compose up --build
```

The container uses [`src/deploy/bootstrap.py`](src/deploy/bootstrap.py) as its startup command. On first boot it builds Chroma into `/app/storage/chroma_db`, then starts `uvicorn`. Later restarts reuse that storage instead of rebuilding from scratch.

What persists in Docker:

- Chroma collections via the named volume `vietlegal_storage`
- chat session memory via `/app/storage/chat_memory.db`

What you still need locally:

- a filled `.env` with at least `GROQ_API_KEY`
- the 2025 traffic-law PDFs listed in [`data/manifest.json`](data/manifest.json)

## Deploy on Render

This repo includes a Render Blueprint at [`render.yaml`](render.yaml).

Recommended flow:

1. Push the repo to GitHub.
2. In Render, create a new Blueprint from the repo.
3. Keep the bundled Docker runtime and attach the persistent disk defined in `render.yaml`.
4. Set secret env vars like `GROQ_API_KEY`, plus `SERPER_API_KEY` / `TAVILY_API_KEY` if you want stronger official-source fallback.
5. Deploy and wait for the first boot to finish building Chroma before testing `/chat`.

Render notes:

- the service uses `Docker` instead of a native Python runtime for reproducible builds
- the persistent disk is mounted at `/app/storage`, which keeps Chroma and chat-memory files across restarts
- the health check uses `GET /health`
- first deploy will be slower because the app may download the local embedding model and build the vector store

## Free Deploy on Hugging Face Spaces

If you want a free public demo instead of a paid Render service with persistent disk, use Hugging Face Spaces with the Docker SDK.

- Space README template: [`README.hf-space.md`](README.hf-space.md)
- Step-by-step guide: [`docs/deploy-huggingface-spaces.md`](docs/deploy-huggingface-spaces.md)

Trade-offs:

- free Spaces can sleep after inactivity
- storage is not persistent on the free tier, so chat memory and rebuilt Chroma state can reset
- for a portfolio demo, this is usually acceptable

## API / Endpoints

- `POST /chat`
- `POST /chat/stream`
- `GET /chat/history?session_id=...`
- `GET /chat/sessions`
- `DELETE /chat/sessions/{session_id}`
- `GET /tts/voices?locale=vi-VN`
- `POST /tts`
- `GET /health`
- `GET /eval/metrics`

## Tests

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Run the smoke benchmark used by CI:

```powershell
.\.venv\Scripts\python.exe -m src.eval.run_benchmark --smoke
```

Regression coverage includes routing, follow-up memory, official-source fallback, benchmark artifacts, manifest-driven ingestion, chat history endpoints, SSE streaming, and TTS endpoints.

## Known Limits

- not production-ready
- memory is intentionally short-term only
- retrieval quality still depends on chunking and corpus coverage
- the public benchmark is compact and portfolio-focused
