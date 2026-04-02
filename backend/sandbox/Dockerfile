# Use a base image with multiple compilers and interpreters
FROM ubuntu:22.04

# Avoid prompts for interactive installations
ENV DEBIAN_FRONTEND=noninteractive

# Update and install common compilers and interpreters
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    openjdk-17-jdk \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set up a non-root user for security
RUN useradd -m sandboxuser
USER sandboxuser
WORKDIR /home/sandboxuser

# The code will be mounted or copied here
CMD ["/bin/bash"]
