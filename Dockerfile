# =============================================================================
# Multi-stage Dockerfile for the Bridge Bidding Assistant
# =============================================================================
#
# This Dockerfile uses a "multi-stage build" to create a small, efficient
# production image. Multi-stage builds let you use multiple FROM statements,
# each starting a new build stage. You can copy artifacts from one stage to
# another, leaving behind everything you don't need (build tools, dev
# dependencies, source caches, etc.).
#
# Our two stages:
#   1. "frontend" -- uses Node.js to build the React app into static files
#   2. "runtime"  -- uses Python to run the FastAPI backend, serving those
#                    static files alongside the API
#
# The final image only contains the Python runtime + our code + the built
# frontend assets. No Node.js, no npm, no source .tsx files.
#
# Build:  docker build -t kibitzer .
# Run:    docker run -p 8000:8000 -e SECRET_KEY=your-secret kibitzer
# =============================================================================


# ---------------------------------------------------------------------------
# Stage 1: Build the React frontend
# ---------------------------------------------------------------------------
# We use node:22-slim (Debian-based, small) to install npm dependencies
# and run the Vite build. The output is a set of static files (HTML, JS, CSS)
# in /app/frontend/dist/.

FROM node:22-slim AS frontend

# Set the working directory inside the container. All subsequent commands
# (COPY, RUN, etc.) are relative to this path.
WORKDIR /app/frontend

# Copy package.json and package-lock.json FIRST, before copying source code.
# Why? Docker caches each layer. If package.json hasn't changed, Docker
# reuses the cached `npm install` layer -- saving minutes on rebuilds.
# This is called "layer caching" and is one of the most important Docker
# optimizations.
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies. `npm ci` is the "clean install" command -- it
# installs exactly what's in package-lock.json (deterministic, fast,
# no surprises). Use `npm ci` in CI/CD and Docker; use `npm install`
# only during local development when you're changing dependencies.
RUN npm ci

# NOW copy the rest of the frontend source code. Changes to source files
# invalidate this layer and everything after it, but the npm install layer
# above is still cached (since package.json didn't change).
COPY frontend/ ./

# Build the production bundle. This runs TypeScript compilation + Vite
# bundling, outputting optimized, minified, content-hashed files into dist/.
# Content hashing means filenames include a hash of their contents
# (e.g. index-B5gpXRns.js), enabling aggressive browser caching.
RUN npm run build


# ---------------------------------------------------------------------------
# Stage 2: Python runtime (the final image)
# ---------------------------------------------------------------------------
# This is the image that actually runs in production. It contains:
#   - Python 3.12
#   - Our backend code (FastAPI + rule engine)
#   - The built frontend static files (copied from stage 1)
#
# It does NOT contain Node.js, npm, frontend source code, test files,
# or development dependencies.

FROM python:3.12-slim AS runtime

# Install PDM (Python Dependency Manager). PDM is like npm for Python --
# it manages dependencies and virtual environments. We install it globally
# so we can use it to install our project's dependencies.
RUN pip install --no-cache-dir pdm

WORKDIR /app

# Copy dependency files first (same layer-caching trick as the npm step).
# pyproject.toml defines what we depend on; pdm.lock pins exact versions.
COPY pyproject.toml pdm.lock ./

# Install production dependencies only (no dev dependencies like pytest,
# ruff, etc.). The flags:
#   --prod          : skip dev dependency groups
#   --no-lock       : don't update the lock file (use it as-is)
#   --no-editable   : install packages normally (not in editable/dev mode)
#   --no-self       : don't install the project itself yet (we haven't
#                     copied the source code)
RUN pdm install --prod --no-lock --no-editable --no-self

# Copy the backend source code.
COPY src/ src/

# Now install the project itself (editable install of our bridge package).
# This is separate from the dependency install so that code changes don't
# invalidate the (slow) dependency layer.
RUN pdm install --prod --no-lock --no-editable

# Copy the built frontend from stage 1 into a "static" directory.
# FastAPI will serve these files at runtime. The --from=frontend flag
# means "copy from the 'frontend' build stage", not from the host machine.
COPY --from=frontend /app/frontend/dist/ static/

# Create a directory for the SQLite database. In docker-compose.yml,
# we mount a host volume here so the database persists across container
# restarts. Without a volume mount, the database would be lost every
# time the container stops.
RUN mkdir -p /app/data

# Tell Docker that this container listens on port 8000. This is
# documentation only -- it doesn't actually publish the port. You still
# need `-p 8000:8000` when running the container.
EXPOSE 8000

# Health check -- Docker (and orchestrators like Docker Compose, ECS,
# Kubernetes) periodically hit this endpoint to verify the app is alive.
# If it fails repeatedly, the container is restarted automatically.
#   --interval=30s  : check every 30 seconds
#   --timeout=5s    : give up if no response within 5 seconds
#   --retries=3     : mark unhealthy after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# The command that runs when the container starts. We use `pdm run` to
# ensure uvicorn runs inside PDM's managed virtual environment.
#
# Key flags:
#   --host 0.0.0.0  : listen on all network interfaces (required in Docker;
#                     without this, uvicorn only listens on 127.0.0.1 which
#                     is unreachable from outside the container)
#   --port 8000     : match our EXPOSE declaration
#   --workers 1     : single worker process. We use 1 because SQLite doesn't
#                     support concurrent writes from multiple processes. If
#                     you switch to PostgreSQL later, increase this to
#                     match your CPU count (e.g. --workers 4).
#
# NOTE: No --reload flag! That's for development only. In production,
# --reload watches the filesystem for changes and restarts, which wastes
# resources and can cause unexpected behavior.
CMD ["pdm", "run", "uvicorn", "bridge.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
