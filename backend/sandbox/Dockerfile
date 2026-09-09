# ── DebugVerse Sandbox Image ────────────────────────────────────────────────
# Base: Ubuntu 22.04 LTS
# Provides: gcc, g++, python3, node, npm, openjdk-17
# Security: non-root user, minimal layer count, no dev packages
# ─────────────────────────────────────────────────────────────────────────────

FROM ubuntu:22.04

# Avoid interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# Install all compilers/interpreters in a single layer and clean up immediately
# to keep image size minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-pip \
    openjdk-17-jdk-headless \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create a non-root sandbox user for security
RUN useradd -m -s /bin/bash sandboxuser

# Switch to non-root user
USER sandboxuser
WORKDIR /home/sandboxuser

# Default shell entry point — overridden by docker run bash -c "..."
CMD ["/bin/bash"]
