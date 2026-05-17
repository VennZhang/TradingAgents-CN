# TradingAgents-CN Agent Instructions

## Setup & Environment

- **Deployment mode**: Services run directly in a (WSL2) Docker container — **not** via Docker Compose.
- **Python**: 3.10+ (user has 3.12.7), `tradingagents` package installed via `pip install -e .`
- **Node**: 18+, Yarn package manager for frontend
- **.env** at project root provides all config (MongoDB, Redis, LLM API keys). It is pre-configured with the user's credentials — do NOT regenerate or overwrite it.
- **DASHSCOPE_API_KEY** is set to the user's 阿里云百炼 token in `.env`. This is the primary LLM provider.

## Commands

### Service Management
```bash
bash scripts/quick_start.sh                        # Start all (dev mode, Redis optional)
REDIS_ENABLED=true bash scripts/quick_start.sh     # Start with Redis
bash scripts/quick_stop.sh                         # Stop all (interactive prompts for DBs)
```

### Backend
```bash
pip install -e .                                   # Install tradingagents in editable mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Start backend dev server
```

### Frontend
```bash
cd frontend && yarn install                        # Install frontend dependencies
cd frontend && yarn dev --host 0.0.0.0 --port 3000 # Start frontend dev server
cd frontend && yarn build                          # Production build
cd frontend && yarn lint                           # Lint Vue/TS files
```

### Testing
```bash
pytest tests/                                      # Run all non-integration tests (default)
pytest tests/ -m integration                       # Run integration tests (need running services)
pytest tests/path/to/test_file.py::test_name       # Run single test
```
- `pytest.ini` at `tests/` skips `integration` mark and `test_server_config`/`test_stock_codes` by default
- Many scripts in `scripts/` are ad-hoc diagnostics, not part of the formal test suite

### Database
```bash
mongosh -u admin -p tradingagents123 --authenticationDatabase admin tradingagentscn  # Connect MongoDB
redis-cli -a tradingagents123                       # Connect Redis
```

## Project Architecture

```
tradingagents/    # Core Python library (Apache 2.0) — agents, graph, LLM clients, tools, dataflows
app/              # FastAPI backend (PROPRIETARY — commercial license required)
frontend/         # Vue 3 + Vite frontend (PROPRIETARY — commercial license required)
scripts/          # Utility scripts, quick start/stop, data sync, migrations
tests/            # pytest test suite
```

### Core Execution Flow

**Stock Analysis** (个股分析):
```
TradingAgentsGraph.propagate()
  → Propagator.create_initial_state()        # Initialize AgentState
  → GraphSetup.build()                       # Build StateGraph(AgentState)
  → graph.stream()                           # Node-level streaming execution
```
Pipeline: 3 parallel analysts (market/fundamentals/news) → Bull/Bear debate (conditional rounds) → Research Manager → Trader → Risk debate (conditional rounds) → Risk Manager → Signal extraction

**Index Prediction** (指数预测):
```
IndexPredictionGraph.propagate()
  → Propagator.create_initial_index_state()  # Initialize IndexPredictionState
  → IndexPredictionGraphSetup.build()        # Build StateGraph(IndexPredictionState)
  → graph.stream()                           # Node-level streaming execution
```
Pipeline: user expectations → 4 parallel analysts (technical/sentiment/macro/valuation) → 2 serial analysts (sector_theme → index_impact) → Bull/Bear debate → Index Research Manager → Index Trader → Risk debate → Index Risk Manager → final decision

### LangGraph Graph Architecture

Two independent graphs built with LangGraph `StateGraph`:

| Aspect | Stock Analysis | Index Prediction |
|--------|---------------|-----------------|
| Graph class | `TradingAgentsGraph` | `IndexPredictionGraph` |
| Builder | `GraphSetup` (`setup.py`) | `IndexPredictionGraphSetup` (`index_prediction_setup.py`) |
| State type | `AgentState` | `IndexPredictionState` |
| Analysts | 3 parallel | 4 parallel + 2 serial |
| Shared | `ConditionalLogic`, `Propagator`, `SignalProcessor` | same |

