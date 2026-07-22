#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="$HOME/AIFT-Genesis"
REMOTE="https://github.com/AIFreedomTrustFederation/AIFT-Genesis.git"
TARGET="$PREFIX/bin/aift"

echo "== AIFT Perfect Repair =="

pkg update -y
pkg install -y git python jq coreutils

echo
echo "== Remove broken aift alias from current shell =="
unalias aift 2>/dev/null || true
unset -f aift 2>/dev/null || true
hash -r || true

echo
echo "== Remove broken aift alias from startup files =="
for f in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
  if [ -f "$f" ]; then
    cp "$f" "$f.aift_backup_$(date +%Y%m%d_%H%M%S)"
    sed -i '/alias[[:space:]]\+aift=/d' "$f"
    sed -i '/alias aift=/d' "$f"
  fi
done

echo
echo "== Clone or update AIFT-Genesis =="
cd "$HOME"

if [ ! -d "$REPO/.git" ]; then
  git clone "$REMOTE" "$REPO"
fi

cd "$REPO"

echo
echo "== Discard local bin/aift edits and pull latest =="
git checkout main
git restore bin/aift 2>/dev/null || true
git pull --ff-only origin main

echo
echo "== Install clean aift executable =="
chmod +x "$REPO/bin/aift"
rm -f "$TARGET"
cp -f "$REPO/bin/aift" "$TARGET"
chmod +x "$TARGET"
hash -r || true

echo
echo "== Confirm command resolution =="
type -a aift || true
which aift || true

echo
echo "== Test direct executable =="
"$TARGET" help >/dev/null
"$TARGET" doctor

echo
echo "== Test normal command =="
aift help >/dev/null
aift doctor

echo
echo "== Cleanup old repair script =="
rm -f "$REPO/fix_aift_cli.sh" 2>/dev/null || true

echo
echo "== Git status =="
git status --short

echo
echo "== Ready =="
echo "To create your first trust, run:"
echo '  aift trust init "Zechariah Family Trust"'

read -r -p "Create Zechariah Family Trust now? (y/N): " ans
case "$ans" in
  y|Y|yes|YES)
    aift trust init "Zechariah Family Trust"
    ;;
  *)
    echo "Skipped trust creation."
    ;;
esac
