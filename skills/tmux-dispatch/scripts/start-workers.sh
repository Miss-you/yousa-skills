#!/bin/bash
# start-workers.sh — 创建 tmux session 并启动 N 个 claude worker pane
#
# Usage: start-workers.sh <session-name> <num-workers> [work-dir]
# Example: start-workers.sh cc-batch 3 /Users/apple/Documents/knowledge-card
#
# Output: writes pane ID mapping to /tmp/cc-batch/<session>/pane-map.txt
#   Format: <worker-index> <pane-id>  (one per line)

set -euo pipefail

SESSION="${1:?Usage: start-workers.sh <session> <num-workers> [work-dir]}"
NUM_WORKERS="${2:?Usage: start-workers.sh <session> <num-workers> [work-dir]}"
WORK_DIR="${3:-.}"

# Validate session name
if [[ ! "$SESSION" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Session name must be alphanumeric (with - and _)" >&2
    exit 1
fi

# Ensure batch directory exists with restricted permissions
BATCH_DIR="/tmp/cc-batch/${SESSION}"
mkdir -p -m 700 "$BATCH_DIR"
PANE_MAP="${BATCH_DIR}/pane-map.txt"
> "$PANE_MAP"  # Clear existing map

# Kill existing session if any
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Claude Code sets CLAUDECODE env var which prevents nested sessions.
# We must unset it in tmux so child claude processes can start.
CLAUDE_CMD="unset CLAUDECODE; claude --dangerously-skip-permissions"

# Create new session with first pane, capture its pane ID
FIRST_PANE=$(tmux new-session -d -s "$SESSION" -c "$WORK_DIR" -x 200 -y 50 -P -F '#{pane_id}')
echo "0 ${FIRST_PANE}" >> "$PANE_MAP"

# Start claude in the first pane (unset CLAUDECODE to avoid nested-session check)
tmux send-keys -t "$FIRST_PANE" "$CLAUDE_CMD" Enter

# Create additional panes and start claude in each
for ((i = 1; i < NUM_WORKERS; i++)); do
    # Capture the actual pane ID at creation time
    PANE_ID=$(tmux split-window -t "${SESSION}:0" -c "$WORK_DIR" -P -F '#{pane_id}')
    tmux select-layout -t "${SESSION}:0" tiled
    echo "${i} ${PANE_ID}" >> "$PANE_MAP"
    # Stagger startup to avoid API burst
    sleep 3
    tmux send-keys -t "$PANE_ID" "$CLAUDE_CMD" Enter
done

# Even out the layout
tmux select-layout -t "${SESSION}:0" tiled

echo "Session '${SESSION}' created with ${NUM_WORKERS} workers."
echo "Pane map: ${PANE_MAP}"
echo "Attach with: tmux attach -t ${SESSION}"
