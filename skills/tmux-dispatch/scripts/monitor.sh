#!/usr/bin/env bash
# monitor.sh — 主监控循环：检测完成 + work-stealing 分发
# Compatible with bash 3.x (macOS) — no associative arrays
#
# Usage: monitor.sh <session> <batch-dir> <num-workers> [poll-interval] [timeout-minutes]
# Example: monitor.sh cc-batch /tmp/cc-batch/cc-batch 3 30 20

set -euo pipefail

SESSION="${1:?Usage: monitor.sh <session> <batch-dir> <num-workers> [poll-sec] [timeout-min]}"
BATCH_DIR="${2:?Usage: monitor.sh <session> <batch-dir> <num-workers> [poll-sec] [timeout-min]}"
NUM_WORKERS="${3:?Usage: monitor.sh <session> <batch-dir> <num-workers> [poll-sec] [timeout-min]}"
POLL_INTERVAL="${4:-30}"
TIMEOUT_MINUTES="${5:-20}"
READINESS_DELAY=8

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Build task queue (sorted)
TASKS=()
for f in "${BATCH_DIR}"/task-*.md; do
    [[ -f "$f" ]] || continue
    BASENAME=$(basename "$f" .md)
    TASKS+=("${BASENAME#task-}")
done
TOTAL=${#TASKS[@]}

if [[ $TOTAL -eq 0 ]]; then
    echo "No tasks found in ${BATCH_DIR}"
    exit 1
fi

echo "=== tmux-dispatch monitor ==="
echo "Session: ${SESSION} | Workers: ${NUM_WORKERS} | Tasks: ${TOTAL}"
echo "Poll: ${POLL_INTERVAL}s | Timeout: ${TIMEOUT_MINUTES}min"
echo ""

# Use flat arrays instead of associative arrays (bash 3.x compat)
# WORKER_TASK[i] = task_id assigned to worker i (empty = idle)
# WORKER_START[i] = epoch timestamp when task was dispatched
WORKER_TASK=()
WORKER_START=()
for ((w = 0; w < NUM_WORKERS; w++)); do
    WORKER_TASK+=("")
    WORKER_START+=(0)
done

# Track next task index for dispatch
NEXT_TASK_IDX=0

# Check if a task is done/failed/pending by looking at files
task_status() {
    local tid="$1"
    if [[ -f "${BATCH_DIR}/done-${tid}" ]]; then
        echo "done"
    elif [[ -f "${BATCH_DIR}/failed-${tid}" ]]; then
        echo "failed"
    else
        echo "pending"
    fi
}

# Dispatch next pending task to a worker
dispatch_next() {
    local worker=$1
    while [[ $NEXT_TASK_IDX -lt $TOTAL ]]; do
        local tid="${TASKS[$NEXT_TASK_IDX]}"
        NEXT_TASK_IDX=$((NEXT_TASK_IDX + 1))
        local status
        status=$(task_status "$tid")
        if [[ "$status" == "pending" ]]; then
            WORKER_TASK[$worker]="$tid"
            WORKER_START[$worker]=$(date +%s)
            "${SCRIPT_DIR}/send-task.sh" "$SESSION" "$worker" "${BATCH_DIR}/task-${tid}.md"
            echo "[$(date +%H:%M:%S)] Worker ${worker} → task-${tid}"
            return 0
        fi
    done
    WORKER_TASK[$worker]=""
    return 1
}

# Skip already-done tasks in log
for tid in "${TASKS[@]}"; do
    if [[ -f "${BATCH_DIR}/done-${tid}" ]]; then
        echo "[resume] Task ${tid} already done"
    fi
done

# Initial dispatch
for ((w = 0; w < NUM_WORKERS; w++)); do
    sleep 2
    dispatch_next "$w" || true
done

echo ""
echo "[$(date +%H:%M:%S)] Initial dispatch done. Entering monitor loop..."
echo ""

# Monitor loop
while true; do
    sleep "$POLL_INTERVAL"

    DONE_COUNT=0
    FAILED_COUNT=0
    for tid in "${TASKS[@]}"; do
        local_status=$(task_status "$tid")
        [[ "$local_status" == "done" ]] && DONE_COUNT=$((DONE_COUNT + 1))
        [[ "$local_status" == "failed" ]] && FAILED_COUNT=$((FAILED_COUNT + 1))
    done

    COMPLETED=$((DONE_COUNT + FAILED_COUNT))
    echo "[$(date +%H:%M:%S)] Progress: ${DONE_COUNT}/${TOTAL} done, ${FAILED_COUNT} failed"

    if [[ $COMPLETED -ge $TOTAL ]]; then
        echo ""
        echo "=== All tasks completed ==="
        echo "Done: ${DONE_COUNT} | Failed: ${FAILED_COUNT} | Total: ${TOTAL}"
        break
    fi

    # Work-stealing: check each worker
    for ((w = 0; w < NUM_WORKERS; w++)); do
        current_tid="${WORKER_TASK[$w]}"
        [[ -z "$current_tid" ]] && continue

        current_status=$(task_status "$current_tid")
        if [[ "$current_status" == "done" ]] || [[ "$current_status" == "failed" ]]; then
            echo "[$(date +%H:%M:%S)] Worker ${w} freed from task-${current_tid} (${current_status})"
            sleep "$READINESS_DELAY"
            WORKER_TASK[$w]=""
            dispatch_next "$w" || true
            continue
        fi

        # Timeout check
        start_ts="${WORKER_START[$w]}"
        now_ts=$(date +%s)
        elapsed=$(( (now_ts - start_ts) / 60 ))
        if [[ $elapsed -ge $TIMEOUT_MINUTES ]]; then
            echo "[$(date +%H:%M:%S)] ⚠ Worker ${w} task-${current_tid} timeout (${elapsed}min)"
        fi
    done
done
