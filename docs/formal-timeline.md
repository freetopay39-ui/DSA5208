# 正式实验时间线：事后依据原始日志整理

整理日期：2026-09-16。依据仓库提交 `e8a39030e424cf6aac5c1dfbe4b490d26076e0c3`；由OpenAI Codex辅助整理。此文件是新增证据索引，不是当时的群聊回执，不代表组员已签名。原coordination.md、gate.json及原始日志保留原样。

所有时间为UTC。各机器时钟偏差未独立测量，快照时间取utc.txt的命令开始时间；命令内部的多次采集不完全同时。操作结束估计由started_utc加duration_ms计算，不能作为独立记录的精确结束时间。事件先后请同时参考各自来源。

完整机器可读索引：[formal-timeline.csv](formal-timeline.csv)。关卡引用纠正：[evidence-addendum.md](evidence-addendum.md)。

|批次|场景|run_id|首条操作开始|最后操作结束估计|
|---|---|---|---|---|
|F1|normal|`20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538`|2026-09-16T11:12:27.070017+00:00|2026-09-16T11:12:43.528518+00:00|
|F2|node_stop|`20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1`|2026-09-16T11:29:11.966349+00:00|2026-09-16T11:29:30.246135+00:00|
|F3|partition_cross_side|`20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee`|2026-09-16T11:45:53.684066+00:00|2026-09-16T11:46:11.726711+00:00|

## F1 证据时间索引

|UTC|事件|依据|说明|
|---|---|---|---|
|2026-09-16T11:07:19Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-c/snapshot-20260916T110719759393725/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:07:20Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-a/snapshot-20260916T110720900069716/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:07:21Z|member-b_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/snapshot-20260916T110721797780836/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:08:56.793775+00:00|prepare_started|[prepare-started.json](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/prepare-started.json)||
|2026-09-16T11:09:04.529756+00:00|data_ready|[data-ready.json](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/data-ready.json)||
|2026-09-16T11:09:23Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-c/snapshot-20260916T110923221776359/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:09:25Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-a/snapshot-20260916T110925690171760/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:11:43.825524+00:00|gate_recorded|[gate.json](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/gate.json)|人工声明；故障引用勘误见evidence-addendum.md|
|2026-09-16T11:12:26.767942+00:00|batch_execution_started|[execute-started.json](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/execute-started.json)||
|2026-09-16T11:12:27.070017+00:00|first_operation_started|[20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538-ryw-quorum-01.jsonl](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538-ryw-quorum-01.jsonl)||
|2026-09-16T11:12:40Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-c/snapshot-20260916T111240762901687/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:12:42Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-a/snapshot-20260916T111242258150708/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:12:43.528518+00:00|last_operation_ended_estimate|[20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538-ryw-quorum-02.jsonl](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538-ryw-quorum-02.jsonl)|started_utc + rounded duration_ms；不是独立墙钟结束记录|
|2026-09-16T11:12:43.632463+00:00|batch_execution_done|[workload-done.json](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/workload-done.json)||
|2026-09-16T11:13:19Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-c/snapshot-20260916T111319141788386/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:13:59Z|member-b_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/snapshot-20260916T111359823206427/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:14:01Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-c/snapshot-20260916T111401784477092/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:14:08Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-a/snapshot-20260916T111408261754752/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:14:34Z|representative_recovery_read_started|[recovery-read-utc.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-b/recovery-read-utc.txt)|返回值见同目录recovery-read.txt；不是全部数据恢复完成时间|

## F2 证据时间索引

