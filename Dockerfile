FROM python:3.12-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv==0.11.23
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ROADMAP_DATA_DIR=/app/data
WORKDIR /app
RUN groupadd --gid 10001 roadmap && useradd --uid 10001 --gid roadmap --no-create-home roadmap
COPY --from=builder /app/.venv /app/.venv
COPY data ./data
USER 10001:10001
RUN roadmap-mcp validate
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).close()"]
ENTRYPOINT ["roadmap-mcp"]
CMD ["serve", "--host", "0.0.0.0"]
