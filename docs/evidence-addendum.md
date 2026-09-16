# 关卡证据引用勘误（追加，不改历史原件）

整理日期：2026-09-16。依据原始仓库提交 `e8a39030e424cf6aac5c1dfbe4b490d26076e0c3`，OpenAI Codex辅助复核。原gate.json、execute-started.json内嵌gate及coordination.md均不改写。本勘误纠正的是证据指向；不是补造当时授权或回执。

|批次|原字段|原引用|应配合引用的现有证据|理由|
|---|---|---|---|---|
|F2|c_evidence|[snapshot-20260916T112449704632117](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/snapshot-20260916T112449704632117)|[stopped-20260916T112536957973812.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/stopped-20260916T112536957973812.txt)|原引用三节点正常、容器运行，不能证明停止。新索引文件记录exited及FinishedAt。|
|F3|a_evidence|[snapshot-20260916T114029068574711](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114029068574711)|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114321890637766/status.txt)|原引用为分区前全UN。替代索引显示n1/n2 UN、n3 DN。|
|F3|c_evidence|[snapshot-20260916T114005535408465](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114005535408465)|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/status.txt)|原引用为分区前全UN。替代索引显示n3 UN、n1/n2 DN。|

## 覆盖执行窗口的补充证据

- [results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv)
- [results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112913490328031.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112913490328031.txt)
- [results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112925472898162.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112925472898162.txt)
- [results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112934195969125.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112934195969125.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/iptables.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/iptables.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/container.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/container.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114614235639225/status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114614235639225/status.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114618474494353/status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114618474494353/status.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114618474494353/iptables.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114618474494353/iptables.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/counters-20260916T114555121804930.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/counters-20260916T114555121804930.txt)
- [results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/counters-20260916T114618272514274.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/counters-20260916T114618272514274.txt)

F2实际操作发生在停止后、启动前；F3实际操作发生在分区添加后、解除前。两侧快照、DROP计数和事件日志相互支持该判断。详细时间见[时间线](formal-timeline.md)。这些证据支持本轮故障条件，不是连续抓包，也不能排除每一毫秒内的未记录状态变化。

结论：现有正确证据已在仓库中，引用缺陷无需通过重跑修复。报告引用上述证据与本勘误；保留旧关卡以呈现真实记录过程。
