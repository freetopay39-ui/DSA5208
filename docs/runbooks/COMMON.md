# 三方共用：协同关卡、证据目录与 GitHub 上传

## 1. 所有命令在哪里执行

除明确标注 Cloud Shell 或本机外，均在自己负责的 **Ubuntu VM 的 `~/dsa5208`** 中执行。A 对 n1，B 对 n2，C 对 n3。不要在本机 PowerShell 粘贴 Bash 命令。

已有环境不重建；已有 smoke 结果不覆盖。每轮开始前恢复健康；实验期间不要 git pull、修改配置、部署新程序或运行 repair。

## 2. 每个人的唯一责任

| 工作 | 主责 | 配合/复核 |
|---|---|---|
| 网络、三节点与版本基线 | A | C 复核部署可复现性 |
| 参数预测、workload、检查器 | B | A 复核语义；C 抽查判定 |
| run_id 创建、登记、发布 | C | A/B 原样使用 |
| 准备测试数据和运行客户端 | B | C 等待初始化完成 |
| 正式故障注入/恢复 | C | A 验证多数侧；B 验证客户端路径 |
| 原始客户端日志 | B | C 分析 |
| 多数侧集群证据 | A | C 对齐时间线 |
| 少数侧状态和故障事件 | C | A 复核故障范围 |
| 汇总表、图表 | C | B 从原始记录重算 |
| README、PR 合并、提交包整合 | A | B/C 交叉审阅；C 从零复现 |

## 3. 一轮实验的协同关卡

| 关卡 | 谁发出完成通知 | 必须满足 | 下一步 |
|---|---|---|---|
| G0 BASELINE_READY | A | 三节点 UN、无残留分区、代码/配置一致；数据状态另检 | C 创建本轮 ID |
| G1 RUN_REGISTERED | C | run_id、场景、参数、轮次和三人职责登记 | B 准备数据 |
| G2 DATA_READY | B | 新 history 初始化完成；无在途业务请求；证据已落盘 | 正常场景直接 G4；故障场景 C 注入 |
| G3 FAULT_VERIFIED | C 汇总 A/B 回执 | 两侧拓扑、端口和规则/进程状态符合目标 | B 开始负载 |
| G4 WORKLOAD_DONE | B | 工作负载退出/结束，数据已 flush，记录错误和中断 | C 恢复故障 |
| G5 RECOVERY_VERIFIED | A/B/C | C 确认规则/进程恢复，A 确认拓扑，B 验证指定数据 | 三方封存证据 |
| G6 EVIDENCE_MERGED | A | 三方 PR 合并、路径齐全、分析输入可追溯 | 下一轮或分析 |

正常场景没有 G3，G5 仍检查结束状态；没有真正注入故障就不写 FAULT_VERIFIED。

消息示例：`[完整run_id] B DATA_READY：初始化完成、无在途请求，可注入 node_stop。` 场景名采用 `node_stop`；修复版 runner 已按场景选择路由，先按 [修复说明](../ROUTING_MR_FIX.md) 在 VM 验收。

群聊确认需要由相关人实际发出；不要在文档里预先代填“已确认”。关键回执抄入本轮协同记录，并写清操作者和 UTC 时间；截图可补充但不能代替实验日志。

如果某项不满足，记录原因并停在对应关卡。无效配置、意外中断、超时和完整运行都保留，不通过删除记录来整理“干净结果”。

## 4. 统一目录：各人只写自己的证据

```text
docs/
  runbooks/                         本套六个指引/核查文件
  versions.md                       A 汇总
  experiment-plan.md                B 主写，三人运行前确认
  run-registry-c.tsv                C 追加维护
  reproduction-c.md                 C 复现记录
  ai-usage.md                       每人追加自己的使用记录
results/
  raw/<run_id>/
    manifest.json                   B 写，A/C 复核
    member-a/                       A 的状态、配置和日志
    member-b/                       B 的客户端历史、命令和终端输出
    member-c/                       C 的故障、恢复和协同记录
    screenshots/member-a|member-b|member-c/
  processed/<run_id>/               派生结果，不手工改 raw
  figures/                         C 的图表和数据来源说明
scripts/                           健康检查、分区、恢复、版本采集
src/                               runner、工作负载、检查器
analysis/                          可重复分析入口
report/                            报告源文件与最终 PDF
```

