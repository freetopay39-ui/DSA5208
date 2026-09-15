# 成员 B：实验程序、检查器、运行与原始历史

先读 [COMMON.md](COMMON.md)。配置与 smoke 完成不表示四类正式实验已实现。你的工作是把课程定义转换成可记录、可检查、可重复的操作历史。C 管理 run_id，你负责 manifest 与客户端。

## B1. 先清点已有程序，不猜入口

在 VM2：

```bash
cd ~/dsa5208
git ls-files
git rev-parse HEAD
cat config/schema.cql
```

已从下载快照核验：runner 为 `python -m src.run`，支持 `prepare`、`run`、`check`；实现位于 src/run.py、client.py、workloads.py、checkers.py，依赖位于 requirements-lock.txt。当前没有 analysis 目录/分析程序，也没有 README。首先把本手册的真实命令整理入仓库 README。

本地修复版已按场景选路由：normal/cross_side=n1→n3，node_stop/majority=n1→n2，minority=n3→n3；初始化只连接需要的节点，连接失败保存 setup 记录，MR 成功读取无行判 witness。11 项离线测试通过，详见 [修复说明](../ROUTING_MR_FIX.md)。用户已授权上传，云端尚未运行验收；先同步并做小样本验收，日志去重、其他检查器边界等仍见 REPO_CHECK。

继续维护 src/client.py、src/workloads.py、src/checkers.py、src/run.py。字段与现有 schema 对齐；需要改表时采用明确的新表/迁移并更新 A/C 的基线，不在正式数据中途偷偷改 schema。

**过程文件：** README 的实际入口、依赖锁、schema、源码、docs/experiment-plan.md。

**协同：** A 审核一致性语义和配置，C 核对原始日志是否足够分析。

## B2. 实验客户端必须满足的要求

1. 每条 statement 显式设置读或写 CL；manifest 记录实际配置。
2. 禁止静默自动重试和 speculative execution；记录明确超时，保持连接初始化在操作计时之外。
3. 固定 coordinator 时不能仅提供一个 contact point：驱动可能发现其他节点。使用已验收的单节点路由策略，并保存实际 coordinator；正常场景的副本来源如需推断，要有 trace 等证据。
4. 用一个逻辑 session 的操作序号确定 RYW/MR/MW/WFR 的程序顺序。切换 coordinator 可以切换连接，但不能丢掉逻辑 session。
5. 对 RYW/MR 固定单 writer、无 TTL/删除、明确版本和递增 mutation timestamp；时间戳策略记录在 manifest，避免 LWW 冲突被误当复制顺序问题。
6. 对 MW/WFR 保存不可变前驱/后继及依赖 ID；前驱不覆盖、不删除、不设置 TTL。
7. JSONL 每次追加并 flush，结果文件已存在时拒绝新 run 覆盖。记录启动/结束、退出码和异常；中断保留部分文件。
8. 连接错误、unavailable、读超时、写超时、客户端超时分别记录。写超时是结果不确定，可能已写入部分副本。

实际 coordinator 获取方式依 driver 版本验收，未知值用 null，不用目标地址冒充。tracing 会有额外开销；诊断运行与正式延迟采样分开。

## B3. 四种模型如何操作和判定

下表使用概念对象 x/a/b，映射到当前 schema 的真实列名后实现；不要直接把伪代码当 CQL。

| 模型 | 工作负载 | 判定与前置条件 |
|---|---|---|
| RYW | U 成功写 x=v1 → U 读 x | 后一读成功且 v<v1 或缺失才是反例；前一写失败/不确定不作为成功前置 |
| MR | 单 writer 有序更新；同一 reader 连续读 x | 成功读到新版后成功读到更旧版本；操作顺序和版本意义明确 |
| MW | U 成功写 a → U 成功写依赖 a 的 b | 隔离 n3 已有 b 而不可变 a 缺失，结合故障与本地副本证据；读倒退不能替代 MW |
| WFR | P 写 a → U 实际读到 a → U 成功写依赖 a 的 b | 在处理 b 的隔离 n3 验证 b 存在、a 不存在；必须保留 U.read(a) 的实际结果 |

