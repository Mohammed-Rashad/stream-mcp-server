FROM python:3.12-slim

WORKDIR /app

# Install the package
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Default port (override with $PORT on Railway/Fly.io/Render)
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Start the remote MCP server (SSE + Bearer auth)
CMD ["stream-mcp-remote"]
