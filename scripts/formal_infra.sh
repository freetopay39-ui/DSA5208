#!/usr/bin/env bash
# Run on the role's own VM. Fault commands ONLY on n3, after B DATA_READY.
set -euo pipefail
: "${LAB_RUN:?Set the shared run ID}"
: "${LAB_ROLE:?Set a, b or c}"
[[ "$LAB_RUN" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{7,119}$ ]]
[[ "$LAB_ROLE" =~ ^[abc]$ ]]
cd "$(dirname "$0")/.."
out="$PWD/results/raw/$LAB_RUN/member-$LAB_ROLE"
mkdir -p "$out"
stamp="$(date -u +'%Y%m%dT%H%M%S%N')"
event() { printf '%s\t%s\n' "$(date -u +'%FT%TZ')" "$1" >> "$out/fault-events.tsv"; }
require_c() {
  [[ "$LAB_ROLE" == c ]]
  [[ "$(hostname -s)" == dsa5208-n3 ]]
}
case "${1:-}" in
  snapshot)
    folder="$out/snapshot-$stamp"
    mkdir "$folder"
    date -u +'%FT%TZ' > "$folder/utc.txt"
    hostname > "$folder/hostname.txt"
    git rev-parse HEAD > "$folder/code-commit.txt"
    git status --short > "$folder/git-status.txt"
    sudo docker inspect --format '{{.State.Status}} {{.Image}} {{.HostConfig.NetworkMode}} {{json .HostConfig.CapAdd}}' cassandra > "$folder/container.txt"
    sudo docker exec cassandra nodetool status > "$folder/status.txt"
    sudo docker exec cassandra nodetool describecluster > "$folder/cluster.txt"
    sudo docker exec -u 0 cassandra iptables -S > "$folder/iptables.txt"
    cat "$folder/status.txt"
    echo "Saved: $folder (inspect manually; this is not automatic acceptance)"
    ;;
  stop)
    require_c
    event node_stop_requested
    sudo docker stop cassandra
    sudo docker inspect --format '{{.State.Status}} {{.State.FinishedAt}}' cassandra | tee "$out/stopped-$stamp.txt"
    event node_stop_command_finished
    ;;
  start)
    require_c
    event node_start_requested
    sudo docker start cassandra
    ;;
  partition)
    require_c
    sudo docker exec -u 0 cassandra sh -c 'if iptables -S DSA5208_PARTITION >/dev/null 2>&1; then echo "Existing partition chain: inspect and restore first" >&2; exit 1; fi'
    event partition_requested
    sudo docker exec -u 0 cassandra sh -c '
set -e
iptables -N DSA5208_PARTITION
iptables -A DSA5208_PARTITION -p tcp -m multiport --sports 7000,7001 -j DROP
iptables -A DSA5208_PARTITION -p tcp -m multiport --dports 7000,7001 -j DROP
iptables -I INPUT 1 -j DSA5208_PARTITION
iptables -I OUTPUT 1 -j DSA5208_PARTITION
'
    event partition_rules_added
    ;;
  counters)
    require_c
    sudo docker exec -u 0 cassandra iptables -L DSA5208_PARTITION -n -v | tee "$out/counters-$stamp.txt"
    ;;
  heal)
    require_c
    event heal_requested
    sudo docker exec -u 0 cassandra sh -c '
set -e
iptables -D INPUT -j DSA5208_PARTITION
iptables -D OUTPUT -j DSA5208_PARTITION
iptables -F DSA5208_PARTITION
iptables -X DSA5208_PARTITION
'
    sudo docker exec -u 0 cassandra iptables -S > "$out/iptables-after-$stamp.txt"
    event partition_rules_removed
    ;;
  *) echo "Usage: bash scripts/formal_infra.sh snapshot|stop|start|partition|counters|heal" >&2; exit 2;;
esac
