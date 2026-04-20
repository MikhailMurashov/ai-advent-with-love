FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv
RUN uv sync

COPY server.py .

EXPOSE 8005
CMD ["uv", "run", "fastmcp", "run", "server.py:mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8005"]
