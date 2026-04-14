FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir $(python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(' '.join(d['project']['dependencies']))")

COPY app.py api_client.py data_layer.py config.yaml ./

EXPOSE 8501
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8501"]
