# A Stock Agent

ADK Python A-share research analysis agent.

This project is research-only. It does not provide trading, order placement,
personalized investment advice, position sizing, or broker integration.

## What is included

- Python 3.12 project managed by uv
- FastAPI business API for a future custom frontend
- Google ADK single-agent entrypoint
- Optional ADK Web UI for developer debugging and eval traces
- SQLite local knowledge base with FTS5
- Local document import for TXT, Markdown, PDF, and EPUB
- Local embedding model support, defaulting to `BAAI/bge-base-zh-v1.5`
- AKShare wrapper service for A-share market data
- Docker Compose deployment with a developer UI profile

## Quick start

```bash
uv sync
cp .env.example .env
uv run pytest
uv run a-stock-agent-api
```

The API starts on `http://127.0.0.1:8000`.

```bash
curl http://127.0.0.1:8000/health
```

## ADK Web UI

The ADK Web UI is for developer/debug/eval use only. It is not the product
frontend contract.

```bash
uv run adk web src/a_stock_agent/adk_app
```

Use it to inspect tool calls, traces, and MiniMax compatibility. The future
custom frontend should use the FastAPI endpoints under `/api/v1`.

## API endpoints

- `GET /health`
- `GET /api/v1/config`
- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`
- `POST /api/v1/knowledge/import`
- `GET /api/v1/knowledge/documents`
- `DELETE /api/v1/knowledge/documents/{document_id}`
- `GET /api/v1/stocks/{symbol}/snapshot`
- `GET /api/v1/stocks/{symbol}/history`

## Import a book

```bash
uv run a-stock-agent-import books/example.txt
```

Or through the API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/knowledge/import \
  -H 'content-type: application/json' \
  -d '{"file_path":"books/example.txt"}'
```

## Docker

```bash
docker compose up --build
```

To also run ADK Web UI:

```bash
docker compose --profile dev-ui up --build
```

Data is persisted through local bind mounts:

- `./data:/app/data`
- `./books:/app/books`
- `./models:/app/models`

## LLM configuration

MiniMax is the expected default provider in practice, but the code keeps the
ADK model connector isolated behind `LLMProviderFactory`-style helpers.

OpenAI-compatible example:

```env
LLM_PROVIDER=openai
LLM_MODEL=MiniMax-M2.7
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=replace-me
```

Anthropic-compatible example:

```env
LLM_PROVIDER=anthropic
LLM_MODEL=MiniMax-M2.7-highspeed
LLM_BASE_URL=https://api.minimaxi.com/anthropic
LLM_AUTH_TOKEN=replace-me
```

The Python project also understands the earlier Go demo variable names:

```env
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
ANTHROPIC_API_KEY=replace-me
ANTHROPIC_AUTH_TOKEN=
ANTHROPIC_MODEL=MiniMax-M2.7-highspeed
```

## AKShare note

AKShare data is suitable for research workflows, but public data sources can be
delayed, unavailable, or change response fields. The service layer normalizes
AKShare output before it reaches tools or APIs.

For Eastmoney endpoints that require the `akshare-proxy-patch` gateway, enable
the patch explicitly in `.env`. Only the configured URL allowlist is hooked;
other AKShare requests are left untouched.

```env
AKSHARE_PROXY_PATCH_ENABLED=true
AKSHARE_PROXY_PATCH_GATEWAY=101.201.173.125
AKSHARE_PROXY_PATCH_TOKEN=replace-me
AKSHARE_PROXY_PATCH_RETRY=30
AKSHARE_PROXY_PATCH_HOOK_URLS=https://82.push2.eastmoney.com/api/qt/clist/get,https://push2.eastmoney.com/api/qt/stock/get,https://17.push2.eastmoney.com/api/qt/clist/get,https://push2his.eastmoney.com/api/qt/stock/kline/get,https://push2his.eastmoney.com/api/qt/stock/trends2/get,https://push2.eastmoney.com/api/qt/clist/get,https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get,http://push2.eastmoney.com/api/qt/clist/get
```
