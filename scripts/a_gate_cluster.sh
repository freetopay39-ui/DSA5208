#!/usr/bin/env bash
# A 专用：三节点集群验收关卡。用法: ./a_gate_cluster.sh <checkpoint_name>
set -uo pipefail
NAME="${1:?usage: a_gate_cluster.sh <checkpoint_name>}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="$HOME/dsa5208/results/raw/A/checkpoints/${TS}_${NAME}"
mkdir -p "$DIR"
X() { sudo docker exec cassandra "$@"; }

X nodetool status          > "$DIR/nodetool-status.txt"        2>&1
X nodetool describecluster > "$DIR/nodetool-describecluster.txt" 2>&1
X nodetool gossipinfo      > "$DIR/nodetool-gossipinfo.txt"    2>&1
X nodetool info            > "$DIR/nodetool-info.txt"          2>&1
X nodetool netstats        > "$DIR/nodetool-netstats.txt"      2>&1
X nodetool tpstats         > "$DIR/nodetool-tpstats.txt"       2>&1
X nodetool failuredetector > "$DIR/nodetool-failuredetector.txt" 2>&1
X nodetool statushandoff   > "$DIR/nodetool-statushandoff.txt" 2>&1
X cassandra -v             > "$DIR/cassandra-version.txt"      2>&1
sudo docker image inspect cassandra:5.0.9 \
  --format '{{index .RepoDigests 0}}' > "$DIR/base-image-digest.txt" 2>&1

UN=$(awk '$1=="UN"{c++} END{print c+0}' "$DIR/nodetool-status.txt")
DN=$(awk '$1=="DN"{c++} END{print c+0}' "$DIR/nodetool-status.txt")
SCHEMA=$(sed -n '/Schema versions:/,/^$/p' "$DIR/nodetool-describecluster.txt" \
         | grep -cE '[0-9a-f]{8}-[0-9a-f]{4}')

{
  echo "checkpoint: $NAME"
  echo "captured_utc: $(date -u +%FT%TZ)"
  echo "observer_node: $(hostname -s)"
  echo "un_count: $UN"
  echo "dn_count: $DN"
  echo "schema_version_count: $SCHEMA"
} | tee "$DIR/_summary.yaml"

echo "-------- GATE --------"
[ "$UN" -eq 3 ]     && echo "PASS  三节点 UN"            || echo "FAIL  UN=$UN (期望3) —— 若正处于故障场景这是预期的"
[ "$SCHEMA" -eq 1 ] && echo "PASS  schema agreement"     || echo "FAIL  schema 版本数=$SCHEMA (期望1)"
echo "evidence -> $DIR"
