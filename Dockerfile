
FROM python:3.13-slim AS builder

ENV POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.8.3"

WORKDIR /build
COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root --no-directory

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
RUN poetry install --only main


FROM python:3.13-slim AS runtime

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

ENV PATH="/build/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

COPY --from=builder /build/.venv /build/.venv
COPY --from=builder /build/src ./src
COPY --from=builder /build/alembic ./alembic
COPY --from=builder /build/alembic.ini ./

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
