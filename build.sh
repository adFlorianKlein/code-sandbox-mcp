#!/usr/bin/env bash
set -e

# Version precedence: CLI argument > VERSION file > "latest"
VERSION="${1:-$(cat VERSION 2>/dev/null || echo "latest")}"

echo "Building images with tag: $VERSION"

docker build -f docker/base.Dockerfile -t "code-sandbox-base:$VERSION" .
docker build -f docker/nodejs.Dockerfile -t "code-sandbox-nodejs:$VERSION" --build-arg BASE_VERSION="$VERSION" .
docker build -f docker/java.Dockerfile   -t "code-sandbox-java:$VERSION"   --build-arg BASE_VERSION="$VERSION" .
docker build -f docker/full.Dockerfile   -t "code-sandbox-full:$VERSION"   --build-arg BASE_VERSION="$VERSION" .

echo "Done. Built: code-sandbox-base:$VERSION, code-sandbox-nodejs:$VERSION, code-sandbox-java:$VERSION, code-sandbox-full:$VERSION"
