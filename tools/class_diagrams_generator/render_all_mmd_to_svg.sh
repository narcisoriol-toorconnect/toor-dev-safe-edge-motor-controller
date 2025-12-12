#!/bin/sh
set -eu

# Render all .mmd files in this directory to .svg
# Tries local `mmdc` (mermaid-cli). If not available, falls back to Docker image `minlag/mermaid-cli`.

OUT_DIR="$(dirname "$0")/out"

if [ ! -d "$OUT_DIR" ]; then
  echo "Output directory $OUT_DIR does not exist. Nothing to render." >&2
  exit 1
fi

# Find files
shopt_available=0
# POSIX sh: we avoid bash-only shopt; use simple loop
found=0
for f in "$OUT_DIR"/*.mmd; do
  [ -f "$f" ] || continue
  found=1
  break
done

if [ "$found" -eq 0 ]; then
  echo "No .mmd files found in $OUT_DIR" >&2
  exit 0
fi

# Choose renderer
if command -v mmdc >/dev/null 2>&1; then
  RENDERER="mmdc"
  echo "Using local mmdc (mermaid-cli)"
elif command -v docker >/dev/null 2>&1; then
  RENDERER="docker"
  echo "mmdc not found. Using Docker image minlag/mermaid-cli as fallback"
else
  echo "Neither 'mmdc' nor 'docker' found in PATH. Please install Node (npm) and @mermaid-js/mermaid-cli or Docker." >&2
  exit 2
fi

for f in "$OUT_DIR"/*.mmd; do
  [ -f "$f" ] || continue
  out_svg="${f%.mmd}.svg"
  echo "Rendering: $(basename "$f") -> $(basename "$out_svg")"
  if [ "$RENDERER" = "mmdc" ]; then
    # Use local mmdc
    # Ensure Puppeteer will find a system Chromium if it wasn't downloaded
    if [ -z "${PUPPETEER_EXECUTABLE_PATH:-}" ]; then
      # Try common binary names
      for bin in chromium chromium-browser google-chrome-stable google-chrome chromium-browser-stable; do
        if command -v "$bin" >/dev/null 2>&1; then
          export PUPPETEER_EXECUTABLE_PATH="$(command -v $bin)"
          echo "Using Chromium at $PUPPETEER_EXECUTABLE_PATH for Puppeteer"
          break
        fi
      done
    fi

    # Create a temporary puppeteer config to run Chromium with no-sandbox when running as root
    TMP_CFG="/tmp/mermaid-puppeteer-config-$$.json"
    cat > "$TMP_CFG" <<JSON
{
  "executablePath": "${PUPPETEER_EXECUTABLE_PATH:-}",
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
JSON

    mmdc -i "$f" -o "$out_svg" --puppeteerConfigFile "$TMP_CFG" || {
      echo "mmdc failed for $f" >&2
      rm -f "$TMP_CFG"
      exit 3
    }
    rm -f "$TMP_CFG"
  else
    # Docker fallback; mount workspace root and call image
    docker run --rm -v "$(pwd)":/data minlag/mermaid-cli \
      -i "/data/$f" -o "/data/$out_svg" || {
      echo "Docker mermaid-cli failed for $f" >&2
      exit 4
    }
  fi
done

echo "Rendered SVGs are in: $OUT_DIR"
