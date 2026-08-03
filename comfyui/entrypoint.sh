#!/usr/bin/env bash
# Bootstrap SDXL checkpoint then start ComfyUI (yanwk/comfyui-boot compatible).
set -euo pipefail

MODELS_DIR="${COMFYUI_MODELS_DIR:-/root/ComfyUI/models}"
CKPT_DIR="${MODELS_DIR}/checkpoints"
CKPT_NAME="${COMFYUI_CKPT_NAME:-sd_xl_base_1.0.safetensors}"
CKPT_PATH="${CKPT_DIR}/${CKPT_NAME}"
CKPT_URL="${COMFYUI_CKPT_URL:-https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors}"

mkdir -p "${CKPT_DIR}"

if [[ ! -f "${CKPT_PATH}" ]]; then
  echo "[comfyui] Downloading ${CKPT_NAME} (first boot; large file)..."
  # Resume-friendly download into a temp name, then atomic rename.
  tmp="${CKPT_PATH}.partial"
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 5 --retry-delay 5 -C - -o "${tmp}" "${CKPT_URL}"
  else
    wget -c -O "${tmp}" "${CKPT_URL}"
  fi
  mv "${tmp}" "${CKPT_PATH}"
  echo "[comfyui] Checkpoint ready: ${CKPT_PATH}"
else
  echo "[comfyui] Checkpoint present: ${CKPT_PATH}"
fi

# Prefer the image's stock launcher when present.
if [[ -x /runner-scripts/entrypoint.sh ]]; then
  exec /runner-scripts/entrypoint.sh "$@"
fi
if [[ -x /start.sh ]]; then
  exec /start.sh "$@"
fi

# Fallback: launch ComfyUI directly (listen on all interfaces for Docker DNS).
COMFY_ROOT="${COMFYUI_ROOT:-/root/ComfyUI}"
cd "${COMFY_ROOT}"
exec python main.py --listen 0.0.0.0 --port 8188 "$@"
