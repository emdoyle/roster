# Must be built from the root of the repository
FROM python:3.10
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y \
    wget \
    xz-utils

# Download and extract ctags binary
RUN wget -O ctags.tar.xz https://github.com/universal-ctags/ctags-nightly-build/releases/download/2023.09.07%2Bf7e27b4521d7dcc0b80f9f787055b53524fb95a6/uctags-2023.09.07-linux-x86_64.tar.xz \
    && tar -xf ctags.tar.xz \
    && mv uctags-2023.09.07-linux-x86_64/bin/ctags /usr/local/bin/ \
    && rm -r uctags-2023.09.07-linux-x86_64 ctags.tar.xz

RUN pip install poetry

COPY ./poetry.lock ./pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY ./roster_api /app/roster_api

RUN poetry install --only-root

CMD ["poetry", "run", "roster-api"]