# Dockerfile
#
# WHAT: Builds one image that can run EITHER the edge agent
#       OR the coordinator — which service actually starts is
#       decided by an environment variable, not by building
#       two separate images. Simpler to maintain, one image to
#       push, works for every node.
# WHY:  Every edge node and the coordinator share the exact
#       same appcd/ package underneath — building one shared
#       image avoids duplicating that logic across multiple
#       Dockerfiles.

FROM python:3.13-slim

# Prevents Python from writing .pyc files and buffers output
# immediately to logs — standard container hygiene settings.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency list FIRST, install, THEN copy code.
# This ordering means Docker can reuse the slow "install
# TensorFlow" step from cache on future builds, as long as
# requirements.txt hasn't changed — only your code layer
# rebuilds, which is much faster during development.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual project code
COPY appcd/ appcd/
COPY edge_agent/ edge_agent/
COPY coordinator/ coordinator/
COPY dashboard/ dashboard/

# Default port exposed — edge agents and coordinator will
# override this via docker-compose as needed
EXPOSE 8000

# No CMD here deliberately — docker-compose.yml specifies
# exactly which service (edge_agent or coordinator) each
# container runs, and with which environment variables