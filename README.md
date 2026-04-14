# AI Advent With Love

Микросервисный AI-чат с поддержкой tool calling через MCP.

## Стек

| Сервис | Технологии | Порт |
|---|---|---|
| `services/api` | FastAPI + SQLAlchemy async + litellm | 8000 |
| `services/mcp-weather` | FastAPI MCP + Open-Meteo | 8001 |
| `services/ui` | Chainlit | 8501 |

## Быстрый старт

```bash
cp services/api/.env.example services/api/.env
# Заполнить LLM_MODEL, API_KEY (и GIGACHAT_CREDENTIALS если нужно)

docker-compose up --build
```

Открыть http://localhost:8501

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `LLM_MODEL` | litellm model string: `gigachat/GigaChat-2-Pro`, `claude-haiku-4-5`, `gpt-4o` |
| `API_KEY` | API ключ для выбранного провайдера |
| `GIGACHAT_CREDENTIALS` | Base64 credentials для GigaChat (если используется) |

## Архитектура

```
services/
├── api/                        # FastAPI backend
│   └── app/
│       ├── agent/              # Бизнес-логика (strategies, memory, mcp_client, agent)
│       ├── infrastructure/     # LiteLLMClient, SSETransport
│       ├── interfaces/         # Protocol-интерфейсы (ILLMClient, IMCPTransport, репозитории)
│       ├── db/                 # SQLAlchemy модели + репозитории (SQLite)
│       ├── routers/            # HTTP/WS эндпоинты (users, sessions, chat)
│       ├── dependencies.py     # FastAPI DI
│       ├── config.py           # Pydantic Settings
│       └── main.py             # FastAPI app + startup
├── mcp-weather/                # MCP-сервер погоды (Open-Meteo)
└── ui/                         # Chainlit UI
```

### Поток данных

```
Chainlit UI → WebSocket /ws/chat/{session_id}
                   ↓
             FastAPI (agent.py)
              ├── IMemoryRepository → SQLite
              ├── ISessionRepository → SQLite
              ├── ILLMClient (litellm) → LLM provider
              └── MCPClient → SSETransport → mcp-weather:8001
```

## Smoke Test

```bash
docker-compose up --build
# 1. Открыть http://localhost:8501
# 2. Ввести username → создаётся пользователь в SQLite
# 3. "какая погода в Москве?" → agent вызывает weather tool → ответ
# 4. Sidebar: сессия появилась
# 5. Новая сессия → вернуться к старой → история загружается
# 6. ChatSettings → изменить температуру → следующий ответ другой
```

## Локальная разработка (API)

```bash
cd services/api
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```
