#!/usr/bin/env bash
set -euo pipefail

N="${1:-50}"
SANDBOX="${SANDBOX:-workspace-write}"     # or danger-full-access
APPROVALS="${APPROVALS:-never}"

mkdir -p .agent/logs scripts

for ((i=1; i<=N; i++)); do
  if [[ -f .agent/STOP || -f .agent/DONE ]]; then
    echo "STOP or DONE detected. Exiting."
    break
  fi

  export CODEX_ITERATION="$i"

  echo "=== CYCLE $i / $N: PLANNER ==="
  codex-proxy --search exec --cd . --sandbox "$SANDBOX" --output-last-message ".agent/last_planner.txt"     - < .agent/planner.md     > ".agent/logs/planner_${i}.out" 2> ".agent/logs/planner_${i}.err"

  echo "=== CYCLE $i / $N: WORKER ==="
  codex-proxy exec --cd . --sandbox "$SANDBOX" --ask-for-approval "$APPROVALS" --output-last-message ".agent/last_worker.txt"     - < .agent/worker.md     > ".agent/logs/worker_${i}.out" 2> ".agent/logs/worker_${i}.err"

  echo "=== CYCLE $i / $N: JUDGE ==="
  codex-proxy exec --cd . --sandbox "$SANDBOX" --ask-for-approval "$APPROVALS" --output-last-message ".agent/last_judge.txt"     - < .agent/judge.md     > ".agent/logs/judge_${i}.out" 2> ".agent/logs/judge_${i}.err"

  echo "--- tail progress ---"
  tail -n 25 .agent/progress.md || true
  echo
done