旧的 `results/raw/C/versions-n3.txt`、`results/raw/A/versions-n1.txt` 等继续保留，由 versions.md 链接。不要为满足新目录重写历史。

manifest 最少记录：run_id、三台 code commit、模型、场景、读写 CL、诊断 CL、seed、history 数、coordinator 路由、表名、RF、read repair、重试/超时策略、timestamp 策略、镜像/版本证据路径、实际开始结束时间、结束状态。

只用 ONE 读取隔离副本的诊断不属于 QUORUM/ALL 业务读；用 `phase=diagnostic` 区分。manifest 中保留实际参数，不根据文件名猜测。

## 5. C 创建，A/B 接收 run_id

C 每个新 run 执行一次：

```bash
cd ~/dsa5208
export LAB_RUN="$(date -u +'%Y%m%dT%H%M%SZ')-$(cat /proc/sys/kernel/random/uuid)"
mkdir -p docs "results/raw/$LAB_RUN/member-c"
if [ ! -f docs/run-registry-c.tsv ]; then
  printf 'utc\trun_id\tevent\tnote\n' > docs/run-registry-c.tsv
fi
printf '%s\t%s\tREGISTERED\towner=C\n' "$(date -u +'%FT%TZ')" "$LAB_RUN" >> docs/run-registry-c.tsv
printf '%s\n' "$LAB_RUN"
```

C 把输出原样发给 A/B。三人各自设置变量，ROLE 选自己的小写字母：

```bash
cd ~/dsa5208
export LAB_RUN='替换成C发布的完整编号'
export LAB_ROLE='c'
export LAB_OUT="$PWD/results/raw/$LAB_RUN/member-$LAB_ROLE"
mkdir -p "$LAB_OUT" "results/raw/$LAB_RUN/screenshots/member-$LAB_ROLE"
```

SSH 重连后重新设置相同值，不再次生成 ID。新的参数、新的独立试验或中断后重新开始使用新 ID；一轮中的多条操作历史用不同 history_id。

每次状态检查使用不同文件名，例如 `during-01-status.txt`、`during-02-status.txt`；不要用相同 tee 文件覆盖前次输出。

## 6. 各角色通用的初始快照

确认 LAB_OUT 正确后，每轮执行一次。以下 noclobber 会拒绝覆盖已有文件；报错时检查已有证据或使用新的检查文件名，不盲目重跑。

```bash
(
  set -eC
  : "${LAB_OUT:?请先设置本轮目录}"
  date -u +'%FT%TZ' > "$LAB_OUT/before-utc.txt"
  hostname > "$LAB_OUT/hostname.txt"
  git rev-parse HEAD > "$LAB_OUT/code-commit.txt"
  git status --short > "$LAB_OUT/git-status.txt"
  sudo docker exec cassandra nodetool status > "$LAB_OUT/before-status.txt"
  sudo docker inspect --format '{{.State.Status}} {{.Image}} {{.HostConfig.NetworkMode}} {{json .HostConfig.CapAdd}}' cassandra > "$LAB_OUT/container-before.txt"
)
```

git-status 中新证据文件是正常情况，但源码/配置的未提交修改必须处理后再冻结版本。实际运行期间保存的 code commit 不因后来证据提交、PR 合并而回填修改。

## 7. 截图最低要求

| 阶段 | 截图 | 谁保存 | 对应文本证据 |
|---|---|---|---|
| 基线，仅版本变化时重拍 | 三 VM 名称/私有 IP/机型；三节点 UN | A | versions、配置、nodetool |
| 每种故障首轮及异常轮 | 停止的容器或分区规则及两侧状态 | C 保存 n3，A 保存多数侧 | inspect、iptables、status |
| 代表性一致性历史 | 输入、返回值、操作 ID | B | JSONL 和 checker 输出 |
| 恢复 | 三节点恢复及规则已清除 | A/C | after-status、iptables-after |
| 复现 | 干净环境、运行完成和图表 | C | 复现命令、日志、版本 |

