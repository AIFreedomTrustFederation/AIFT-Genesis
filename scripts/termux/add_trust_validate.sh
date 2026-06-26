#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="$HOME/AIFT-Genesis"
TARGET="$PREFIX/bin/aift"

cd "$REPO"

git checkout main
git pull --ff-only origin main

python3 <<'PY'
from pathlib import Path

p = Path("bin/aift")
s = p.read_text()

if "cmd_trust_validate()" not in s:
    insert = r'''
cmd_trust_validate() {
  require_command git
  require_command python3

  local target="${1:-$PWD}"

  [ -d "$target" ] || fail "trust path does not exist: $target"

  local required_files=(
    "README.md"
    "TRUST.md"
    "IDENTITY.md"
    "VALUES.md"
    "GOVERNANCE.md"
    "AI_STEWARD.md"
    "TREE_OF_LIFE.md"
    "MAP.md"
    "ECONOMY.md"
    "FEDERATION_LINK.md"
    "LOCAL_MANIFEST.json"
  )

  echo "AIFT Trust Validate"
  echo "TRUST: $target"
  echo

  for f in "${required_files[@]}"; do
    if [ ! -f "$target/$f" ]; then
      fail "missing required file: $f"
    fi
  done
  echo "Required files: OK"

  validate_no_unreplaced_tokens "$target"
  echo "Generator variables: OK"

  validate_no_placeholder_language "$target"
  echo "Unfinished markers: OK"

  validate_json "$target"
  echo "JSON: OK"

  if [ -d "$target/.git" ]; then
    (
      cd "$target"
      git status --short
      if [ -n "$(git status --porcelain)" ]; then
        fail "trust git working tree is not clean"
      fi
    )
    echo "Git working tree: OK"
  else
    fail "trust is not a git repository"
  fi

  echo
  echo "Trust validation passed."
}
'''
    marker = '\ncmd_trust_list() {'
    s = s.replace(marker, insert + marker)

s = s.replace('aift trust list', 'aift trust list\n  aift trust validate [path]')

old = '''      list)
        cmd_trust_list
        ;;
      *)'''
new = '''      list)
        cmd_trust_list
        ;;
      validate)
        shift 2
        cmd_trust_validate "${1:-$PWD}"
        ;;
      *)'''
if old in s and 'cmd_trust_validate "${1:-$PWD}"' not in s:
    s = s.replace(old, new)

s = s.replace('echo "Usage: aift trust init \\"Trust Name\\" | aift trust list"', 'echo "Usage: aift trust init \\"Trust Name\\" | aift trust list | aift trust validate [path]"')

p.write_text(s)
PY

chmod +x bin/aift
cp -f bin/aift "$TARGET"
chmod +x "$TARGET"
hash -r || true

aift doctor
aift trust validate "$HOME/AIFT-Trusts/zechariah-family-trust"

git add bin/aift
git commit -m "Add trust validation command" || true
git push origin main

echo
echo "Done. You can now run:"
echo "  aift trust validate ~/AIFT-Trusts/zechariah-family-trust"
