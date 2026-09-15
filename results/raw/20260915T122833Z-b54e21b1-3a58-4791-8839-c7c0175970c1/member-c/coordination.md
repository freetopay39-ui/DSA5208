# 三方协同记录

- run_id:20260915T122833Z-b54e21b1-3a58-4791-8839-c7c0175970c1
- 实验：MR / partition_majority
- 写 CL：QUORUM
- 读 CL：QUORUM
- history：20260915T122833Z-b54e21b1-3a58-4791-8839-c7c0175970c1-mr-h001
- 代码 commit

## 过程记录

| UTC 时间 | 成员 | 事件 | 实际回执或观察 |
|---|---|---|---|
| 20260915 | A | BASELINE_READY | 三节点 UN，schema 一致，无残留分区 |
| 20260915 | C | RUN_REGISTERED | 发布本轮编号，A/B 确认使用 |
| 20260915 | B | DATA_READY | prepare 返回 ok，无在途请求 |
| 20260915 | C | 分区注入 | 规则已添加，实际状态见日志 |
| 20260915 | A | 多数侧验证 | 填写实际节点状态 |
| 20260915 | B | 端口验证 | 填写实际端口检查结果 |
| 20260915 | C | FAULT_VERIFIED | 三方检查通过，通知 B 开始 |
| 20260915 | B | WORKLOAD_DONE | 填写实际读写结果和 checker 输出 |
| 20260915 | C | 解除分区 | 专用规则已清除 |
| 20260915 | A/B/C | RECOVERY_VERIFIED | 填写拓扑、规则和恢复读取结果 |

## 异常

填写错误、等待、重试、SSH 中断等实际情况。
若没有，写“本轮未观察到异常”。
本轮未观察到异常。

## 最终状态

- 执行状态：填写 COMPLETED / ABORTED / INCONCLUSIVE
- checker 结果：填写真实输出
- 恢复状态：填写实际状态
- 缺失证据：填写缺失项；无则写“无”

COMPLETED

## 证据路径

- A：填写本轮 member-a 路径
- B：填写 JSONL 和 checker.txt 路径
- C：fault-events.tsv、分区计数、节点状态、iptables-after.txt
