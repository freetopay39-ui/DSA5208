#!/usr/bin/env bash
<<<<<<< HEAD
set -uo pipefail

. /etc/os-release

echo "node: $(hostname -s)"
echo "cpu_model: $(lscpu | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2}')"
echo "internal_ip: $(hostname -I | awk '{print $1}')"
echo "captured_utc: $(date -u +%FT%TZ)"
=======
# 三台都跑，输出交给 A 汇总成 docs/versions.md
set -uo pipefail
. /etc/os-release
echo "node: $(hostname -s)"
echo "internal_ip: $(hostname -I | awk '{print $1}')"
echo "captured_utc: $(date -u +%FT%TZ)"
echo "cpu_model: $(lscpu | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2}')"
>>>>>>> 6785a3a (feat: add version inventory collection script)
echo "ubuntu: ${VERSION_ID} (${VERSION_CODENAME})"
echo "kernel: $(uname -r)"
echo "docker_engine: $(sudo docker version --format '{{.Server.Version}}')"
echo "compose: $(sudo docker compose version --short)"
echo "containerd: $(containerd --version | awk '{print $3}')"
<<<<<<< HEAD
echo "base_image_digest: $(sudo docker image inspect cassandra:5.0.9 --format '{{index .RepoDigests 0}}')"
echo "built_image_id: $(sudo docker image inspect dsa5208-cassandra:5.0.9 --format '{{.Id}}')"
=======
echo "base_image_digest: $(sudo docker image inspect cassandra:5.0.9 --format '{{index .RepoDigests 0}}' 2>/dev/null || echo '(unavailable)')"
echo "built_image_id: $(sudo docker image inspect dsa5208-cassandra:5.0.9 --format '{{.Id}}' 2>/dev/null || echo '(unavailable)')"
>>>>>>> 6785a3a (feat: add version inventory collection script)
echo "cassandra: $(sudo docker exec cassandra cassandra -v 2>/dev/null)"
echo "nodetool: $(sudo docker exec cassandra nodetool version 2>/dev/null | tr -d '\r')"
echo "jvm: $(sudo docker exec cassandra java -version 2>&1 | head -n1)"
echo "---"
