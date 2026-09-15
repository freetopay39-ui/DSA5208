# 成员 A：基础设施、验收、版本冻结与提交整合

先读 [COMMON.md](COMMON.md)。本手册从三 VM 配置与 smoke 已完成开始，不重复安装。C 统一创建 run_id，B 负责客户端，你负责集群基线和多数侧证据。

## 当前仓库可直接复用的 A 脚本

已核查下载快照中的三个脚本：

```bash
# n1 执行；gate 保存快照并打印 PASS/FAIL，需要人工看结果
bash scripts/a_gate_cluster.sh post-smoke-review

# 观测器依赖 jq；首次使用前检查，缺少时安装
command -v jq
# 缺少 jq 才执行 sudo apt-get install -y jq

# 接收本轮 LAB_RUN 后，在独立 SSH 窗口运行，结束时 Ctrl+C
bash scripts/a_observe.sh "$LAB_RUN" 30
```

gate 输出在 `results/raw/A/checkpoints/<时间>_<名称>/`，不是新的 member-a 目录。脚本即使打印 FAIL 也不保证非零退出码，因此不能以 shell 成功返回自动通过验收。

observer 输出在 `results/raw/A/topology_<run_id>.jsonl`，追加写入，约每轮采样命令执行时间再加 30 秒，并非精确 30 秒周期；使用多次 nodetool，有观测开销，正式比较中保持相同采样策略。取值失败时部分字段会落成 0，不能将其直接解释为真实零 hints 或零 schema。用原始状态核对异常。

这两种原有路径保留，写入本轮 member-a 的 `evidence-index.md`，并在自己的证据 PR 中精确添加对应原路径，不需要移动文件。

`python3 scripts/gen_predictions.py` 会在 `~/dsa5208/docs/predictions.csv` 生成并覆盖 80 行预测。正式运行前修正 REPO_CHECK 指出的逐操作可用性问题；已人工修订过的 CSV 不再次运行生成器覆盖。不得将自动生成内容不经审阅直接当成最终预测。

## A1. 收齐基线成果，确认仓库可作为起点

在 VM1 执行并保存：

```bash
cd ~/dsa5208
mkdir -p docs results/raw/A/checkpoints
git rev-parse HEAD > results/raw/A/checkpoints/post-smoke-commit.txt
git ls-files > results/raw/A/checkpoints/post-smoke-tracked-files.txt
sudo docker exec cassandra nodetool status > results/raw/A/checkpoints/post-smoke-status.txt
sudo docker exec cassandra nodetool describecluster > results/raw/A/checkpoints/post-smoke-cluster.txt
sudo docker exec cassandra cqlsh -e 'DESCRIBE KEYSPACE dsa5208' > results/raw/A/checkpoints/post-smoke-schema.txt
```

最后一条假设实际 keyspace 为 dsa5208；若小组改名，以 config/schema.cql 为准。不要因不匹配再次创建另一套表。

收齐三份版本文件；将 VM/OS/CPU/Java/Docker/Cassandra/driver/镜像 digest、三机私有 IP、RF、dc/rack 和证据路径写入 `docs/versions.md`。

确认 B 的 smoke 记录至少含：实际 CQL/命令、写成功、跨节点读到的值、时间、CL 和当前 commit。若只有口头“通过”，请 B 补一轮带记录的 smoke，不补造旧输出。

**过程文件：** 上面五个 txt、versions.md、现有 smoke 文件索引。

**截图：** 三台 VM 名称/内部 IP/机型；n1 的三节点 UN；B 提供的代表性 smoke 输出。不要截图凭据或完整账单信息。

**协同：** A 把基线 commit 和文件清单发给 B/C；三机 `git rev-parse HEAD` 对齐。镜像构建时间不同可能导致本地自建 image ID 不同，记录原因和基础 digest，不能仅以自建 ID 不同断定数据库版本不同。

## A2. 与 B/C 冻结实验设计

