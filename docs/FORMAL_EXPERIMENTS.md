# 精简正式实验：24 个条件，120 条历史

2026-09-15 制定，2026-09-16 交付。按小组决定直接执行正式实验，不另设小样本验收。此前探索结果保留并单列，不挑选成功/反例加入本次固定分母。首条到末条均保留，包括失败、超时、中断。以下方案替代旧手册中的全矩阵和继续小样本安排。

## 1. 固定矩阵与研究问题

三个 block，每个 block 独立 run_id，四模型 × 两档配置 × 5 条新 history = 40 条。共24个条件、120条业务历史。history 间没有键重用；同一block共享故障窗口，不是5次独立故障重复。不要据此估计总体故障概率或做强统计显著性结论。

| block | scenario | source→target | 条件编号 | 历史数 |
|---|---|---|---|---|
| F1 正常 | normal | n1→n3 | F1-RYW-L/H、F1-MR-L/H、F1-MW-L/H、F1-WFR-L/H | 40 |
| F2 停止 n3 | node_stop | n1→n2 | F2-RYW-L/H、F2-MR-L/H、F2-MW-L/H、F2-WFR-L/H | 40 |
| F3 跨侧分区 | partition_cross_side | n1→n3 | F3-RYW-L/H、F3-MR-L/H、F3-MW-L/H、F3-WFR-L/H | 40 |

L：业务写ONE、业务读ONE。H：业务写QUORUM、业务读QUORUM。MW没有业务读，H仍传read_cl=ONE给runner，但汇总为N/A；MW/WFR诊断读取始终ONE，不参与强业务读的结论。ALL仅用于健康阶段初始化与恢复检查，不作为第四档正式配置。多数/少数侧单独实验留作已有探索材料，不继续扩展主矩阵。

| 模型 | 一条历史具体做什么 | 判断与局限 |
|---|---|---|
| RYW | 同一U经source写x=v1，再经target读x | 成功写后成功读到v0/空值是本受控无删除无TTL历史的反例；未知值无效 |
| MR | P经source写v1；同一R经source读，再经target读 | 首读成功v1、次读成功v0/空值是反例；前提未建立是inconclusive；第二读失败是blocked |
| MW | 同一U先在source写a，再在target写依赖a的b；经target诊断b和a | 检查会话写顺序的传播依赖；b有而a无仅在已验证隔离n3时构成有力依赖异常候选；不是同键最终值排序测试 |
| WFR | P在source写a；U在source读a，然后在target写依赖a的b；诊断b和a | 检查读→后继写的依赖；确认U真的读到a，且隔离n3见b不见a；不以flag单独证明因果违规 |

## 2. 运行前预测（保留原预测，不按结果回填）

前提：RF=3，三节点均为副本，原schema不变，无并发外部写、无TTL/删除、无实验中repair；当前BLOCKING read repair、speculative_retry=NONE。ONE成功不等于只写一个副本，coordinator也不等于实际服务读取的唯一副本。

| 场景/档位 | RYW | MR | MW | WFR |
|---|---|---|---|---|
| F1/L | 写读通常成功，弱读可能旧值 | 通常完成，可能倒退/前提未建立 | 双写通常成功；ONE诊断不能证明普遍顺序保证 | 读后写通常可完成；诊断可能不充分 |
| F1/H | 在受控单键历史预期成功读v1 | 预期成功v1→v1 | 双QUORUM写预期成功，但ONE跨键诊断不构成普遍保证 | 业务操作预期成功，ONE诊断同样有限 |
| F2/L | 存活侧通常成功，弱读仍有旧值可能 | 存活侧通常完成，不能先验排除倒退 | 存活侧双写通常完成 | 存活侧读后写通常完成 |
| F2/H | 两存活副本可满足QUORUM，预期v1 | 预期v1→v1 | 两次写预期成功 | 前驱写、读、后继写预期成功 |
| F3/L | n1成功写后n3可读旧v0，预期可见反例 | 若n1首读v1，n3次读v0，预期可见反例 | n1写a，隔离n3写b成功，可见b无a候选 | U读到a后在隔离n3写b，可见b无a候选 |
| F3/H | n1写可成功，n3读预计不可用→blocked | n1写及首读可成功，n3次读不可用→blocked | n1写a可成功，n3写b不可用→blocked | n1写/读a可成功，n3写b不可用→blocked |

