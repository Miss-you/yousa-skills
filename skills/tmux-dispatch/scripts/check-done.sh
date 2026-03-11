#!/bin/bash
# check-done.sh — 检查任务完成状态
#
# Usage: check-done.sh <batch-dir> [task-id]
#   No task-id: show all status
#   With task-id: check specific task, exit 0 if done

set -euo pipefail

BATCH_DIR="${1:?Usage: check-done.sh <batch-dir> [task-id]}"

if [[ -n "${2:-}" ]]; then
    # Check specific task
    TASK_ID="$2"
    if [[ -f "${BATCH_DIR}/done-${TASK_ID}" ]]; then
        echo "done"
        exit 0
    elif [[ -f "${BATCH_DIR}/failed-${TASK_ID}" ]]; then
        echo "failed"
        exit 2
    else
        echo "running"
        exit 1
    fi
else
    # Show all status
    TOTAL=$(find "${BATCH_DIR}" -maxdepth 1 -name 'task-*.md' 2>/dev/null | wc -l | tr -d ' ')
    DONE=$(find "${BATCH_DIR}" -maxdepth 1 -name 'done-*' 2>/dev/null | wc -l | tr -d ' ')
    FAILED=$(find "${BATCH_DIR}" -maxdepth 1 -name 'failed-*' 2>/dev/null | wc -l | tr -d ' ')
    RUNNING=$((TOTAL - DONE - FAILED))

    echo "Total: ${TOTAL} | Done: ${DONE} | Failed: ${FAILED} | Running/Pending: ${RUNNING}"

    # List status per task
    for task_file in "${BATCH_DIR}"/task-*.md; do
        [[ -f "$task_file" ]] || continue
        BASENAME=$(basename "$task_file" .md)
        ID="${BASENAME#task-}"
        if [[ -f "${BATCH_DIR}/done-${ID}" ]]; then
            STATUS="✓ done"
        elif [[ -f "${BATCH_DIR}/failed-${ID}" ]]; then
            STATUS="✗ failed"
        else
            STATUS="… pending/running"
        fi
        echo "  ${ID}: ${STATUS}"
    done
fi
