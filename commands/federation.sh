#!/usr/bin/env bash
set -euo pipefail

AIFT_OS="$HOME/AIFT/aift-os.sh"

if [ ! -x "$AIFT_OS" ]; then
  echo "AIFT OS command not found at: $AIFT_OS"
  exit 1
fi

case "${1:-help}" in
  status) "$AIFT_OS" status ;;
  graph) "$AIFT_OS" graph ;;
  dashboard) "$AIFT_OS" dashboard ;;
  verify) "$AIFT_OS" verify ;;
  deps) "$AIFT_OS" deps ;;
  pull) "$AIFT_OS" pull ;;
  update) "$AIFT_OS" update ;;
  doctor) "$AIFT_OS" doctor ;;
  full) "$AIFT_OS" full ;;
  help|*)
    echo "AIFT Federation Commands"
    echo
    echo "Usage:"
    echo "  aift federation status"
    echo "  aift federation graph"
    echo "  aift federation dashboard"
    echo "  aift federation verify"
    echo "  aift federation deps"
    echo "  aift federation pull"
    echo "  aift federation update"
    echo "  aift federation doctor"
    echo "  aift federation full"
    ;;
esac
