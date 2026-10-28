FROM vllm/vllm-openai:latest

WORKDIR /app

# Prevent HF Hub from checking for new model versions (offline mode)
ENV HF_HUB_OFFLINE=1

# Install analytical dependencies
RUN uv pip install --system --no-cache-dir \
    "duckdb>=2.0.0" \
    "polars>=2.1.0" \
    "fastexcel>=0.21.0" \
    "pydantic>=2.14.1"

# Pre-install DuckDB SQLite extension while network is available during build
RUN python3 -c "import duckdb; conn=duckdb.connect(); conn.execute('INSTALL sqlite;')"

# Copy application code
COPY src/zaic_2026/ /app/zaic_2026/

# Copy entry point
COPY predict.sh /app/predict.sh
RUN chmod +x /app/predict.sh

# Copy pre-downloaded model weights
COPY models/ /app/models/
