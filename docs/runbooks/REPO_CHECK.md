# 下载仓库核查与正式实验前待办

核查对象：`D:\DSA5208\PROJECT1\DSA5208-main`（用户提供的 GitHub 下载快照）。无 .git，commit 未知；需三台 VM 记录实际 HEAD。检查日期：2026-09-14。

**修复更新：** 下表记录首次检查时的情况。2026-09-14 已在本地修复场景路由、连接初始化错误记录/资源清理、MR 空行和未知值判定，11 项离线测试通过。2026-09-15 用户已授权上传；云端仍需同步与验收，详见 [修复记录](../ROUTING_MR_FIX.md)。其余项不因本次修复而自动关闭。

## 已具备

- compose.yaml、Dockerfile、.env.example、config/schema.cql。
- schema 为 dsa5208.items(history,k,value)，RF=3，BLOCKING read repair，speculative_retry=NONE。
- src/run.py 提供 prepare/run/check；workloads.py 提供四种定向历史；client.py 单节点 allowlist、FallthroughRetryPolicy、逐操作 JSONL；checkers.py 提供四模型判定。
- scripts/collect_versions.sh、a_gate_cluster.sh、a_observe.sh、gen_predictions.py。
- A/B/C 三节点版本证据；A 的集群/schema checkpoints；C 的停止与分区演练证据。

## 当前快照不能据此确认的事项

- 未发现独立 smoke 读写日志/JSONL。用户已确认 smoke 通过，这里仅说明仓库证据待补齐，不否定实际完成。
- C 的旧演练目录里有 partition_verified 和 DN/DN/UN 证据，但未见 heal/iptables-after/after-status 等恢复记录。不能据此断言当前仍分区；下一轮前做当前状态快照，旧记录补充说明证据缺口，不伪造过去的恢复时间。
- 未见 README、analysis 程序、正式多历史数据、检查器测试集、run-registry 或 manifest。

用户已说明旧截图另有保存，暂不补传；仅报告引用旧演练时再查找/重跑。正式实验以新 run 的真实完整证据为主。修复后已新增 tests/test_routing_and_mr.py，首次检查所述“未见测试集”不再适用于更新后的本地目录。

## 必须处理的代码/实验边界

| 项目 | 源码依据 | 影响与处理人 |
|---|---|---|
| scenario 不改变路由 | src/run.py make_clients 固定建 n1/n3；workloads 固定使用它们 | B：实现显式路由，使 node_stop 只联系存活侧，区分 majority/minority/cross_side；否则不能执行全矩阵 |
| 停 n3 后 runner 可能直接启动失败 | NodeClient.__init__ 立即 connect；不在 execute 异常记录范围内 | B：所需连接按场景创建，启动失败也保存 run 级错误；不能当成 quorum 业务请求返回 |
| 重复历史和日志混合 | Logger 始终 append；load 不按 run_id 过滤；op 取首条重复 ID | B：拒绝重复执行，按 run/history/model/phase 验证唯一性；读取时校验 schema、依赖和顺序 |
| MR 成功读到无行未识别 | checkers.mr 只对 v0 判 witness | B：在无删除/TTL、先成功见 v1 的受控条件下，后续 missing 应按模型处理，不能判 no_witness |
| 未知 value 被当作未见异常 | ryw/mr 对非预期值直接落入 no_witness | B：未知/污染输入标 inconclusive 或 invalid，不能默认为有效正常历史 |
| MW/WFR 证据只靠 flag | dependency_check 检查 scenario 与 fault_verified，没校验真实 coordinator/session/依赖链全部字段 | B/C：把三方外部证据绑定本轮，检查实际路由、session、key/value 和顺序；未知证据不得自动升级 witness |
| MW 没有业务读 | workloads.mw 只有两次写和 ONE 诊断读 | A/B：预测与统计注明 read_cl 不适用，不能声称测试了 MW 的 ALL 业务读 |
| 预测表过于概括 | gen_predictions.py 对整个跨侧历史使用统一 AVAIL，未逐操作区分侧与 CL | A/B：按真实操作序列修正。例 RYW 多数侧 QUORUM 写→少数侧 ONE 读可完成；MW ONE 写+read_cl=ALL 实际无 ALL 业务读，不该仅因此预测 blocked |
| 程序返回值不等于业务成功 | execute 捕获数据库错误写 status，main 正常结束 | B：读取日志中的 status；prepare 失败不能宣布 DATA_READY |
| 观测脚本有额外依赖/局限 | a_observe 依赖 jq、多次 nodetool，字段缺失部分落 0 | A/C：安装 jq、固定采样策略、检查采集错误，不把未知当真实零 |
| gate 不是强制门禁 | a_gate_cluster 打印 FAIL 但无明确失败退出码 | A：人工检查摘要；自动化前改为正确退出码 |

这些问题不是数据库一致性实验结果。修复版可按五场景路由进行云端小样本验收；其余历史完整性、诊断证据与预测问题仍须逐条审阅，不能直接把输出用于完整正式结论。

## 已执行的本地检查

1. src 下 Python 文件通过 AST 语法解析；未安装/连接云数据库运行 runner。
2. 调用纯 Python 检查器构造 `MR: 成功读 v1 → 成功读取无行`，当前返回 `no_witness_observed`，确认上述边界问题。
3. 构造 `RYW: 成功写 → 读取 unexpected 值`，当前返回 `no_witness_observed`，确认未知输入未单独处理。

以上三个步骤是首次核查记录。后续按用户要求修改了业务源码中的场景路由与 MR 判定并新增回归测试，未修改数据库配置或原始实验数据。同步到 VM 后由 A/C 审阅并冻结新的实验 commit。
