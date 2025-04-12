FROM python:3.12-slim-bullseye

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

WORKDIR /NeonFC-SSL
COPY . .

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY neonfc_ssl ./neonfc_ssl

RUN poetry install --without dev

ENTRYPOINT ["poetry", "run", "neonfc"]