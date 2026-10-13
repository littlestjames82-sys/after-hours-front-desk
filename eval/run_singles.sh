#!/bin/bash
# Run the remaining eval scenarios one at a time, each against a
# freshly started brain + desk stack, retrying a scenario once if it
# errors. The sandbox kills long-lived model servers unpredictably;
# short, self-contained runs are what survive here. Every scenario's
# raw output lands in eval/results-one-<id>.json via the harness.
cd ~/workspace/after-hours-front-desk || exit 1
source scripts/env-sandbox.sh

LLAMA=~/workspace/ghost-os/spike-llama/src/build/bin/llama-server
MODEL=~/workspace/downloads/gemma-3-4b-it-Q4_K_M.gguf

cleanup() {
  pkill -9 -f '[l]lama-server' 2>/dev/null
  pkill -9 -f '[d]esk/server.py' 2>/dev/null
  sleep 2
}

run_one() {
  local id="$1"
  cleanup
  setsid nohup "$LLAMA" -m "$MODEL" --port 8771 -t 2 -c 8192 \
    --parallel 1 --host 127.0.0.1 > "/tmp/llama-$id.log" 2>&1 < /dev/null &
  for _ in $(seq 1 40); do
    curl -s -m 3 http://127.0.0.1:8771/health | grep -q '"ok"' && break
    sleep 3
  done
  timeout 500 python3 eval/run_eval.py --tag "one-$id" --only "$id" \
    > "eval/run-one-$id.log" 2>&1
  python3 - "$id" <<'PYEOF'
import json, sys
sid = sys.argv[1]
try:
    d = json.load(open(f"eval/results-one-{sid}.json"))
    ok = bool(d["results"]) and "score" in d["results"][0]
except Exception:
    ok = False
print("SCENARIO_OK" if ok else "SCENARIO_FAILED")
PYEOF
}

for id in "$@"; do
  echo "===== $id (attempt 1) ====="
  if [ "$(run_one "$id" | tail -1)" = "SCENARIO_OK" ]; then
    echo "===== $id DONE ====="
  else
    echo "===== $id (attempt 2) ====="
    run_one "$id" | tail -1
    echo "===== $id finished attempt 2 ====="
  fi
done
cleanup
echo "ALL_SINGLES_DONE"
