FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir $(python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(' '.join(d['project']['dependencies']))")

COPY server.py .

EXPOSE 8002
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8002"]