**定向分区历史：** n3 隔离，a 在多数侧产生；同一逻辑 U 将后继写发到 n3。n3 的 ONE 诊断读无法向其他副本成功取数据，因此更容易形成可解释的副本证据。前驱不可变、无删除/TTL 是必要限制。没有这些证据只标 candidate/inconclusive。

正常/多数侧的 coordinator 可以转发请求，观察者读 b 后读不到 a 本身不足以证明处理 b 的副本缺 a。

高 CL 的后继写或读取在少数侧可能被阻断，这时记录 blocked，不能说“没有反例所以证明成立”。ALL/QUORUM 业务读和定位隔离副本的 ONE 诊断读必须用 phase 区分。

**过程文件：** 每模型伪代码与 CQL 映射、检查器规则、正反例日志、每次实际实验完整 JSONL。

## B4. 检查器先通过这些验收

至少构造并验证：

1. 成功写 v1 后成功读 v0 → RYW witness。
2. 当前 v0/v1 workload：读 v1 后读 v0 或成功读取无行 → MR witness；扩展更多版本时同步扩展检查器。
3. 写 timeout 后读旧值 → 不应自动判 RYW witness。
4. 返回无行的成功读取与读取异常 → 两种不同结果。
5. 两个任意副本的缺前驱 → 候选，不直接定 MW/WFR。
6. 同一隔离副本上不可变前驱缺失、后继存在，且依赖链完整 → 该受控模型的 witness。
7. 无有效历史 → N/A，而非 0% 反例。
8. 同一 JSONL 重复输入分析 → 不应重复计数；用 run_id/history_id/operation_id 识别。

保存每个验收样本、预期判定、实际输出到源码测试目录或 `results/validation/`；A/C 抽查。只有检查器可信才扩大规模。

## B5. 运行前冻结预测和矩阵

模型：RYW、MR、MW、WFR。W/R：ONE/ONE、QUORUM/QUORUM、ALL/ONE、ONE/ALL。场景视角：normal、node_stop、partition_majority、partition_minority，最多 64 个组合单元；不适用或无法形成有效历史的单元显式注明原因。跨分区的定向历史另列，若四模型/四配置全部展开再加 16 单元，即仓库生成器的 80 行。修复版已有这些场景的路由，但仍需云端逐场景小样本验收。

不要认为所有模型都必须在每个单元产生可判断的反例；比如少数侧 QUORUM 会阻止历史完成。这本身是可用性结果。

先做每单元 5–20 条冒烟历史，测定耗时；可用单元可采用 3 轮各 100 条，不可用单元用较少请求（例如每轮 20 次）避免长时间超时。样本策略在运行前固定并解释；课程没有要求固定 500 条。

预测内容至少包括：ONE/ONE 可能旧读、QUORUM 的可用副本要求、ALL 在一个节点不可用时的影响、read repair 和 timestamp 的作用、MW/WFR 不能仅凭 W+R>RF 推导。

**过程文件：** experiment-plan.md、matrix 配置、预计运行时间、A/C 审阅记录。

## B6. 每轮开始：接收 C 的 ID，建立 manifest

按 COMMON 设置 `LAB_ROLE=b` 和 LAB_OUT，保存初始快照。你创建本轮 manifest.json，先写计划字段，结束后补实际时间/状态；不要把未发生的时间和结果预填。

建议记录：

```json
{
  "run_id": "C发布的真实ID",
  "code_commit": "本轮实际源码commit",
  "model": "ryw",
  "scenario": "normal",
  "read_cl": "ONE",
  "write_cl": "ONE",
  "diagnostic_cl": null,
  "seed": 1,
  "planned_histories": 20,
  "table": "填写实际表名",
  "routing": "填写实际coordinator计划",
  "timestamp_policy": "填写实际策略",
  "request_timeout_seconds": 10,
  "status": "planned",
  "started_utc": null,
  "ended_utc": null
}
```