Key graph concepts:
- `ConditionalLogic` — `should_continue_*` methods decide tool-call loops vs. next node; includes dead-loop prevention via tool call count limits
- `Propagator.get_graph_args()` — returns `stream_mode` ("updates" for progress callbacks, "values" otherwise) and `recursion_limit`
- `Reflector` — post-analysis reflection, writes experience to ChromaDB long-term memory
- `SignalProcessor` — extracts structured decisions (action/target_price/confidence/risk_score) from final state

### LLM Integration

**LLM clients** (`tradingagents/llm_clients/`):
- `openai_client.py` — `NormalizedChatOpenAI(ChatOpenAI)` with `invoke()` that normalizes content. Does NOT use `streaming=True`
- `provider_factory.py` — `create_llm_by_provider()` factory function, routes by provider name to appropriate client
- Supported providers: OpenAI, 阿里百炼(DashScope/ChatTongyi), Google GenAI, Anthropic, AIHubMix, DeepSeek, 百度千帆, 本地端点

**LLM call pattern**: All agents use `llm.invoke()` (synchronous, wait for full response). No token-level streaming. The "streaming" is at **LangGraph node level** — each completed node emits an intermediate state update.

**Config flow**: Provider/model config stored in MongoDB → `config_service.py` reads it → passed to `create_llm_by_provider()` → `ChatOpenAI`/`ChatTongyi` instance created with `base_url`, `api_key`, `model`, `temperature`, `max_tokens`, `timeout`

### Agent Layer (`tradingagents/agents/`)

Uses **lazy imports** (`__getattr__` + `_EXPORTS` dict in `__init__.py`) to avoid circular dependencies.

- `analysts/` — Market, Fundamentals, News, Social Media, China Market + 6 index-specific analysts
- `researchers/` — Bull/Bear Researcher + Index Bull/Bear Researcher
- `managers/` — Research Manager, Risk Manager + Index variants
- `risk_mgmt/` — Aggressive/Conservative/Neutral Debater + Index variants
- `trader/` — Trader + Index Trader
- `utils/agent_states.py` — Core state types: `AgentState`, `InvestDebateState`, `RiskDebateState`, `IndexPredictionState`, `IndexDebateState`, `IndexRiskDebateState`
- `utils/agent_utils.py` — `Toolkit` class with `@tool` decorated methods (market data, news, fundamentals, technical indicators). **Toolkit methods with `@tool` MUST have docstrings** (LangChain requirement)
- `utils/memory.py` — `FinancialSituationMemory` (ChromaDB-based)

### Data Layer (`tradingagents/dataflows/`)

- `interface.py` — Unified data access entry point, abstracts all data sources
- `data_source_manager.py` — Manages China/US data source priorities, auto-fallback chains
- `providers/` — `BaseStockDataProvider` abstract base → concrete: AKShare, BaoStock, Tushare (China), YFinance, AlphaVantage, Finnhub (US), HK stocks
- `cache/` — Multi-level: file cache → MongoDB cache → adaptive cache
- `news/` — Chinese finance news, Google News, Reddit, Finnhub news

### Backend (`app/`)

- `main.py` — FastAPI app init, CORS, router registration, lifespan events
- `routers/` — API endpoints organized by domain: `analysis.py`, `stock.py`, `index_prediction.py`, `expectations.py`, `sse.py`, `config.py`, `auth.py`
- `services/` — Business logic layer: `analysis_service.py`, `index_prediction_service.py`, `config_service.py`, `stock_service.py`
- `worker.py` — Task execution: runs analysis in `asyncio.create_task`, reports progress via Redis
- `core/` — Auth (JWT), config, database connections (MongoDB motor client, Redis client)
- `routers/sse.py` — Server-Sent Events endpoint for real-time progress push
- Progress tracking: Agent node completes → `progress_callback` → Redis PubSub → SSE → Frontend polling

### Frontend (`frontend/`)

- **Tech stack**: Vue 3 + Vite + Element Plus + Pinia + Vue Router + ECharts + Axios + Marked
- `src/views/SingleAnalysis/` — Individual stock analysis page (3407 lines, reference implementation for rich form + progress + results)
- `src/views/IndexPrediction/` — Index prediction pages (analysis, history)
- `src/views/Expectations/` — User macro expectations CRUD
- `src/views/Settings/` — Config management (LLM providers, models, data sources)
- `src/api/` — Axios-based API modules matching backend routers
- `src/types/` — TypeScript type definitions
- `src/router/index.ts` — Route definitions
- `src/stores/` — Pinia stores

