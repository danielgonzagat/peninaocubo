#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# PATH: venv + Homebrew primeiro
export PATH="$ROOT/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p logs

log(){ printf '%s %s\n' "$(date '+%F %T')" "$*"; }

# Defaults (podem vir de export já feitos no ambiente)
: "${TOP:=60}"
: "${JITTER:=0.0005}"
: "${POP:=8}"
: "${GEN:=1}"
: "${NOV_MIN:=0.0001}"
: "${CANARY_EVERY:=5}"
: "${REAL:=1}"
: "${FUSE_SUBPROC_TIMEOUT:=120}"
: "${FUSE_POLICY:=staging}"

while :; do
  log "run smart (policy=$FUSE_POLICY, top=$TOP)"
  FUSE_REAL="$REAL" FUSE_SUBPROC_TIMEOUT="$FUSE_SUBPROC_TIMEOUT" \
  python scripts/run_smart.py --top "$TOP" --mode auto --seed "$RANDOM" \
    --jitter "$JITTER" --pop "$POP" --gen "$GEN" --novelty-min "$NOV_MIN" \
    | tee -a logs/omega_forever.log

  # placar + publicação + autocommit
  python scripts/summarize_fusion.py | tee -a logs/omega_forever.log
  ./scripts/publish_score.sh || true
  ./scripts/autocommit_data.sh || true

  # canário strict periódico
  if (( $(date +%s) % CANARY_EVERY == 0 )); then
    log "🐤 canário strict"
    FUSE_POLICY=strict FUSE_REAL="$REAL" FUSE_SUBPROC_TIMEOUT="$FUSE_SUBPROC_TIMEOUT" \
    python scripts/run_smart.py --top "$((TOP/3))" --mode auto --seed "$RANDOM" \
      --jitter "$JITTER" --pop "$POP" --gen "$GEN" --novelty-min "$NOV_MIN" \
      | tee -a logs/omega_forever.log
    ESCALATE_POLICY=strict python scripts/escalate_passed.py | tee -a logs/omega_forever.log
    python scripts/summarize_fusion.py | tee -a logs/omega_forever.log
    ./scripts/publish_score.sh || true
    ./scripts/autocommit_data.sh || true
  fi

  sleep 3
done
