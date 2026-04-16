FROM python:3.13-slim

WORKDIR /backend

ARG UV_VERSION=0.9.18

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# uv
RUN pip install --no-cache-dir uv==${UV_VERSION}

# зависимости (для кеша слоёв)
COPY pyproject.toml uv.lock ./

# создаст .venv и поставит строго по lock
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# чтобы команды (uvicorn/alembic/pytest) находились без uv run
ENV PATH="/backend/.venv/bin:$PATH"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
