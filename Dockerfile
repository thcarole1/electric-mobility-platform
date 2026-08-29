FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --user . python-dotenv

FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p data/raw data/warehouse

COPY --from=builder /root/.local /root/.local
COPY src/ src/
COPY run_pipeline.py .

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "run_pipeline.py"]
