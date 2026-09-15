# 成员 C：运行登记、故障与恢复、分析、复现

先读 [COMMON.md](COMMON.md)。你维护 n3，统一发布 run_id，负责故障证据和结果分析。现有环境与 smoke 已完成，不重新安装；旧的 MEMBER_C_GUIDE.md 用于背景，本手册用于接下来与 A/B 的协同。

## C1. 下一次 VM 连接后先检查现状

```bash
hostname
cd ~/dsa5208
git status --short
git rev-parse HEAD
sudo docker inspect --format '{{.State.Status}} {{.HostConfig.NetworkMode}} {{json .HostConfig.CapAdd}}' cassandra
sudo docker exec -u 0 cassandra iptables -S
sudo docker exec cassandra nodetool status
```

应为 n3、容器运行、Compose bridge 网络、NET_ADMIN；无 DSA5208_PARTITION 残留，三节点最终 UN。若云 VM 关机，先让 A 按约定启动，Docker 容器也要按原流程启动。若仍有分区，按 C7 恢复，不开始 smoke/prepare。

旧演练目录原样保留。按用户决定，旧截图暂不补传，正式实验不受此阻塞；报告若引用旧演练再查找材料或新建 run 重跑。现在的健康检查记录现在的时间，不伪装成过去的恢复记录。

**过程文件：** 当前状态快照、旧演练说明；版本文件已存在，不必每轮重新采集。

## C2. 先与 A/B 协同完成哪些准备

1. A 确认基线 commit、三节点健康、现有 smoke 证据路径。
2. B 同步本地修复版后，按 ROUTING_MR_FIX 的步骤验收 node_stop 及其余场景；不要在尚未同步的新旧程序间混跑正式矩阵。
3. 你与 B 冻结日志字段、判定和图表分母，不先写依赖不存在字段的分析程序。
4. 三人采用 COMMON 的 G0–G6。你发布 ID 不代表已经获得注入通知。

**过程文件：** docs/analysis-notes-c.md、协同记录、检查器抽查结果。

## C3. 创建本轮编号并维护登记表

收到 A 的 BASELINE_READY 后，按 COMMON 第 5 节生成 run_id 并建立登记表。模型、场景、CL、轮次与 B 确认，编号本身只用时间+UUID即可。

将完整 ID 发给 A/B，三人确认使用同一值。你设置 `LAB_ROLE=c`、LAB_OUT，保存 COMMON 的初始快照。

为本轮事件追加一行：

```bash
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'run_registered_by_C' >> "$LAB_OUT/fault-events.tsv"
```

创建 `$LAB_OUT/coordination.md`，记录每个关卡的真实回执，例如：

```text
run_id:
场景 / 模型 / W/R:
A BASELINE_READY 时间与证据:
B DATA_READY 时间与初始化日志:
C 注入请求/完成时间:
A 多数侧验证:
B CQL/路由验证:
C 少数侧/规则验证:
B WORKLOAD_DONE:
C 恢复操作:
A 拓扑恢复:
B 数据恢复:
本轮状态 / 异常 / 待补证据:
```

不要预填成功。每个独立 run 只生成一次 ID；SSH 重连恢复同一值；重新执行历史或更改配置则新建 run，不把前后两轮拼在一起。

## C4. 正常基线时你做什么

保持 n3 正常运行，确认没有规则残留；配合 B 的 prepare 和 run，不注入任何故障。开始/结束分别保存 status，异常时保存日志和资源快照。

首次正常试验，A/B/C 确认：B 的 log 确实使用你的 run_id、原始数据和终端输出齐全、checker 判定可解释。你先用一条历史验证分析流程，再要求 B 扩大样本。

**截图：** 首次正常基线可保存 n3 三节点 UN；无需每条历史截图。

## C5. 单节点停止流程

**前置：** B 已同步修复版并确认 `node_stop` 使用 n1/n2，先按 [修复说明](../ROUTING_MR_FIX.md) 协同完成一次小样本。尚未更新的旧 runner 仍会连接 n3，不能混用。

收到 DATA_READY，确认没有其他正式 run，执行：

```bash
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'node_stop_requested' >> "$LAB_OUT/fault-events.tsv"
sudo docker stop cassandra
sudo docker inspect --format '{{.State.Status}} {{.State.FinishedAt}}' cassandra | tee "$LAB_OUT/stopped-state.txt"
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'node_stop_completed' >> "$LAB_OUT/fault-events.tsv"
```

**协同：** A 确认 n1/n2 UN、n3 DN；B 确认存活侧可以连接。你确认容器 exited。三方完成 G3 后 B 才运行业务请求。

**过程文件：** stopped-state.txt、fault-events.tsv、A 的状态和 B 的连接验收引用。

**截图：** exited 状态（带节点/run_id）；与 A 的 DN 视图配对。

收到 WORKLOAD_DONE 后恢复：

```bash
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'node_start_requested' >> "$LAB_OUT/fault-events.tsv"
sudo docker start cassandra
```

启动需要时间，约 20–30 秒后再查 `nodetool status`，失败时不重复 start。A/C 三节点 UN，B 检查指定数据后记录恢复完成。这是进程停止场景，不叫网络分区，也不宣称等同拔电。

