# syntax=docker/dockerfile:1.7
# bragi-delivery-zelda: bragi-delivery with bragi-theme-zelda preinstalled.
# See docker/admin.Dockerfile for the rationale on the root/bragi user
# switch and the build args.

ARG BRAGI_VERSION=1.28.1
FROM ghcr.io/sgaduuw/bragi-delivery:v${BRAGI_VERSION}

ARG THEME_VERSION
USER root
RUN test -n "${THEME_VERSION}" \
    || (echo "THEME_VERSION build-arg is required" && exit 1)
RUN pip install --no-cache-dir "bragi-theme-zelda==${THEME_VERSION}"
USER bragi