示例值不是强制真实参数；运行前与计划一致，运行后记录实际执行参数与停止原因。

初始化使用全新 history_id。需要“所有副本先有 v0”的试验在健康阶段以足够 CL 初始化并验证，再发 DATA_READY。初始化和诊断不混进测量阶段成功率/延迟。

## B7. 正常场景

### 真实入口：先做一条受控历史

在 VM2 项目根目录，首次安装或没有可用虚拟环境时：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m src.run --help
python -m src.run run --help
```

已有可用虚拟环境只需激活，不反复安装。若 python3-venv 缺失再安装对应 Ubuntu 包。务必从仓库根目录运行模块。

设置一条新 history 和日志（本例 RYW/ONE/ONE，参数按冻结计划改）：

```bash
export LAB_MODEL='ryw'
export LAB_HISTORY="${LAB_RUN}-${LAB_MODEL}-h001"
export LAB_LOG="$LAB_OUT/${LAB_HISTORY}.jsonl"
test ! -e "$LAB_LOG"
```

最后一条必须成功（`echo $?` 为 0）；已有文件说明需要检查之前是否执行过，不能直接重复写入。当前 Logger 是追加模式，重复执行会混合 operation_id。

健康状态下初始化一次：

```bash
python -m src.run prepare --model "$LAB_MODEL" --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG"
```

RYW/MR 的 prepare 必须在 JSONL 中出现 `phase=prepare, operation_id=0, status=ok` 的 ALL 写 v0。程序退出 0 不代表该操作成功，要看实际记录。MW/WFR 的 prepare 无写入；需使用全新 history，并确认 a/b 不存在且本轮不复用。

normal 在健康三节点直接执行：

```bash
python -m src.run run --model "$LAB_MODEL" --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG" --scenario normal --write-cl ONE --read-cl ONE
```

保存判定（修复版将 driver 导入延后，check 和 --help 不需要连接数据库或安装 driver）：

```bash
mkdir -p "results/processed/$LAB_RUN"
python -m src.run check --model "$LAB_MODEL" --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG" | tee "results/processed/$LAB_RUN/${LAB_HISTORY}-checker.txt"
```

当前 check 实际只按 history/model 过滤，不按 --run-id 过滤，因此一个 log 只对应一个 run/history；--run-id 不能替你防止混入旧记录。判定仍需按 REPO_CHECK 人工复核，正式批量前修复。

G0/G1/G2 完成后直接运行，无需 C 注入。使用实际已验证的程序命令，并将**完整命令**写入 `member-b/command.txt`。日志至少分为 `operations.jsonl` 和终端输出；设置 LAB_RUN 环境变量本身不会自动传给程序，runner 必须显式读取它或接受对应参数。

终端可用 `script` 保存交互执行过程：

```bash
script -q -e "$LAB_OUT/runner-terminal.txt"
# 在新打开的 shell 里执行 README 中已验证的实际 runner 命令
# 等命令结束后记录退出码，再 exit 结束终端记录
```

上面注释处不是现成启动入口。程序本身必须另外保存 JSONL；不要把终端总用时或 cqlsh 启动时间当成数据库单次操作延迟。

结束后生成 checker 输出到 `results/processed/<run_id>/`，并记录 WORKLOAD_DONE。保留原始错误，不能因为全部零反例就丢弃该轮。

## B8. 节点停止与网络分区：何时配合 C

### 单节点停止

1. 初始化完成，通知 C 可停止 n3。
2. A 确认 n3 DN；你确认存活侧可连接。
3. 将业务 coordinator 固定或限制在存活侧，运行指定 CL。
4. 若计划包含连已停节点的测试，单列 connection-error 场景，不混入副本不足结果。
5. WORKLOAD_DONE 后通知 C 恢复，验证数据并记录。

### 网络分区

**现有程序的准确执行位置：** RYW/MR 先执行上一节 prepare，然后等 C 注入和三方 G3 通过，才执行下面 run；不要在隔离后 prepare ALL。使用同一 LAB_RUN/HISTORY/LOG，run 每条历史只执行一次：

```bash
python -m src.run run --model "$LAB_MODEL" --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG" --scenario partition_cross_side --write-cl ONE --read-cl ONE --partition-verified
```

`--partition-verified` 只是你输入的布尔声明，程序不会检测 iptables/拓扑；必须先取得 A/C/B 的真实证据。不通过时不加标志、不声称已验证。normal 不加该标志。

MW 当前没有使用业务 read_cl，只有 ONE 诊断读；所以改 MW 的 `--read-cl ALL` 不会产生 ALL 业务读取，应作为不适用维度注明，不能当作不同读配置的实验。

1. 健康阶段完成本轮需要的前置状态；停止新请求并确认在途请求结束。
2. C 注入，A/C 保存两侧拓扑。
3. 你验证 n3 CQL 可达：

```bash
nc -vz 10.20.0.13 9042 > "$LAB_OUT/n3-cql-reachability.txt" 2>&1
```

4. 在 G3 通过后运行指定侧或跨侧工作负载；路由必须符合 manifest。
5. 诊断读取单列 phase 和证据。不要在同一 run 中临时改变 CL 直到“终于成功”。
6. 工作负载结束后通知 C 恢复；如果准备测恢复过程，事先约定查询方法、频率、截止时间和何时移除规则。

**截图：** 一条代表性异常及其 operation_id/值，或典型 unavailable/timeout；完整请求仍以 JSONL 为准。

## B9. 停止请求和异常处置

没有运行程序时直接回复“无工作负载”。前台程序优先等本轮结束，需要中断时使用程序支持的停止方式或 Ctrl+C。后台进程使用实际 PID/会话管理，不能 `killall python`。

客户端退出不撤销已发请求；按 timeout 和驱动行为确认在途请求结束。将 run 标为 aborted/incomplete，保留已发生的写，使用新 history 重新开始。

如果 C 恢复失败或 n3 意外 OOM，立即停止新的测量请求，把额外故障记录进 manifest，不把这轮悄悄归到原定场景。

## B10. 数据恢复验收

C 清除规则、A 三节点 UN 后，你按本轮事先定义的对象/版本/CL 验证数据，不只做端口测试。将命令、读到的值、时间和副本定位方式保存为 `member-b/recovery-check.jsonl` 或文本。

若观察会触发 read repair，写明影响；没有达到恢复条件就填“截至截止时间未观察到”，不写“UN 所以全部同步”。维护性 repair 若必要由 A 在观察结束后安排。

## B11. 你上传什么

使用 COMMON 的 `evidence/b/<run_id>` 分支和 PR：

```text
results/raw/<run_id>/manifest.json
results/raw/<run_id>/member-b/
  before-utc.txt / code-commit.txt / 初始快照
  command.txt
  runner-terminal.txt
  operations.jsonl
  初始化和路由验收记录
  n3-cql-reachability.txt（适用时）
  recovery-check.*
results/raw/<run_id>/screenshots/member-b/
```

源码、检查器和依赖文件先通过独立 work/b 分支审阅合并，正式测量使用合并后的代码。不要生成实验结果后才把影响结果的未提交代码补入一个无法追溯的 commit。

## B12. 支持 C 分析和最终报告

给 C：字段说明、检查器入口、每历史 verdict 表、错误分类、分母规则、原始日志路径。C 给出图表后你抽查：至少一条 witness、一个 blocked、一个正常历史能从 raw 重算；与汇总数字一致。

你负责报告中四种定义、参数与预测、workload 设计、检查器和代表性历史解释。A 整合，C 写分析/局限/复现。引用数据库官方文档、driver 版本和 AI 使用，不把当前未执行的预测写成结果。

**你最终交付：** 可运行源码、依赖锁、检查器与验收样本、每轮原始历史、真实启动命令、manifest、模型/设计章节，以及 C 可直接使用的数据接口。