## C6. 网络分区流程

### C6.1 注入前

B 必须先在健康阶段完成 RYW/MR 的 ALL prepare；MW/WFR 使用新的、未复用的 history。你收到 DATA_READY 后：

```bash
hostname
sudo docker inspect --format '{{.HostConfig.NetworkMode}} {{json .HostConfig.CapAdd}}' cassandra
sudo docker exec -u 0 cassandra iptables -S | tee "$LAB_OUT/iptables-before.txt"
```

若存在 DSA5208_PARTITION，先恢复并检查上轮状态。只在 n3 的 bridge 容器中注入，不在 VM 宿主机或整个 VPC 乱加规则。

### C6.2 执行一次

```bash
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'partition_requested' >> "$LAB_OUT/fault-events.tsv"
sudo docker exec -u 0 cassandra sh -c '
set -e
iptables -N DSA5208_PARTITION
iptables -A DSA5208_PARTITION -p tcp -m multiport --sports 7000,7001 -j DROP
iptables -A DSA5208_PARTITION -p tcp -m multiport --dports 7000,7001 -j DROP
iptables -I INPUT 1 -j DSA5208_PARTITION
iptables -I OUTPUT 1 -j DSA5208_PARTITION
'
```

成功通常没有输出；最后单引号不能漏。报错先检查已有规则，不反复运行注入片段。仅阻断 internode 流量，保留 9042 和管理 SSH。

### C6.3 三方验证，再允许 B 开始

```bash
sudo docker exec -u 0 cassandra iptables -L DSA5208_PARTITION -n -v | tee "$LAB_OUT/partition-counters-01.txt"
sudo docker exec cassandra nodetool status | tee "$LAB_OUT/partition-status-01.txt"
```

你应看到 DROP 计数增长，n3 UN、n1/n2 逐渐 DN；A 应看到 n1/n2 UN、n3 DN；B 在 VM2 的 `nc -vz 10.20.0.13 9042` 仍成功。第一次仍全 UN 可以等 20–30 秒后保存 -02 快照，不能因为 DROP 已增长就提前通过。

约 2–3 分钟仍不满足则暂停排查。三方通过后：

```bash
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'partition_verified' >> "$LAB_OUT/fault-events.tsv"
```

通知 B：`[run_id] 三方分区证据齐全，可以运行。` B 此时才对 cross_side 使用 `--partition-verified`。该 flag 是人为声明，不会自动验证故障。

**过程文件：** iptables-before、partition-counters-01/02、partition-status-01/02、fault-events、coordination；保存 A/B 证据路径。

**截图：** 规则和少数侧状态。不要为截图反复注入，也不要删除第一次全 UN 的历史输出。

### C6.4 工作负载期间

不修改规则、不重启、不写测试数据、不 repair。B 保持逻辑 session 并发送请求；你只维护故障状态。若 n3 OOM 或容器退出，立即通知 B，记录为额外故障并终止/另标该 run。

## C7. 恢复分区（B 完成后）

先保存最终计数，再移除：

```bash
sudo docker exec -u 0 cassandra iptables -L DSA5208_PARTITION -n -v > "$LAB_OUT/partition-final-counters.txt"
printf '%s\t%s\n' "$(date -u +'%FT%TZ')" 'heal_requested' >> "$LAB_OUT/fault-events.tsv"
sudo docker exec -u 0 cassandra sh -c '
set -e
iptables -D INPUT -j DSA5208_PARTITION
iptables -D OUTPUT -j DSA5208_PARTITION
iptables -F DSA5208_PARTITION
iptables -X DSA5208_PARTITION
'
```

若之前只执行了一部分，片段可能因缺失某条规则而停止。此时查看 `iptables -S INPUT`、`iptables -S OUTPUT`，只删除仍存在的专用链引用；引用全部消失后才清空/删除该链。每条命令都用 `sudo docker exec -u 0 cassandra` 前缀。链不存在则不再删除。不要运行裸 `iptables -F`。

保存恢复证据：

```bash
sudo docker exec -u 0 cassandra iptables -S > "$LAB_OUT/iptables-after.txt"
sudo docker exec cassandra nodetool status > "$LAB_OUT/after-status-01.txt"
date -u +'%FT%TZ' > "$LAB_OUT/after-check-utc.txt"
```

状态尚未恢复就等待后保存 -02，不能把第一次检查时间当拓扑恢复时间。与 A 的三节点 UN、B 的数据恢复检查共同完成 G5。

自动恢复观察尚未结束时不 repair。拓扑连通、指定对象读到正确数据、所有副本完全同步是不同结论，报告按实际证据描述。

**SSH 意外断开：** 等网络稳定重连，恢复 LAB_RUN/LAB_OUT，检查容器和规则，不猜故障自动消失。需要重跑用新 run_id，旧轮标 aborted/inconclusive 并保存原因。

## C8. 封存并上传本轮证据

记录实际结束状态，追加登记事件：

