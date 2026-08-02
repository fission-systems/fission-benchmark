FROM mcr.microsoft.com/dotnet/sdk:9.0 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    libcapstone-dev \
    g++ \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and build Reko, pinned to a known-good commit.
#
# Upstream floats on main with no release cadence we track, so an
# unpinned `git clone --depth 1` periodically breaks this image on
# unrelated upstream changes -- e.g. commit 2a488d8 (2026-07-06)
# refactored several ViewModels to use C#13's `field` keyword, which
# this SDK/csproj's LangVersion doesn't recognize (CS0103: the name
# 'field' does not exist in the current context), failing the build.
# Pin to the last commit before that refactor and bump deliberately.
ARG REKO_COMMIT=19d53a830a033317c4fc7f744633c9d90df5b94a
WORKDIR /tmp
RUN git init reko && \
    cd reko && \
    git remote add origin https://github.com/uxmal/reko.git && \
    git fetch --depth 1 origin "${REKO_COMMIT}" && \
    git checkout FETCH_HEAD && \
    export DOTNET_ROLL_FORWARD=Major && \
    dotnet msbuild -p:Platform=x64 -p:Configuration=UnixRelease -t:build_solution -m ./src/BuildTargets/BuildTargets.csproj

# Use lightweight runtime image if possible, but dotnet decompile.dll requires dotnet runtime + capstone-dev
# We use dotnet sdk:9.0 image to make sure dotnet and compilers are correct, and keep it simple.
FROM mcr.microsoft.com/dotnet/sdk:9.0

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libcapstone-dev \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy built Reko files from builder
COPY --from=builder /tmp/reko/src/Drivers/CmdLine/bin/x64/Release/net8.0 /opt/reko

# Copy server files
WORKDIR /app
COPY server.py /app/server.py

# Create virtual environment and install python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8000
ENV REKO_BIN=/opt/reko/decompile.dll
CMD ["python3", "/app/server.py"]
