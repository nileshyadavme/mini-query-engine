# ── Stage: runtime ────────────────────────────────────────────────────────────
# Using slim variant to keep image size small (~50 MB vs ~900 MB for full image)
FROM python:3.12-slim

# Set environment variables
# - PYTHONDONTWRITEBYTECODE: prevents Python from writing .pyc files to disk
# - PYTHONUNBUFFERED: ensures stdout/stderr are sent straight to terminal (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Copy entire project into the container
# (No pip install needed — this is pure Python with zero external dependencies)
COPY . .

# Default command: run the interactive REPL
# Override at runtime with:  docker run ... python tests/test_engine.py
CMD ["python", "main.py"]