超时写是结果未知；Unavailable/连接初始化错误分别记录。错误类型以实测为准。若F3首读ONE没读到前提，不重跑该history。没有观察到反例不等于证明模型对任意操作成立。MW/WFR无反例尤其不能被写成“QUORUM提供跨键因果一致性”。

依据与AI使用：Cassandra [Dynamo/一致性级别](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html)、[read repair](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/read_repair.html)，查阅2026-09-15。预测是对本项目具体操作序列的推断；文档的monotonic quorum reads不等于全部四种会话保证。本方案、批量代码与辅助测试由OpenAI Codex生成，小组负责执行与证据复核；在报告AI使用说明中列入。

## 3. 一次性准备

本地18项离线测试通过，包含原runner回归、矩阵数量、混合/重复日志拒绝、路由检查、候选标签和模拟完整block流程。未在三台云VM上代跑实验；实际数据只能由三人执行产生。Windows本机没有可用Git Bash，基础设施脚本执行前在VM用`bash -n scripts/formal_infra.sh`作语法检查（不是额外烟测）。

将本次新增的src/formal_batch.py、scripts/formal_infra.sh、tests/test_formal_batch.py和本文同步到三台VM。同一commit，记录软件版本、RF、schema、超时/重试设置及镜像信息。B沿用已安装依赖的.venv。脚本依靠`python -m`从仓库根目录运行，不需要pip新增依赖。运行中的block不得pull、改代码、repair、改配置。

先结束上一轮并封存证据。若在证据分支，提交完成后再切main并git pull --ff-only；有源码修改先核对，不强制覆盖。下面F1/F2/F3每轮重复同一流程，只改scenario，每轮C生成新编号。

## 4. A确认健康，C登记，三人建目录

A确认三节点UN、schema一致、三人commit相同；C确认n3无残留分区。C生成编号（每block一次）：

```bash
cd ~/dsa5208
export LAB_RUN="$(date -u +'%Y%m%dT%H%M%SZ')-$(cat /proc/sys/kernel/random/uuid)"
export LAB_SCENARIO=normal
# F2改为node_stop；F3改为partition_cross_side
export LAB_ROLE=c
export LAB_OUT="$PWD/results/raw/$LAB_RUN/member-c"
mkdir -p "$LAB_OUT" docs
if [ ! -f docs/run-registry-c.tsv ]; then
  printf 'utc\trun_id\tevent\tnote\n' > docs/run-registry-c.tsv
fi
printf '%s\t%s\tREGISTERED\tformal;%s;40 histories\n' "$(date -u +'%FT%TZ')" "$LAB_RUN" "$LAB_SCENARIO" >> docs/run-registry-c.tsv
printf 'RUN=%s SCENARIO=%s\n' "$LAB_RUN" "$LAB_SCENARIO"
```

A/B原样设置编号和场景，各自角色分别a/b：

```bash
cd ~/dsa5208
export LAB_RUN='替换为C发布编号'
export LAB_SCENARIO=normal
export LAB_ROLE=a
# B必须改成b，场景也必须与C相同
export LAB_OUT="$PWD/results/raw/$LAB_RUN/member-$LAB_ROLE"
mkdir -p "$LAB_OUT"
```

三人保存初始快照并检查原始内容：

```bash
bash scripts/formal_infra.sh snapshot
```

A补充本轮schema与展开配置（当前无认证；若后来含密码先脱敏）：

```bash
sudo docker exec cassandra cqlsh -e 'DESCRIBE KEYSPACE dsa5208' > "$LAB_OUT/schema-before.txt"
sudo docker compose config > "$LAB_OUT/compose-resolved.yaml"
```