|UTC|事件|依据|说明|
|---|---|---|---|
|2026-09-16T11:24:49Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/snapshot-20260916T112449704632117/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:24:52Z|member-b_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/snapshot-20260916T112452066427809/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:25:21.578718+00:00|prepare_started|[prepare-started.json](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/prepare-started.json)||
|2026-09-16T11:25:28.255295+00:00|data_ready|[data-ready.json](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/data-ready.json)||
|2026-09-16T11:25:36Z|node_stop_requested|[fault-events.tsv](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv)||
|2026-09-16T11:25:42.486454246Z|container_finished_at|[during-stopped-20260916T112913490328031.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112913490328031.txt)|exited|
|2026-09-16T11:25:42.486454246Z|container_finished_at|[during-stopped-20260916T112925472898162.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112925472898162.txt)|exited|
|2026-09-16T11:25:42.486454246Z|container_finished_at|[during-stopped-20260916T112934195969125.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/during-stopped-20260916T112934195969125.txt)|exited|
|2026-09-16T11:25:42.486454246Z|container_finished_at|[stopped-20260916T112536957973812.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/stopped-20260916T112536957973812.txt)|exited|
|2026-09-16T11:25:43Z|node_stop_command_finished|[fault-events.tsv](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv)||
|2026-09-16T11:26:07Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/snapshot-20260916T112607734039946/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:28:31.270192+00:00|gate_recorded|[gate.json](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/gate.json)|人工声明；故障引用勘误见evidence-addendum.md|
|2026-09-16T11:29:11.648525+00:00|batch_execution_started|[execute-started.json](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/execute-started.json)||
|2026-09-16T11:29:11.966349+00:00|first_operation_started|[20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1-ryw-quorum-01.jsonl](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1-ryw-quorum-01.jsonl)||
|2026-09-16T11:29:13Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/snapshot-20260916T112913719077035/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:29:25Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/snapshot-20260916T112924998866148/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:29:30.246135+00:00|last_operation_ended_estimate|[20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1-ryw-quorum-02.jsonl](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1-ryw-quorum-02.jsonl)|started_utc + rounded duration_ms；不是独立墙钟结束记录|
|2026-09-16T11:29:30.354468+00:00|batch_execution_done|[workload-done.json](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/workload-done.json)||
|2026-09-16T11:29:33Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/snapshot-20260916T112933948364762/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:29:45Z|node_start_requested|[fault-events.tsv](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv)||
|2026-09-16T11:30:12Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/snapshot-20260916T113011999134754/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:30:13Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/snapshot-20260916T113013819656258/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:30:54Z|representative_recovery_read_started|[recovery-read-utc.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-b/recovery-read-utc.txt)|返回值见同目录recovery-read.txt；不是全部数据恢复完成时间|
|2026-09-16T11:30:59Z|recovery_verified_by_A_B_C|[fault-events.tsv](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-c/fault-events.tsv)||

## F3 证据时间索引

|UTC|事件|依据|说明|
|---|---|---|---|
|2026-09-16T11:40:05Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114005535408465/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:40:15Z|member-b_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/snapshot-20260916T114015962975985/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:40:29Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114029068574711/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:41:42.961077+00:00|prepare_started|[prepare-started.json](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/prepare-started.json)||
|2026-09-16T11:41:50.273005+00:00|data_ready|[data-ready.json](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/data-ready.json)||
|2026-09-16T11:41:58Z|partition_requested|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||
|2026-09-16T11:41:58Z|partition_rules_added|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||
|2026-09-16T11:42:05Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114205292263996/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:42:40Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114240629399626/status.txt)|DN 10.20.0.12; UN 10.20.0.13; DN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:43:21Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114321890637766/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:44:30Z|partition_verified_by_A_B_C|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||
|2026-09-16T11:45:09.188827+00:00|gate_recorded|[gate.json](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/gate.json)|人工声明；故障引用勘误见evidence-addendum.md|
|2026-09-16T11:45:53.379249+00:00|batch_execution_started|[execute-started.json](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/execute-started.json)||
|2026-09-16T11:45:53.684066+00:00|first_operation_started|[20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee-ryw-quorum-01.jsonl](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee-ryw-quorum-01.jsonl)||
|2026-09-16T11:45:55Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114555302341285/status.txt)|DN 10.20.0.12; UN 10.20.0.13; DN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:45:56Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114556295132840/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:46:05Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114605032028349/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:46:11.726711+00:00|last_operation_ended_estimate|[20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee-ryw-quorum-02.jsonl](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee-ryw-quorum-02.jsonl)|started_utc + rounded duration_ms；不是独立墙钟结束记录|
|2026-09-16T11:46:11.807075+00:00|batch_execution_done|[workload-done.json](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/workload-done.json)||
|2026-09-16T11:46:14Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114614235639225/status.txt)|UN 10.20.0.12; DN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:46:18Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114618474494353/status.txt)|DN 10.20.0.12; UN 10.20.0.13; DN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:46:43Z|heal_requested|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||
|2026-09-16T11:46:44Z|partition_rules_removed|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||
|2026-09-16T11:47:00Z|member-c_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/snapshot-20260916T114700077399415/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:47:11Z|member-a_snapshot_started|[status.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/snapshot-20260916T114711830169369/status.txt)|UN 10.20.0.12; UN 10.20.0.13; UN 10.20.0.11；utc.txt为快照命令开始，状态在其后采集|
|2026-09-16T11:47:45Z|representative_recovery_read_started|[recovery-read-utc.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-b/recovery-read-utc.txt)|返回值见同目录recovery-read.txt；不是全部数据恢复完成时间|
|2026-09-16T11:47:50Z|recovery_verified_by_A_B_C|[fault-events.tsv](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-c/fault-events.tsv)||

## 对原协同记录的补充说明

- 原文“完成/YES/正常”没有精确回执时间，保留为原始人工描述；此处引用日志补足可追溯时间，不能倒推出群聊通知的发送时间。
- F3原coordination.md的`202600916`存在日期笔误。B真正批量执行开始时间以execute-started.json为准，首条请求另按JSONL记录，两者不要混用。
- F1没有故障，不要求补造故障事件。F2/F3恢复读取均只有一个代表性MR对象，不能写成全部副本完全同步。
