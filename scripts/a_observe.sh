#!/usr/bin/env bash
# A 专用：n1 视角拓扑观测器，逐行 JSONL。
# 用法: ./a_observe.sh <run_id> [interval_sec]
# 每轮实验开始前启动，结束后 Ctrl-C。不要在实验中途重启它。
set -uo pipefail

RUN_ID="${1:?usage: a_observe.sh <run_id> [interval_sec]}"
INTERVAL="${2:-5}"
OUT="$HOME/dsa5208/results/raw/A/topology_${RUN_ID}.jsonl"
mkdir -p "$(dirname "$OUT")"
NODE="$(hostname -s)"
echo "observer on $NODE -> $OUT  (interval=${INTERVAL}s, Ctrl-C to stop)"

while true; do
  TS="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
  MONO="$(awk '{print $1}' /proc/uptime)"

  STATUS="$(sudo docker exec cassandra nodetool status 2>&1)"
  RC_STATUS=$?

  UP="$(printf '%s\n' "$STATUS"   | awk '$1=="UN"{print $2}' | jq -R . | jq -sc .)"
  DOWN="$(printf '%s\n' "$STATUS" | awk '$1=="DN"{print $2}' | jq -R . | jq -sc .)"

  HINT_BYTES="$(sudo docker exec cassandra sh -c \
      'du -sb /var/lib/cassandra/hints 2>/dev/null | cut -f1' 2>/dev/null | tail -n1 | tr -dc '0-9')"
  HINT_FILES="$(sudo docker exec cassandra sh -c \
      'ls -1 /var/lib/cassandra/hints 2>/dev/null | wc -l' 2>/dev/null | tail -n1 | tr -dc '0-9')"

  PHI="$(sudo docker exec cassandra nodetool failuredetector 2>/dev/null \
      | awk 'NR>1 && NF>=2 {gsub(/\//,"",$1); printf "%s=%s;",$1,$2}')"

  SCHEMA_N="$(sudo docker exec cassandra nodetool describecluster 2>/dev/null \
      | sed -n '/Schema versions:/,/^$/p' | grep -cE '[0-9a-f]{8}-[0-9a-f]{4}' | tr -dc '0-9')"

  jq -nc \
    --arg run_id "$RUN_ID" --arg observer "$NODE" \
    --arg ts "$TS" --arg mono "$MONO" --arg rc "$RC_STATUS" \
    --argjson up "${UP:-[]}" --argjson down "${DOWN:-[]}" \
    --arg hb "${HINT_BYTES:-0}" --arg hf "${HINT_FILES:-0}" \
    --arg phi "${PHI:-}" --arg sn "${SCHEMA_N:-0}" \
    '{run_id:$run_id, observer:$observer, ts_utc:$ts,
      uptime_s:($mono|tonumber), nodetool_rc:($rc|tonumber),
      up:$up, up_count:($up|length), down:$down, down_count:($down|length),
      hints_bytes:(($hb|select(.!=""))//"0"|tonumber),
      hints_files:(($hf|select(.!=""))//"0"|tonumber),
      failure_detector_phi:$phi,
      schema_version_count:(($sn|select(.!=""))//"0"|tonumber)}' >> "$OUT"

  sleep "$INTERVAL"
done
