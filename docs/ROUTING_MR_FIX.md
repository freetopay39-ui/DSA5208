# 场景路由与 MR 边界修复

修复日期：2026-09-14；交付更新：2026-09-15。用户已授权将修复上传仓库。未修改数据库 schema、配置或原始实验数据。

## 修复后的真实路由

| --scenario | source（前驱写/首次读） | target（后续读/后继写/诊断） |
|---|---|---|
| normal | n1 | n3 |
| node_stop | n1 | n2 |
| partition_majority | n1 | n2 |
| partition_minority | n3 | n3 |
| partition_cross_side | n1 | n3 |

四种 workload 都按 source/target 选择 NodeClient。node_stop 不再尝试连接停止的 n3；minority 对同一个 n3 只建立一份客户端。所有运行操作新增 routing 元数据；requested_coordinator 仍记录 IP，actual_coordinator 保持 driver 的实际观测值或 null。

prepare 仍在故障前执行。RYW/MR 通过 n1 做 ALL 初始化，不连接不需要的 n3；MW/WFR 没有 prepare 写入，不为这个空步骤连接数据库。

错误的 scenario 名称由 argparse 拒绝。连接初始化失败保存 phase=setup 的 run 级 connection_error 并失败退出，已建立的连接会关闭。这不是一条业务读写失败，分析时单列 setup。数据库请求内部仍按原逻辑记录 status；进程退出 0 不代表所有请求成功。

## MR 的判断

在本项目无删除、无 TTL、只有 v0/v1 的受控 workload 中：

- 首次成功读到 v1，第二次成功返回 v0 或 returned=null（无行）：witness。
- 第二次 timeout/unavailable/连接错误：blocked，不能当空值反例。
- 第二次成功读到 v1：no_witness_observed。
- 返回字段缺失、返回异常值或格式不匹配：inconclusive。

这不是通用多版本数据库历史检查器。若扩展到 v2/v3 等版本，需同时扩展 workload 和检查器规则。

## 本地验证

在项目根目录执行：

```bash
python -m unittest discover -s tests -v
```

11 项测试通过，包含四种 workload × 五个场景的路由子用例，验证 node_stop 的客户端工厂即使将 n3 视为不可连接也可运行，检查单客户端复用/关闭、连接失败日志、prepare ALL、MR 空值/失败/异常值，以及 check CLI。

这些测试使用模拟客户端，不连接 Cassandra，不能替代三台云 VM 的集成验收。第一次测试遇到 Windows 沙箱临时目录权限问题，改为继承工作区权限的测试目录后全部通过；没有放宽产品代码判定来通过测试。

## B 下一步的云端小样本验收

本次修复合入 main 后，三台 VM 先在工作区干净时执行 git pull --ff-only，确认同一 commit，再按以下步骤验收。

1. 三人确认同一版本；三节点健康、无分区；C 创建新 run_id。
2. B 在 VM2 激活既有虚拟环境，设置变量并准备新的 MR history：

```bash
cd ~/dsa5208
. .venv/bin/activate
export LAB_RUN='替换为C发布的完整ID'
export LAB_HISTORY="${LAB_RUN}-mr-h001"
export LAB_LOG="$PWD/results/raw/$LAB_RUN/member-b/${LAB_HISTORY}.jsonl"
# 文件存在时先检查，不重复执行同一历史
test ! -e "$LAB_LOG"
python -m src.run prepare --model mr --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG"
```

3. B 检查 prepare 的 status=ok（ALL 写 v0），向 C 发 DATA_READY。
4. C 停止 n3，A 验证多数侧状态，B 确认 n1/n2 可连接。
5. B 执行：

```bash
python -m src.run run --model mr --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG" --scenario node_stop --write-cl QUORUM --read-cl QUORUM
python -m src.run check --model mr --history "$LAB_HISTORY" --run-id "$LAB_RUN" --log "$LAB_LOG"
```

6. 检查本轮 workload 的 routing 是 n1/n2、requested_coordinator 不含 n3，实际 status/返回值/错误完整。预期成功读写，但以实际结果为准。
7. C 恢复 n3，A 验证拓扑，B 验证数据。再用新 run/history 补 ONE/ONE、ALL/ONE、ONE/ALL 的小样本；ALL 请求不可用是预期数据，不是改回 n3 路由的理由。
8. 对 partition_majority/minority/cross_side，先健康初始化，再按场景注入真实分区；只有验收过的跨侧实验使用 --partition-verified。

## 本次没有解决的其他实验问题

历史日志仍为 append；每条 history 的 run 只能执行一次，复跑必须使用新 ID。check 仍没有按 run_id 过滤/拒绝重复 operation_id。MW/WFR 的证据仍需三方外部核验，flag 不是自动检测。预测生成器逐操作可用性、RYW 异常输入、分析脚本等仍按 REPO_CHECK 后续处理。完成本次两项修复不意味着整个项目所有正式实验均已通过验收。

## 旧演练证据

按用户决定，旧演练截图暂不补传，也不作为正式运行的阻塞项。报告默认以真实正式实验的完整证据为依据；只有引用旧演练时再查找已存截图或用新 run 重做。重跑证据用新时间与新 ID，不能冒充旧记录。现有原始文件保留不删。
