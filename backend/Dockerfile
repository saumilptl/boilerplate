# Stage 1: Base
FROM python:3.12-slim AS base

ARG GIT_SHA=unknown

ENV GIT_SHA=${GIT_SHA}
ENV PATH="/usr/local/bin:$PATH"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        git \
        wget \
        curl \
        gnupg \
        procps \
        build-essential \
        libpq-dev \
        postgresql-client \
        redis-tools \
        gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Install Ejson
RUN wget -O ejson.tar.gz https://github.com/Shopify/ejson/releases/download/v1.5.2/ejson_1.5.2_linux_amd64.tar.gz && \
    tar -xzf ejson.tar.gz && \
    mv ejson /usr/local/bin/ && \
    rm ejson.tar.gz

# Setup Python and Poetry
RUN python3 -m pip install --upgrade pip
RUN pip install poetry==2.1.0

# Create necessary directories
WORKDIR /app

# Stage 2: Dependencies
FROM base AS dependencies

COPY pyproject.toml poetry.lock ./
RUN touch README.md
RUN poetry install --without dev --no-root

# Stage 3: Development
FROM dependencies AS development

COPY . ./src/
WORKDIR /app/src
RUN poetry install --no-root && \
    cd /app && \
    rm -rf /app/src

VOLUME ["/app/src"]
ENV ENVIRONMENT=development
WORKDIR /app

# Stage 4: Build
FROM dependencies AS build

COPY . ./src/
WORKDIR /app/src
RUN poetry install

# Stage 5: API
FROM build AS api
# Default SERVICE_NAME - will be overridden by container environment if provided
ENV SERVICE_NAME=backend-api

RUN chmod +x scripts/docker/api.entrypoint.sh
ENTRYPOINT ["scripts/docker/api.entrypoint.sh"]

# Stage 6: Worker
FROM build AS worker
# Default SERVICE_NAME - will be overridden by container environment if provided
ENV SERVICE_NAME=backend-worker

RUN chmod +x scripts/docker/worker.entrypoint.sh
ENTRYPOINT ["scripts/docker/worker.entrypoint.sh"]