B 主写 `docs/experiment-plan.md`，你审查：

1. 三节点 RF=3、4 种 W/R 配置：ONE/ONE、QUORUM/QUORUM、ALL/ONE、ONE/ALL。
2. 正常、停止 n3、分区多数侧、分区少数侧分别记录。跨侧定向历史另列，不能假装是固定某一侧。
3. RYW/MR 的版本与 timestamp 有明确先后；超时写不当作确定失败；MW/WFR 不用简单读倒退替代。
4. 业务请求和 ONE 诊断读取分开；客户端选 coordinator 不等于副本选择；固定路由需要实际验收。
5. 每种场景的成功条件、错误预期、样本量、超时和恢复条件写清。

**过程文件：** experiment-plan.md、审阅意见、docs/decision-log.md。

**协同关卡：** B 演示一个会被检查器识别的反例和一个不会误判的失败历史；C 能解释图表分母。三人确认后合入 main，记录基线 commit。零异常不代表普遍保证。

本地 runner 路由/MR 修复已完成，先让 B 同步后完成云端小样本闭环；不要以“离线测试通过”替代“集成验收完成”。旧演练截图不阻塞正式实验，只有报告引用旧材料时才补齐证据。

## A3. 每轮 G0：检查健康并向 C 发布 BASELINE_READY

确认上轮无在途工作负载、无未恢复故障；三台分别检查自己的规则，C 负责 n3。你在 n1 检查：

```bash
cd ~/dsa5208
sudo docker exec cassandra nodetool status
sudo docker exec cassandra nodetool describecluster
sudo docker exec -u 0 cassandra iptables -S
```

三节点 UN、schema agreement 和无残留分区满足后通知 C 创建 run_id。UN 仅代表拓扑；B 负责业务测试数据验收，旧数据未收敛不自动等同完成。

接收 C 的 ID，按 COMMON 设置 `LAB_ROLE=a`、LAB_OUT，保存初始快照。保存配置：

```bash
sudo docker compose config > "$LAB_OUT/compose-resolved.yaml"
sudo docker exec cassandra nodetool describecluster > "$LAB_OUT/cluster-before.txt"
sudo docker exec cassandra cqlsh -e 'DESCRIBE KEYSPACE dsa5208' > "$LAB_OUT/schema-before.txt"
```

如果后来加入认证，不把包含密码的 compose 展开内容上传；保存脱敏副本并注明处理方式。目前的私有 IP 和逻辑 rack 可以作为实验架构信息记录。

## A4. 正常场景中你做什么

B 初始化并运行工作负载，你保持集群配置不动，不 repair、不重启、不 pull。初次正式基线或发现异常时保存一个资源快照：

```bash
sudo docker stats --no-stream > "$LAB_OUT/during-resources-01.txt"
sudo docker exec cassandra nodetool status > "$LAB_OUT/during-status-01.txt"
```

B 完成后保存结束状态。异常时保留数据库日志并记录是否有 OOM、意外退出或其他后台负载；这些可能影响延迟，不能全部解释为 CL 的影响。

## A5. 单节点停止：验证多数侧

等 B 的 DATA_READY 和 C 的停止通知后：

```bash
sudo docker exec cassandra nodetool status | tee "$LAB_OUT/node-down-status-01.txt"
```

等待 n1/n2 UN、n3 DN；每 20–30 秒检查一次，保存新文件名。向 C/B 回报：`[run_id] A：多数侧已确认 n3 DN，n1/n2 UN。`

此场景让 B 连接存活 coordinator；把请求发到已停机 n3 会变成连接失败，不能据此评价存活侧 QUORUM 的可用性。

**截图：** 首次该场景保存多数侧 nodetool；与 C 的 exited 状态共同证明“进程停止”。

**你不执行：** 停自己的容器、替 C 恢复 n3、执行 remove/decommission、清空卷。故障节点本轮仍由 C 控制。

