# syntax=docker/dockerfile:1.7
# bragi-admin-zelda: bragi-admin with bragi-theme-zelda preinstalled.
#
# The base image already drops to UID 1000 (bragi user); switch to root for
# the pip install since site-packages is root-owned, then switch back.
#
# BRAGI_VERSION pins the base image; bumped manually when a newer bragi
# release becomes available. THEME_VERSION is injected by release.yml from
# the GitHub Release tag.

ARG BRAGI_VERSION=1.32.0
FROM ghcr.io/sgaduuw/bragi-admin:v${BRAGI_VERSION}

ARG THEME_VERSION
USER root
RUN test -n "${THEME_VERSION}" \
    || (echo "THEME_VERSION build-arg is required" && exit 1)
RUN pip install --no-cache-dir "bragi-theme-zelda==${THEME_VERSION}"
USER bragi