## Database & Infrastructure

- **MongoDB** (auth enabled): `admin` / `tradingagents123`, database `tradingagentscn`
- **Redis** (auth enabled): password `tradingagents123`, port 6379
- **MongoDB** is required. **Redis** is optional — can be skipped in dev mode for lower resource usage.
- Default admin login: `admin` / `admin123`

Services started:
| Service | Port | Command |
|---------|------|---------|
| Backend (FastAPI) | 8000 | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Frontend (Vite) | 3000 | `yarn dev --host 0.0.0.0 --port 3000` |
| MongoDB | 27017 | `mongod --auth` |
| Redis | 6379 | `redis-server` (dev mode: skipped) |

Key URLs: `http://localhost:3000` (frontend), `http://localhost:8000/docs` (API docs)

## Troubleshooting Startup

- PID files: `.backend.pid`, `.frontend.pid` at project root
- Backend log: `/tmp/uvicorn.log`
- Frontend log: `/tmp/frontend.log`
- Startup log: `logs/quick_start.log`
- MongoDB data: `/data/db`, logs: `/var/log/mongodb/mongod.log`
- If MongoDB fails with auth, the start script falls back to no-auth mode
- The scripts use dynamic path detection (`SCRIPT_DIR` + `dirname`) — do NOT hardcode paths

## Key Constraints

- `app/` and `frontend/` directories are **proprietary** (commercial license). The rest is Apache 2.0.
- This is a **local development deployment** — data lives in this container's MongoDB/Redis, not managed by Docker Compose volumes.
- Multiple project directories share the same MongoDB/Redis (same credentials in `.env`). Only run one instance at a time to avoid port conflicts.
- Project version in code is `1.0.0-preview` (pyproject.toml), though README documents v1.0.1 features.
- `StateGraph(dict)` must use proper typed state (e.g., `StateGraph(IndexPredictionState)`) to avoid parallel node merge conflicts on shared keys like `messages`, `sender`
- Analysis depth maps to debate/risk rounds: 快速(1,1) / 基础(1,1+memory) / 标准(1,2) / 深度(2,2) / 全面(3,3)

## Data Sources

- Primary: **AKShare** (free, no API key needed) — `DEFAULT_CHINA_DATA_SOURCE=akshare`
- Optional: Tushare, BaoStock, FinnHub (require their own tokens)
- Stock data must be synced before analysis; use sync scripts in `scripts/` or the web UI's data management page.

## Index Prediction Feature

A parallel graph (`IndexPredictionGraph`) for forecasting 6 broad-market indices (上证50/沪深300/中证500/中证1000/科创50/创业板指):

- **New data providers**: `tradingagents/dataflows/providers/china/sector_data.py`, `index_data.py`
- **Agent layer**: 14 new agents in `tradingagents/agents/` (analysts, researchers, traders, risk debaters) — registered via `__init__.py`
- **Graph**: `tradingagents/graph/index_prediction_graph.py` + `index_prediction_setup.py`
- **State types**: `IndexPredictionState`, `IndexDebateState`, `IndexRiskDebateState` in `agent_states.py`
- **Backend APIs**: `app/routers/expectations.py` (CRUD for user macro expectations), `app/routers/index_prediction.py` (analysis tasks)
- **Frontend**: `frontend/src/views/Expectations/`, `frontend/src/views/IndexPrediction/`
- Pipeline: user expectations -> 4 parallel analysts -> 2 serial analysts -> bull/bear debate -> trader -> risk debate -> final decision

## Development Plans (opencode)

Active development plans tracked in `~/.local/share/opencode/plans/`:

1. **index-prediction-task-mgmt.md** — Task management & interaction optimization: sessionStorage state recovery for page navigation, cancel/delete/retry task endpoints, dedicated task center page for index prediction
2. **index-prediction-v2.md** — UI overhaul: rewrite IndexPrediction page to match SingleAnalysis's two-column layout with depth selector (5 tiers), analyst card grid, model config sidebar, progress bar with time estimates, tabbed results display