## A6. 网络分区：验证多数侧和故障范围

C 注入后，你保存：

```bash
sudo docker exec cassandra nodetool status | tee "$LAB_OUT/partition-status-01.txt"
```

预期 n1/n2 UN、n3 DN；C 的视图应是相反两侧；B 的 n3:9042 连接应仍成功。三方齐全才允许 C 发布 FAULT_VERIFIED。

如果 C 已有 DROP 计数但你仍全部 UN，不立即宣布失败或开始实验，给故障检测时间。约 2–3 分钟仍不符合时，保留状态、暂停工作负载并协同诊断；不要重复往 n1 加一套未经规划的规则。

**过程文件：** partition-status-01/02.txt、需要时的日志、C 的故障事件引用。

**截图：** 多数侧的状态，与 C 的少数侧状态使用同一 run_id。

## A7. 恢复后你验收什么

B WORKLOAD_DONE → C 恢复 → 你确认三节点 UN 和 schema agreement：

```bash
sudo docker exec cassandra nodetool status > "$LAB_OUT/after-status.txt"
sudo docker exec cassandra nodetool describecluster > "$LAB_OUT/cluster-after.txt"
date -u +'%FT%TZ' > "$LAB_OUT/after-utc.txt"
```

B 另外检查预定数据；C 保存规则消失的证据。自动恢复测量期间不主动 repair；若最后需要维护性 repair，必须在正式窗口之外记录操作原因和开始结束时间。

长实验日志按记录的开始时间导出：

```bash
sudo docker logs --timestamps --since '替换为本轮实际UTC开始时间' cassandra > "$LAB_OUT/cassandra-window.log" 2>&1
```

该占位符必须替换，不能直接运行。文件很大时先检查范围是否正确，不清空原始日志。

## A8. 你上传什么，怎么合并三人的成果

按 COMMON 的证据分支流程上传：本轮 member-a、你的 screenshots/member-a、版本/架构文档的实际更新。PR 中注明 run_id、code commit、通过的关卡和遗留问题。

你负责整合三份 PR，合并前检查：

| 检查项 | 应有文件 |
|---|---|
| 本轮是什么 | manifest.json、C 的登记记录 |
| 使用什么代码与配置 | 三方 code-commit、versions、schema/compose |
| 故障是否生效 | A 多数侧、C 少数侧/容器/规则、B CQL 路径 |
| 客户端实际做了什么 | B 原始 JSONL、启动命令与输出 |
| 是否恢复 | C 规则/进程状态、A 拓扑、B 数据检查 |
| 是否能解释结论 | checker 输出和可追溯操作 ID |

证据 PR 可以如实记录失败，不能因为结果不符合预测就拒收。缺必要证据的 run 标为不完整，补测用新 ID。

不要在 A/B/C 各自证据目录重复编辑同一份文件；公共文档由一个负责人修改，其他人通过 PR 评论复核，减少合并冲突。

## A9. 正式数据冻结、复现和最终交付

1. B/C 确认主要实验覆盖、有效样本和分析一致；你冻结源码版本，汇总结果索引。
2. 备份旧成果，安排 C 的干净环境复现窗口和必要权限。不得因复现误删唯一结果。
3. C 按 README 重建，B 支持定位程序问题但不口头补隐含步骤；必要修正进入文档和代码。
4. 你整合 report.pdf、README、源码/脚本、版本锁、原始主实验数据、图表和引用/AI 使用说明。
5. 创建用于提交的版本标记时写清对应 commit；按课程在 Canvas 的要求提交。GitHub push 本身不是 Canvas 提交。
6. 三人确认备份和提交完成后，停止/删除不再需要的云资源，检查遗留磁盘/IP。只停止容器不能停止 VM 计费。

**你最终交付：** versions.md、architecture/安装说明、完整 README、member-a 证据、结果索引、整合后的 PDF 与提交包，以及 PR 合并记录。
