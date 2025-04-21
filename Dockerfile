FROM python:3.13-slim
LABEL org.opencontainers.image.title="TonieToolbox"
LABEL org.opencontainers.image.description="Convert audio files to Tonie box compatible format"
LABEL org.opencontainers.image.version="0.4.0"
LABEL org.opencontainers.image.authors="Quentendo64"
LABEL org.opencontainers.image.url="https://github.com/Quentendo64/TonieToolbox"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.documentation="https://github.com/Quentendo64/TonieToolbox/blob/main/README.md"
LABEL maintainer="Quentendo64"
WORKDIR /tonietoolbox

# Install FFmpeg and opus-tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    opus-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /tonietoolbox/

# Install the Python package
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create output and temp directories and make them accessible
RUN mkdir -p /tonietoolbox/output /tonietoolbox/temp \
    && chmod -R 777 /tonietoolbox/output /tonietoolbox/temp

# Set entrypoint
ENTRYPOINT ["python", "-m", "TonieToolbox"]

# Default command (will show help)
CMD ["--help"]