## 5. B一次规划并准备40条；C暂不注入

```bash
source .venv/bin/activate
python -m src.formal_batch plan --run-id "$LAB_RUN" --scenario "$LAB_SCENARIO" --seed 5208
python -m src.formal_batch prepare --run-id "$LAB_RUN"
```

程序生成只写一次的batch-plan.json：40条历史、顺序、seed、代码commit、源码SHA256。全部RYW/MR（20条）在健康阶段以ALL初始化；MW/WFR使用全新键，不作业务prepare。只在程序明确打印DATA_READY且data-ready.json存在时，B发DATA_READY。prepare失败：不得注入；保留本block，诊断后新编号重做，不续跑。

## 6. 故障窗口：A/C操作，B等待

F1正常：不注入，三人确认健康后进入下一节。

F2停机：仅C在n3执行：

```bash
bash scripts/formal_infra.sh stop
```

C检查exited；A执行snapshot确认n1/n2 UN、n3 DN。C停机期间不要执行需要进入容器的snapshot。B下方检查n1/n2端口。

F3分区：仅C在n3容器运行、Compose bridge和NET_ADMIN具备、没有专用链残留时执行：

```bash
bash scripts/formal_infra.sh partition
bash scripts/formal_infra.sh counters
bash scripts/formal_infra.sh snapshot
```

A执行snapshot；预期A视角n1/n2 UN、n3 DN，C视角相反，n3仍running且DROP计数增长。20–30秒后可重新检查，文件带新时间；2–3分钟仍不符合先诊断，不允许B执行。不要重复注入。

B检查本轮目标客户端端口（端口成功不是业务成功）：

```bash
python - <<'PY' 2>&1 | tee "$LAB_OUT/ports.txt"
import os, socket
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
hosts = ['10.20.0.11', '10.20.0.12' if os.environ['LAB_SCENARIO']=='node_stop' else '10.20.0.13']
for host in hosts:
    with socket.create_connection((host,9042),timeout=5):
        print(host, '9042 reachable')
PY
```

## 7. B记录真实关卡并批量执行

A/C将实际证据路径和回执发给B；C也保存在自己的coordination.md。B在确认全部满足后生成关卡记录。下面路径必须替换成实际路径，不能保留示例或预先声称通过：

```bash
export A_EVIDENCE='替换为A实际快照或停止验证证据路径'
export C_EVIDENCE='替换为C实际快照或停止验证证据路径'
python - <<'PY'
import json, os
from pathlib import Path
from datetime import datetime, timezone
p=Path(os.environ['LAB_OUT'])/'gate.json'
with p.open('x') as f:
    json.dump(dict(run_id=os.environ['LAB_RUN'],scenario=os.environ['LAB_SCENARIO'],
        verified=True,verified_utc=datetime.now(timezone.utc).isoformat(),
        a_evidence=os.environ['A_EVIDENCE'],c_evidence=os.environ['C_EVIDENCE'],
        b_evidence=str(Path(os.environ['LAB_OUT'])/'ports.txt')),f,indent=2)
PY
python -m src.formal_batch execute --run-id "$LAB_RUN" --gate "$LAB_OUT/gate.json"
```

关卡文件是人工声明，程序不能远程验证A/C证据真实性。门禁记录不自动证明故障；A/C必须持续观察。程序按预先随机顺序运行40条，每条独立JSONL和命令输出，业务unavailable/timeout会保留并继续。意外进程错误/180秒进程超时则中止block，通知C恢复，不自行续跑；新block新ID。SSH断线后先确认原进程状态，不能再次execute。首次启动标记会拒绝重复执行。

运行中A每隔约30秒snapshot；F3时C也snapshot并记counters，F2时C只观察容器exited。快照可手动执行，保持三个block相同观测策略，停止负载后再结束观测。意外恢复/容器退出立即通知B终止，记录额外故障；不继续当作原场景。

