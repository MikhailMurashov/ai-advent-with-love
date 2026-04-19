FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv
RUN uv sync

COPY server.py .
COPY models.py .
COPY database.py .
COPY repository.py .
COPY channels/ channels/

RUN mkdir -p /app/data

EXPOSE 8004
CMD ["uv", "run", "fastmcp", "run", "server.py:mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8004"]
