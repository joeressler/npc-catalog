#!/usr/bin/env bash
# Bootstrap SDXL + ComfyUI for yanwk/comfyui-boot with a models volume mount.
# Mounting /root/ComfyUI/models creates an empty /root/ComfyUI, which breaks the
# image's stock git clone — so we install ComfyUI around that mount ourselves.
set -euo pipefail

MODELS_DIR="${COMFYUI_MODELS_DIR:-/root/ComfyUI/models}"
CKPT_DIR="${MODELS_DIR}/checkpoints"
CKPT_NAME="${COMFYUI_CKPT_NAME:-sd_xl_base_1.0.safetensors}"
CKPT_PATH="${CKPT_DIR}/${CKPT_NAME}"
CKPT_URL="${COMFYUI_CKPT_URL:-https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors}"
COMFY_ROOT="${COMFYUI_ROOT:-/root/ComfyUI}"

mkdir -p "${CKPT_DIR}"

if [[ ! -f "${CKPT_PATH}" ]]; then
  echo "[comfyui] Downloading ${CKPT_NAME} (first boot; large file)..."
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

export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/root/.cache/pycache}"
export PIP_USER="${PIP_USER:-true}"
export PATH="${PATH}:/root/.local/bin"
export PIP_ROOT_USER_ACTION="${PIP_ROOT_USER_ACTION:-ignore}"

if [[ ! -f "${COMFY_ROOT}/main.py" ]]; then
  echo "[comfyui] Installing ComfyUI (models volume mount left intact)..."
  stage="$(mktemp -d)"
  # Full clone so release tags are available (depth=1 omits them).
  git clone --recurse-submodules --shallow-submodules \
    https://github.com/comfyanonymous/ComfyUI.git "${stage}/ComfyUI"
  (
    cd "${stage}/ComfyUI"
    tag="$(git tag | grep -e '^v' | sort -V | tail -1 || true)"
    if [[ -n "${tag}" ]]; then
      echo "[comfyui] Checking out ${tag}"
      git reset --hard "${tag}"
    fi
  )
  mkdir -p "${COMFY_ROOT}"
  # Copy app files without replacing mounted models/output directories.
  for item in "${stage}/ComfyUI"/* "${stage}/ComfyUI"/.[!.]*; do
    [[ -e "${item}" ]] || continue
    name="$(basename "${item}")"
    if [[ "${name}" == "models" || "${name}" == "output" ]]; then
      continue
    fi
    rm -rf "${COMFY_ROOT:?}/${name}"
    cp -a "${item}" "${COMFY_ROOT}/"
  done
  mkdir -p "${COMFY_ROOT}/custom_nodes" "${COMFY_ROOT}/output"
  if [[ ! -d "${COMFY_ROOT}/custom_nodes/ComfyUI-Manager" ]]; then
    git clone --depth=1 \
      https://github.com/ltdrdata/ComfyUI-Manager.git \
      "${COMFY_ROOT}/custom_nodes/ComfyUI-Manager" || true
  fi
  rm -rf "${stage}"
  echo "[comfyui] ComfyUI installed"
else
  echo "[comfyui] ComfyUI present: ${COMFY_ROOT}"
fi

# Newer ComfyUI releases need comfy-aimdo; cu124-slim may not ship it.
if [[ -f "${COMFY_ROOT}/requirements.txt" ]]; then
  if ! python3 -c "import comfy_aimdo" >/dev/null 2>&1; then
    echo "[comfyui] Installing ComfyUI Python requirements..."
    python3 -m pip install --user -r "${COMFY_ROOT}/requirements.txt"
  fi
fi

echo "[comfyui] Starting ComfyUI..."
cd "${COMFY_ROOT}"
# shellcheck disable=SC2086
exec python3 main.py --listen 0.0.0.0 --port 8188 ${CLI_ARGS:-}
