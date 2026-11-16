#!/usr/bin/env bash
# run_demo.sh — One-command reproduction of the whole experiment.
#
# It launches the login server twice on localhost — first with protections OFF
# (the vulnerable "BEFORE" target) and then with protections ON (the hardened
# "AFTER" target) — and runs the dictionary attack against each, plus the
# lockout demonstration. All transcripts are written to results/ for the report.
#
# Usage:  bash run_demo.sh
set -u
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
mkdir -p results
: > logs/auth.log 2>/dev/null || true

start_server () {   # $1 = on|off
  PROTECT="$1" $PY app.py >"results/server_$1.out" 2>&1 &
  SRV_PID=$!
  # wait for the port to answer
  for _ in $(seq 1 30); do
    if $PY - <<'PYEOF' 2>/dev/null
import socket,sys
s=socket.socket(); s.settimeout(0.3)
sys.exit(0 if s.connect_ex(("127.0.0.1",5000))==0 else 1)
PYEOF
    then return 0; fi
    sleep 0.3
  done
  return 1
}

stop_server () { kill "$SRV_PID" 2>/dev/null; wait "$SRV_PID" 2>/dev/null; }

echo "### [1/3] BEFORE — protections DISABLED ###########################"
$PY init_db.py
start_server off || { echo "server failed to start"; cat results/server_off.out; exit 1; }
$PY attack/brute_force.py --out results/attack_before.txt
stop_server

echo
echo "### [2/3] AFTER — protections ENABLED (dictionary attack) #########"
$PY init_db.py
start_server on || { echo "server failed to start"; cat results/server_on.out; exit 1; }
$PY attack/brute_force.py --out results/attack_after.txt
echo
echo "### [3/3] AFTER — account-lockout demonstration ##################"
$PY attack/lockout_demo.py --out results/lockout_after.txt
stop_server

echo
echo "Done. Transcripts saved in results/ :"
ls -1 results/
