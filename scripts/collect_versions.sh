#!/usr/bin/env bash
set -uo pipefail

. /etc/os-release

echo "node: $(hostname -s)"
echo "cpu_model: $(lscpu | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2}')"
echo "internal_ip: $(hostname -I | awk '{print $1}')"
echo "captured_utc: $(date -u +%FT%TZ)"
echo "ubuntu: ${VERSION_ID} (${VERSION_CODENAME})"
echo "kernel: $(uname -r)"
echo "docker_engine: $(sudo docker version --format '{{.Server.Version}}')"
echo "compose: $(sudo docker compose version --short)"
echo "containerd: $(containerd --version | awk '{print $3}')"
echo "base_image_digest: $(sudo docker image inspect cassandra:5.0.9 --format '{{index .RepoDigests 0}}')"
echo "built_image_id: $(sudo docker image inspect dsa5208-cassandra:5.0.9 --format '{{.Id}}')"
echo "cassandra: $(sudo docker exec cassandra cassandra -v 2>/dev/null)"
echo "nodetool: $(sudo docker exec cassandra nodetool version 2>/dev/null | tr -d '\r')"
echo "jvm: $(sudo docker exec cassandra java -version 2>&1 | head -n1)"
echo "---"
