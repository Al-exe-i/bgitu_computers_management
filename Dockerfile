FROM python:3.14-slim

WORKDIR /backend

ARG UV_VERSION=0.9.18

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==${UV_VERSION}

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/backend/.venv/bin:$PATH"

COPY . .

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /backend app \
    && chown -R app:app /backend

USER app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
