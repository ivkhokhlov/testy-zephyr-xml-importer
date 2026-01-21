#!/usr/bin/env bash
set -euo pipefail
echo "=== Queue (Now) ==="
awk 'BEGIN{p=0} /^## Now/{p=1;next} /^## /{if(p==1){exit}} {if(p==1)print}' .agent/queue.md || true
echo
echo "=== Last Planner ==="
tail -n 30 .agent/last_planner.txt 2>/dev/null || true
echo
echo "=== Last Worker ==="
tail -n 30 .agent/last_worker.txt 2>/dev/null || true
echo
echo "=== Last Judge ==="
tail -n 30 .agent/last_judge.txt 2>/dev/null || true
echo
echo "=== Progress ==="
tail -n 30 .agent/progress.md || true