运行结束显示WORKLOAD_DONE，B通知C。此标记只代表程序40条已执行完，不代表40条业务成功。随后可执行汇总（也支持中断block）：

```bash
python -m src.formal_batch summarize --run-id "$LAB_RUN"
```

## 8. C恢复，A检查拓扑，B检查代表性数据

F1不做故障恢复。F2仅C：

```bash
bash scripts/formal_infra.sh start
```

F3仅C：

```bash
bash scripts/formal_infra.sh counters
bash scripts/formal_infra.sh heal
```

heal报错先查专用链引用，不使用裸iptables -F。约20–30秒后A/C snapshot，必要时稍后再查，确认三节点UN、schema一致、专用链已删除。自动恢复测量期间不repair。

B从计划选第一条MR作为代表性恢复读取，日志单独保存：

```bash
export LAB_HISTORY="$(python -c 'import json,os; from pathlib import Path; p=json.loads((Path(os.environ["LAB_OUT"])/"batch-plan.json").read_text()); print(next(x["history"] for x in p["items"] if x["model"]=="mr"))')"
date -u +'%FT%TZ' > "$LAB_OUT/recovery-read-utc.txt"
sudo docker exec cassandra cqlsh -e "CONSISTENCY ALL; SELECT history,k,value FROM dsa5208.items WHERE history='$LAB_HISTORY' AND k='x';" | tee "$LAB_OUT/recovery-read.txt"
```

解释值时查该history实际写状态；成功写v1预期读v1；写超时结果未知。读取报错保留，重查用新文件名。这里只检查一个指定对象，不能宣称40条所有数据及所有副本完全同步。确认后C将RECOVERY_VERIFIED真实回执/UTC记入coordination.md与fault-events.tsv。下一block必须恢复健康后另建编号。

## 9. 结果、截图、上传与报告

自动产物：B目录的计划、初始化/开始/完成标记、gate、40份JSONL、每条命令和退出状态；results/processed/<run_id>/histories.csv与counts.json。首次写入后不覆盖；需重分析时先保存旧派生结果，不改raw。

统计：每条件计划数=5；分别列witness、no_witness_observed、blocked、inconclusive、invalid、setup_error、candidate_dependency_witness。业务请求状态计数另列，排除prepare/diagnostic，不把未执行的后续操作记作成功。中断block注明complete_block=false，不删除也不悄悄以新block替换。候选比例不能称已确认违反率。

MW/WFR：C逐条对照A/C分区覆盖时间、n3实际隔离、诊断实际coordinator=n3、同一run/history、会话顺序、依赖内容、成功读b但读a无行。写独立review.csv，含history、review_status、reviewer、evidence_paths、reason，保留原候选标签。该实验只测固定跨键依赖的可见性/传播，未直接观察副本内部应用顺序，结论须按课程MW/WFR定义说明操作化与局限。没有反例不能证明普遍保证。

截图按场景保留一次：A/C两侧拓扑、C停止或分区计数、恢复；B四模型代表性历史和异常各选必要样例。文本日志为主，不为每条history截图。不要上传.env、令牌、.venv、__pycache__。

三个block各自完成后按角色分支提交；提交只发生在测量之外：

```bash
git switch -c "evidence/$LAB_ROLE/$LAB_RUN"
git add -- "results/raw/$LAB_RUN/member-$LAB_ROLE"
# 仅B：
# git add -- "results/processed/$LAB_RUN"
# 仅C：
# git add -- docs/run-registry-c.tsv
git diff --cached --stat
git diff --cached
git commit -m "Record formal experiment block $LAB_RUN"
git push -u origin "evidence/$LAB_ROLE/$LAB_RUN"
```

各自开PR，A合入。A完成版本/部署/安装资料，B审阅预测和原始状态，C汇总图表与候选复核。最终报告同时呈现请求可用性与一致性判定，说明单故障窗口、每条件5条、固定路由/时间戳、无并发写、未穷举ALL/其他CL及恢复检查范围。旧探索数据另附，不混入本次120条固定计划。
