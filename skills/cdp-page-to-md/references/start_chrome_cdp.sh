#!/bin/bash
# Start Chrome with CDP remote debugging port.
# Uses a dedicated profile directory (Chrome refuses CDP on default profile).
# Cookies are loaded from storage_state.json by the upload script, not from this profile.
#
# Usage: ./start_chrome_cdp.sh [port]
#
# 1. Close all Chrome windows first (Cmd+Q)
# 2. Run this script
# 3. Then use --cdp-endpoint http://localhost:9222 in upload_note.py

PORT="${1:-9222}"
PROFILE_DIR="$HOME/.config/rednote-toolkit/chrome-cdp-profile"
mkdir -p "$PROFILE_DIR"

echo "Starting Chrome with CDP on port $PORT..."
echo "Profile: $PROFILE_DIR"

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  --disable-blink-features=AutomationControlled
