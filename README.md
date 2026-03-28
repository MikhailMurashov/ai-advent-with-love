# LLM Чат

Streamlit-чат с поддержкой любых LLM через litellm (OpenAI, Anthropic, HuggingFace и др.).

## Возможности

- Поддержка любых LLM через litellm (GigaChat, Claude, GPT и др.)
- Скользящее окно контекста (5 сообщений) с авто-саммаризацией
- Счётчик токенов на каждое сообщение и накопленным итогом
- Настройка параметров генерации (temperature, top_p, max_tokens, seed, штрафы)
- Сохранение сессии между перезапусками (`.storage/*.json`)
- Сброс контекста одной кнопкой

## Архитектура

Проект состоит из пяти модулей. `config.py` загружает переменные окружения и экспортирует модель и ключ API. `llm_client.py` оборачивает `litellm.completion()` и возвращает `ChatResponse` с текстом и статистикой токенов. `agent.py` управляет историей диалога, скользящим окном контекста и авто-саммаризацией. `storage.py` сохраняет и загружает сессии из `.storage/*.json`. `app.py` предоставляет Streamlit-интерфейс, вызывает `Agent.run()` и сохраняет состояние через `storage.py`.

## Установка

```bash
uv sync
cp .env.example .env
```

## Настройка `.env`

```env
LLM_MODEL=huggingface/meta-llama/Llama-4-Scout-17B-16E-Instruct
# LLM_MODEL=claude-haiku-4-5
# LLM_MODEL=gpt-4o

API_KEY=your_key_here
```

## Запуск

```bash
uv run streamlit run app.py
```

## Линтинг

```bash
uv run ruff check . --fix
uv run black .
```