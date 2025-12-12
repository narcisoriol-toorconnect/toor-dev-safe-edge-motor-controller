FROM mcr.microsoft.com/devcontainers/base:alpine-3.22

RUN apk add --no-cache \
    xz \
    python3 \
    py3-pip \
    git \
    bash \
    cmake \
    gdb \
    sqlite-dev \
    lua-dev \
    nodejs-current \
    npm \
    docker \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ttf-dejavu \
    sphinx \
    docker-cli-compose \
    && ln -sf python3 /usr/bin/python \
    && pip3 install --no-cache-dir --break-system-packages pipenv

RUN npm install --global yo generator-code

# Install mermaid-cli but skip Puppeteer's Chromium download because system Chromium is provided
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1
RUN npm install --global @mermaid-js/mermaid-cli



