# Must be built from the root of the repository
FROM python:3.10

WORKDIR /app

RUN pip install poetry

COPY ./poetry.lock ./pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY ./roster_api /app/roster_api

RUN poetry install --only-root

CMD ["poetry", "run", "roster-api"]