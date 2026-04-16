# UnderwriteAI

AI-powered health insurance underwriting for the Rwandan market. Multi-agent pipeline with human-in-the-loop review, explainable decisions, and built-in fairness guardrails.

## Architecture

```mermaid
flowchart LR
  subgraph web["apps/web · Next.js"]
    Apply[Applicant form]
    Dash[Underwriter dashboard]
    GraphViz[Graph visualization]
  end

  subgraph api["apps/api · FastAPI"]
    Routes[REST routes]
    Orch[Orchestrator]
    Bus[Event bus]
    SSE[SSE stream]
    Emailsvc[Email service]
    PDF[PDF report]
  end

  subgraph graph_pkg["LangGraph pipeline"]
    DP[doc_parser]
    RA[risk_assessor]
    RAG[guidelines_rag]
    DD[decision_draft]
    CR[critic]
  end

  subgraph data["Data & storage"]
    SQLite[(SQLite)]
    Chroma[(Chroma)]
    Uploads[(uploads/)]
  end

  Provider[[Resend / SMTP]]

  Apply -- multipart --> Routes
  Dash -- REST + SSE --> Routes
  GraphViz -- SSE events --> SSE
  Routes --> Orch --> graph_pkg
  DP --> RA
  DP --> RAG
  RA --> DD
  RAG --> DD
  DD --> CR
  CR -. revise .-> DD
  CR --> Orch
  Orch --> Bus --> SSE
  Orch --> SQLite
  RAG --> Chroma
  Routes --> Uploads
  Emailsvc --> Provider
  PDF --> Emailsvc
```

## Quick start

```bash
# clone and set up env
cp .env.example .env
# fill in API keys

# backend
cd apps/api && uv sync && cd ../..

# frontend
cd apps/web && pnpm install && cd ../..

# seed data
make seed

# run both
make api  # terminal 1
make web  # terminal 2
```

## Development

```bash
make api      # start api server
make web      # start next.js dev server
make test     # run unit tests
make lint     # lint and type-check
make seed     # seed chroma + demo data
make smoke    # end-to-end smoke test
```

## Project structure

```
underwrite-ai/
├── apps/
│   ├── api/          # FastAPI + LangGraph backend
│   └── web/          # Next.js 14 frontend
├── docs/             # architecture docs, demo script
├── .github/workflows # CI
├── Makefile
└── docker-compose.yml
```

## Testing

Four test layers:

- **Unit** (`test_tools.py`) — deterministic tool functions (BMI, age band, risk scoring)
- **Routes** (`test_routes.py`) — API validation, serialization, status codes
- **RAG** (`test_rag.py`) — retrieval regression against expected rule matches
- **Graph** (`test_graph.py`) — golden-path tests per persona with recorded LLM fixtures
- **Smoke** (`smoke_test.py`) — full end-to-end with real LLMs (manual)

```bash
make test              # unit + route + rag tests
make smoke             # full e2e (requires API keys)
```

## License

MIT
