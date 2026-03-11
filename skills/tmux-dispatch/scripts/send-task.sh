#!/bin/bash
# send-task.sh — 向指定 tmux pane 发送任务指令
#
# Usage: send-task.sh <session> <worker-index> <task-file-path>
# Example: send-task.sh cc-batch 0 /tmp/cc-batch/cc-batch/task-00.md
#
# Reads pane-map.txt to resolve worker index to actual tmux pane ID.

set -euo pipefail

SESSION="${1:?Usage: send-task.sh <session> <worker-index> <task-file>}"
WORKER_IDX="${2:?Usage: send-task.sh <session> <worker-index> <task-file>}"
TASK_FILE="${3:?Usage: send-task.sh <session> <worker-index> <task-file>}"

if [[ ! -f "$TASK_FILE" ]]; then
    echo "Error: Task file not found: $TASK_FILE" >&2
    exit 1
fi

# Resolve worker index to pane ID via pane map
PANE_MAP="/tmp/cc-batch/${SESSION}/pane-map.txt"
if [[ ! -f "$PANE_MAP" ]]; then
    echo "Error: Pane map not found: $PANE_MAP" >&2
    echo "Did you run start-workers.sh first?" >&2
    exit 1
fi

TARGET=$(awk -v idx="$WORKER_IDX" '$1 == idx { print $2 }' "$PANE_MAP")
if [[ -z "$TARGET" ]]; then
    echo "Error: Worker index ${WORKER_IDX} not found in pane map" >&2
    exit 1
fi

# Use -l (literal) to avoid tmux interpreting special chars in the message
# Send text and Enter separately
tmux send-keys -t "$TARGET" -l "请读取并严格执行 ${TASK_FILE} 中的全部任务指示，完成全部步骤后创建对应的 done 标记文件。"
tmux send-keys -t "$TARGET" Enter

echo "Task sent to worker ${WORKER_IDX} (${TARGET}): $(basename "$TASK_FILE")"
