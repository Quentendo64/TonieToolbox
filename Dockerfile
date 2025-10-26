FROM python:3.13-slim
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Build argument for version (will be passed from CI/CD or extracted during build)
ARG VERSION

LABEL org.opencontainers.image.title="TonieToolbox"
LABEL org.opencontainers.image.description="Convert audio files to Tonie box compatible format"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.authors="Quentendo64"
LABEL org.opencontainers.image.url="https://github.com/Quentendo64/TonieToolbox"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.documentation="https://github.com/Quentendo64/TonieToolbox/blob/main/README.md"
LABEL maintainer="Quentendo64"

WORKDIR /tonietoolbox

RUN apt-get update && apt-get install -y \
    ffmpeg \
    opus-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Built for platform: ${TARGETPLATFORM}"

COPY . /tonietoolbox/
RUN pip install --no-cache-dir -e .
RUN echo "Built TonieToolbox version: ${VERSION:-unknown}" && \
    echo "Built for platform: ${TARGETPLATFORM:-unknown}"

ENV PYTHONUNBUFFERED=1
RUN mkdir -p /tonietoolbox/output /tonietoolbox/temp \
    && chmod -R 777 /tonietoolbox/output /tonietoolbox/temp

ENTRYPOINT ["python", "-m", "TonieToolbox"]
CMD ["--help"]