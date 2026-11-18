#!/usr/bin/env bash
# Explainer Studio setup. Safe to re-run.
#   ./setup.sh                 install deps, ask for missing API keys, check everything
#   ./setup.sh --from-env      non-interactive: take keys from the current environment (CI, Claude, a pasted export)
#   ./setup.sh --keys FILE     non-interactive: read KEY=value lines from FILE
#   ./setup.sh --skip-install  only keys + checks
#   ./setup.sh --new-channel <slug> "<Channel Name>"   copy the channel template
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd); ENVF="$ROOT/.env"
KEYS=(FAL_API_KEY KIE_API_KEY OPENROUTER_API_KEY PEXELS_API_KEY PIXABAY_API_KEY)
MODE=ask; KEYFILE=""; INSTALL=1

new_channel() {
  local slug="$1" name="$2"
  [[ "$slug" =~ ^[a-z0-9_]+$ ]] || { echo "slug: lowercase letters, digits, _"; exit 1; }
  local d="explainer/channels/$slug"
  [ -e "$d" ] && { echo "$d exists"; exit 1; }
  cp -r explainer/channels/_template "$d"
  sed -i.bak "s/my_channel/$slug/g; s/My Channel/$name/g" "$d"/*.json "$d"/*.md && rm -f "$d"/*.bak
  sed "s/my_channel/$slug/g; s/My Channel/$name/g" explainer/shorts/styles/_example.json > "explainer/shorts/styles/$slug.json"
  mkdir -p "explainer/brand/$slug" "explainer/kit/music/$slug"
  echo "created $d, explainer/shorts/styles/$slug.json, explainer/brand/$slug/, explainer/kit/music/$slug/"
  echo "next: in Claude Code say 'build the channel style for $slug' (skill explainer-channel-style)"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --from-env) MODE=env ;;
    --keys) MODE=file; KEYFILE="$2"; shift ;;
    --skip-install) INSTALL=0 ;;
    --new-channel) new_channel "$2" "${3:-$2}"; exit 0 ;;
    -h|--help) sed -n 2,8p "$0"; exit 0 ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac; shift
done

have() { command -v "$1" >/dev/null 2>&1; }
hint() {
  if have pacman; then echo "sudo pacman -S --needed $*"
  elif have apt-get; then echo "sudo apt-get install -y $*"
  elif have brew; then echo "brew install $*"
  else echo "install: $*"; fi
}

echo "== 1. system tools"
miss=()
for c in python3 node ffmpeg fc-match; do have $c || miss+=($c); done
if [ ${#miss[@]} -gt 0 ]; then
  echo "missing: ${miss[*]}"
  echo "  $(hint python3 nodejs npm ffmpeg fontconfig tesseract)"
  [ $INSTALL = 1 ] && exit 1
fi
have tesseract || echo "optional: tesseract (thumbnail OCR checks) -> $(hint tesseract)"

if [ $INSTALL = 1 ]; then
  echo "== 2. python venv (.venv) + packages"
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
  if [ "${WITH_REMBG:-0}" = 1 ]; then .venv/bin/pip install -q "rembg[cpu]"; else echo "  (rembg skipped; WITH_REMBG=1 ./setup.sh for photo cut-outs on thumbnails)"; fi
  echo "== 3. HyperFrames renderer (npx cache)"
  npx -y hyperframes@0.9.46 --version >/dev/null 2>&1 && echo "  hyperframes 0.9.46 ready" || echo "  WARN: npx hyperframes@0.9.46 failed; check node/npm and network"
  echo "== 4. fonts"
  fc-match -f '%{family}\n' "Noto Sans:black" | grep -qi noto || echo "  Noto Sans not found: $(hint noto-fonts) (or set font_display_file in your brand json)"
fi

echo "== 5. API keys -> .env (values are never printed)"
touch "$ENVF"; chmod 600 "$ENVF"
getv() { { grep -E "^$1=" "$ENVF" 2>/dev/null || true; } | tail -1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//'; }
setv() {
  local k="$1" v="$2" tmp; tmp=$(mktemp)
  grep -vE "^$k=" "$ENVF" > "$tmp" || true
  printf '%s=%s\n' "$k" "$v" >> "$tmp"; mv "$tmp" "$ENVF"; chmod 600 "$ENVF"
}
for k in "${KEYS[@]}"; do
  cur=$(getv "$k")
  case $MODE in
    env)  v="${!k:-}"; [ -n "$v" ] && { setv "$k" "$v"; echo "  $k: saved from environment"; continue; } ;;
    file) v=$({ grep -E "^$k=" "$KEYFILE" || true; } | tail -1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//' || true)
          [ -n "$v" ] && { setv "$k" "$v"; echo "  $k: saved from $KEYFILE"; continue; } ;;
    ask)  if [ -z "$cur" ] && [ -t 0 ]; then
            desc=$(grep -B2 -E "^$k=" .env.example | grep -E '^#' | tail -1 | sed 's/^# //')
            read -r -s -p "  $k ($desc) - paste, or Enter to skip: " v; echo
            [ -n "$v" ] && { setv "$k" "$v"; echo "  $k: saved"; continue; }
          fi ;;
  esac
  [ -n "$cur" ] && echo "  $k: already set" || echo "  $k: not set (feature off)"
done

echo "== 6. check"
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
"$PY" explainer/check_setup.py || { echo "fix the FAIL lines above, then re-run ./setup.sh --skip-install"; exit 1; }
echo
echo "Ready. Activate with: source .venv/bin/activate   then open Claude Code in $ROOT"
echo "New channel: ./setup.sh --new-channel my_slug \"My Channel\""