```bash
# 仅在确实完成后使用 COMPLETED；否则改为 ABORTED/INCONCLUSIVE 并说明原因
printf '%s\t%s\tCOMPLETED\tsee coordination.md\n' "$(date -u +'%FT%TZ')" "$LAB_RUN" >> docs/run-registry-c.tsv
```

按 COMMON 使用 `evidence/c/<run_id>` 分支，精确添加：

```bash
git add -- "results/raw/$LAB_RUN/member-c" docs/run-registry-c.tsv
# 有截图才添加：
git add -- "results/raw/$LAB_RUN/screenshots/member-c"
```

审查 diff → commit → push -u → GitHub PR。PR 描述“故障类型、是否三方验收、是否恢复、缺什么证据”，不要仅写“C 的文件”。A 合并前 B/A 复核时间线。

原快照 .gitignore 忽略 `docs/evidence/**/*.png`，因此新截图按 COMMON 放到 results/raw 下，不要因为被忽略而盲目 `git add -f`。原始日志不包含 token/密钥；`.env;` 若仍存在保持未暂存并核查，不误上传。

## C9. 实现分析：基于现有 JSONL，而不是重写数据库逻辑

当前下载快照没有 analysis 程序，你负责补齐。与 B 确认修订后的日志 schema 后实现 `analysis/summarize.py`（建议入口，尚非已有命令），在 README 写真实用法、输入和输出。

现有 JSONL 包括 run_id、history_id、model、scenario、session_id、operation_id、phase、key、input、returned、write_cl/read_cl、actual_statement_cl、diagnostic_cl、coordinator、timestamp、duration_ms、status、error_type。

修复版 phase 为 setup/prepare/workload/diagnostic，必须分开；setup 错误不计为业务操作。部分正常返回的 actual_coordinator 可能未知，保持 null；不能以 requested 替代。MR 已修复，其他 REPO_CHECK 边界仍需复核。

分析顺序：

1. 校验 JSONL 格式、唯一键、同一文件 run/history 一致性；拒绝混合重复操作。
2. 调用已验收的检查器，生成每 history 判定和原因；保留证据文件与 operation_id。
3. 按模型/场景/业务 CL 分组，分别统计业务读写成功率、错误分类和有效历史数。
4. 反例比例分母只用定义明确的有效历史，blocked/inconclusive 单列；没有有效样本写 N/A。
5. 成功操作 p50/p95 与失败等待时间分开，prepare/diagnostic 不混入业务延迟。
6. MW 的 read_cl 在当前 workload 不起作用，不画成四种不同读配置的性能效果。
7. 对齐 C 的故障事件、A 的 topology JSONL 和 B 的操作时间；跨机时间只辅助，逻辑先后看 session 和程序顺序。

**派生文件：** history-verdicts.csv、summary.csv、validation-errors.txt、输入文件清单和分析版本。正式 raw 不手改；转换/剔除规则透明记录。

## C10. 最小图表与解释

| 图表 | 数据源 | 必须标注 |
|---|---|---|
| 业务读写成功率 | B operations 的 workload phase | 场景、CL、请求数；读写分开 |
| RYW/MR 反例比例 | 每 history verdict | 有效样本数，N/A 和 blocked |
| 延迟 p50/p95 | 成功 workload duration_ms | 样本数、计时范围；失败等待另列 |
| MW/WFR 代表性因果时间线 | B 操作链 + C 分区事件 + A 拓扑 | run/history/operation ID，证据范围 |
| 恢复过程（若测量） | C heal 时间 + A 拓扑 + B 数据探测 | 拓扑恢复与数据可见分别定义 |

B 至少从 raw 重算一项统计，并抽查一条 witness、一个 blocked、一个正常历史。无证据不能写“证明一致”；图表只回答实际 workload 覆盖的问题。

你把分析程序和图表通过独立 `work/c-analysis` 分支与 PR 上传，避免和原始证据 PR 混在一起。记录依赖和命令，另一人能从仓库重新生成。

## C11. 从零复现与最终交付

A 冻结最终源码、备份原数据并安排维护窗口后，你从干净目录/环境仅按 README 复现完整三节点方案。不能只重启 n3 就写成“从零复现”。重用原 VM 清理旧状态前由小组协调，不能自行 `down -v`。

复现覆盖 normal、node_stop、partition、四模型主要历史和分析脚本。出现文档缺口，写入 reproduction-c.md 并将修正入库；不要只接受 A/B 口头步骤。数值不必相同，但操作序列、配置、主要现象和分析流程应可重复。

**复现证据：** 环境/commit、逐条运行命令、实际输出、异常与修订、图表重生成、最终通过/未通过清单。截图保存环境与代表性成功步骤，不代替日志。

你最终交付：run-registry、member-c 证据、分析源码/汇总表/图表、故障方法与局限章节、reproduction-c.md、AI 使用记录。A 整合提交包；GitHub PR 合并后还需要按课程要求提交 Canvas。

## C12. 每日结束前

确认 B 无在途请求；你没有残留分区；A/B 验证恢复；三方成果已上传并备份；由 A 统一停 VM。仅停容器仍有云主机费用。

如果某轮只做了演练就明确写“演练”，如果恢复证据缺失就明确写“证据缺失”；保持记录真实比强行填满每个关卡更重要。
