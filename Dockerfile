# Multi-Stage Dockerfile für gen-db
# Stage 1: C++-Build
# Stage 2: Runtime

# ============================================================================
# Stage 1: C++ Builder
# ============================================================================
FROM ubuntu:22.04 as cpp-builder

# Installation von Build-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Kopiere csubgraph Source
COPY csubgraph-main/ /build/csubgraph/

# Baue C++-Binary
WORKDIR /build/csubgraph
RUN mkdir -p build && \
    cd build && \
    cmake .. \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_FLAGS="-O3 -march=native -flto" && \
    cmake --build . --config Release -j$(nproc) && \
    strip subgraph-cli  # Reduziere Binärgröße

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.9-slim

# Installation von Runtime-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiere C++-Binary aus Builder Stage
COPY --from=cpp-builder /build/csubgraph/build/subgraph-cli /usr/local/bin/subgraph-cli
RUN chmod +x /usr/local/bin/subgraph-cli

# Verifiziere dass Binary funktioniert
RUN echo '{"graph_a":[[0,1],[1,0]],"graph_b":[[0,1],[1,0]]}' | /usr/local/bin/subgraph-cli

# Kopiere Python Source
COPY gen-db-main/src/ /app/src/

# Kopiere Requirements und installiere Python-Dependencies
COPY gen-db-main/src/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Kopiere Datenbank-Init Script
COPY gen-db-main/init_db.sql /app/init_db.sql

# Health Check Script
COPY --chown=root:root << 'EOF' /usr/local/bin/health-check.sh
#!/bin/bash
curl -f http://localhost:8000/api/health || exit 1
EOF
RUN chmod +x /usr/local/bin/health-check.sh

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Environment
ENV PYTHONUNBUFFERED=1
ENV SUBGRAPH_CLI_PATH=/usr/local/bin/subgraph-cli
ENV SUBGRAPH_MAX_WORKERS=4

# Expose Port
EXPOSE 8000

# Run API
CMD ["python", "-m", "uvicorn", "src.backend.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--access-log"]
