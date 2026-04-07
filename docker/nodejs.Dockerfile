ARG BASE_VERSION=latest
FROM code-sandbox-base:${BASE_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*