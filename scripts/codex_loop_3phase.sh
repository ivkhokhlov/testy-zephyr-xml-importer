#!/usr/bin/env bash
set -euo pipefail

N="${1:-50}"
SANDBOX="${SANDBOX:-danger-full-access}"     # or danger-full-access
APPROVALS="${APPROVALS:-never}"

mkdir -p .agent/logs scripts

ts() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  echo "[$(ts)] $*"
}

run_phase() {
  local name="$1"
  local input="$2"
  local last_msg="$3"
  local out_log="$4"
  local err_log="$5"
  shift 5
  local -a cmd=(codex-proxy "$@")

  log "=== ${name} START ==="
  log "${name}: input=${input} last=${last_msg}"
  log "${name}: out=${out_log} err=${err_log}"
  if "${cmd[@]}" --cd . --sandbox "$SANDBOX" --output-last-message "$last_msg" \
    - < "$input" > "$out_log" 2> "$err_log"; then
    log "=== ${name} DONE ==="
  else
    local rc=$?
    log "=== ${name} FAILED (status=${rc}) ==="
    log "${name}: see ${err_log}"
    exit "$rc"
  fi
}

log "loop start: cycles=${N} sandbox=${SANDBOX} approvals=${APPROVALS}"

for ((i=1; i<=N; i++)); do
  if [[ -f .agent/STOP || -f .agent/DONE ]]; then
    reason=""
    [[ -f .agent/STOP ]] && reason="${reason} .agent/STOP"
    [[ -f .agent/DONE ]] && reason="${reason} .agent/DONE"
    log "stop detected:${reason} (exiting)"
    break
  fi

  export CODEX_ITERATION="$i"

  log "cycle ${i}/${N} begin (CODEX_ITERATION=${CODEX_ITERATION})"

  run_phase "PLANNER" ".agent/planner.md" ".agent/last_planner.txt" \
    ".agent/logs/planner_${i}.out" ".agent/logs/planner_${i}.err" \
    --search exec

  run_phase "WORKER" ".agent/worker.md" ".agent/last_worker.txt" \
    ".agent/logs/worker_${i}.out" ".agent/logs/worker_${i}.err" \
    exec

  run_phase "JUDGE" ".agent/judge.md" ".agent/last_judge.txt" \
    ".agent/logs/judge_${i}.out" ".agent/logs/judge_${i}.err" \
    exec

  log "progress tail: .agent/progress.md (last 25 lines)"
  tail -n 25 .agent/progress.md || true
  echo
done