不要求给每个读写请求截图。截图保留终端上下文、节点和 run_id，命名如 `03-partition-n3.png`；云账单标识、邮箱和凭据按需要遮盖，注明截图有隐私处理，不修改实验数值。原始文本是主要证据。

截图在你的电脑上产生，可在 GitHub 网页上传到**自己的证据分支**的对应 screenshots 目录；若在远端分支新增了截图，本机下次提交前先同步该分支。不要同时在网页和终端改同一文件。

## 8. 每人如何上传 GitHub：使用各自分支和 PR

以下在自己 VM 的仓库执行。所有变更都在本轮测量结束、证据导出完成后提交；避免实验途中切换代码。

### 8.1 检查并创建自己的分支

```bash
cd ~/dsa5208
git status --short
git branch --show-current
git check-ignore .env
git switch -c "evidence/$LAB_ROLE/$LAB_RUN"
```

这里假定从本轮已冻结的代码状态创建新分支。若分支已存在，不重复创建，检查后切回同一个分支。若有不明源码修改，先确认归属，不强制切换或清理。

### 8.2 精确添加证据

```bash
git add -- "results/raw/$LAB_RUN/member-$LAB_ROLE"
# 有截图才执行：
git add -- "results/raw/$LAB_RUN/screenshots/member-$LAB_ROLE"
```

B 额外添加本轮 manifest；C 额外添加自己维护的 registry；A 额外添加自己更新的版本文档。只添加实际存在且审阅过的路径，例如：

```bash
# 仅 C：
git add -- docs/run-registry-c.tsv
# 仅 B：
git add -- "results/raw/$LAB_RUN/manifest.json"
```

不要 `git add .`；不提交 `.env`、误建的 `.env;`、密钥、token、数据库 volume 或 `.venv`。体积过大的完整日志由 A 统一安排归档，并在仓库保留校验和、索引和复现主结果所需的小型数据集；不要突然将全部数据库文件打包入库。

### 8.3 审查、提交、推送

```bash
git diff --cached --stat
git --no-pager diff --cached
git commit -m "Add $LAB_ROLE evidence for $LAB_RUN"
git push -u origin "evidence/$LAB_ROLE/$LAB_RUN"
```

如果没有任何待提交修改，commit 会提示 nothing to commit，不需要重复提交。若 push 被拒绝，先看错误，不用 `--force`。尚未完成的试验也可提交，但说明 incomplete/aborted，不能标成正式成功结果。

### 8.4 在 GitHub 创建 PR

打开仓库 → Compare & pull request；base 选择 `main`，compare 选择自己的 `evidence/...` 分支。标题写角色、run_id、场景；描述包括：保存了什么、哪些检查通过、哪些未完成、是否包含异常/中断、关联另外两人的 PR。

A 统一安排合并；A 自己的 PR 由 B 或 C 审阅。此流程防止三人在 main 同时 push 冲突，不要求购买额外工具。

三人审阅重点：ID 是否一致、实验 code commit 是否一致、文件是否缺漏、是否含敏感信息、证据是否支持“已验收”、原始文件是否被覆盖。

### 8.5 合并后再同步

确认本机变更已提交且 PR 已合并，再执行：

```bash
git switch main
git pull --ff-only
git rev-parse HEAD
```

三人确认同一 main commit 后才开始下一轮。若不同步或出现分叉，先检查 `git status` 和 `git log --oneline -5`，由 A 协调，不执行 `reset --hard`。

下一批参数/程序修改用 `work/a-...`、`work/b-...`、`work/c-...` 分支提交，不把源码修改混入证据 PR。代码版本变化需重新做相关小样本验收。

## 9. 每轮怎样收尾

1. B 停止新请求，确认在途请求完成或超时，保存原始日志。
2. C 恢复故障；A 验证拓扑；B 检查本轮定义的数据恢复条件。
3. 三方将开始/故障/恢复/结束证据保存完成；C 登记 COMPLETED、ABORTED 或 INCONCLUSIVE 及原因。
4. 各自提交证据 PR；A 确认齐全后合并。
5. C 分析，B 抽查；图表和检查器结果不能代替 raw。
6. A 在全组确认不再需要 VM 后统一停止云主机。恢复规则、同步数据和备份成果在关机之前完成。
