# 软件版本、部署配置与证据边界

2026-09-16根据已有证据汇总，来源固定提交 `e8a39030e424cf6aac5c1dfbe4b490d26076e0c3`。这是事后资料整理，未重新部署或采集VM状态。下表将实际采集结果与仓库声明区分；不能把声明版本当成已安装版本的独立验证。

## 三台节点实际采集结果

|字段|n1（A）|n2（B）|n3（C）|
|---|---|---|---|
|node|dsa5208-n1|dsa5208-n2|dsa5208-n3|
|internal_ip|10.20.0.11|10.20.0.12|10.20.0.13|
|captured_utc|2026-09-14T08:32:18Z|2026-09-14T07:59:55Z|2026-09-14T07:56:58Z|
|cpu_model|Intel(R) Xeon(R) CPU @ 2.20GHz|Intel(R) Xeon(R) CPU @ 2.20GHz|Intel(R) Xeon(R) CPU @ 2.20GHz|
|ubuntu|24.04 (noble)|24.04 (noble)|24.04 (noble)|
|kernel|7.0.0-1011-gcp|7.0.0-1011-gcp|7.0.0-1011-gcp|
|docker_engine|29.8.0|29.8.0|29.8.0|
|compose|5.5.1|5.5.1|5.5.1|
|containerd|v2.3.5|v2.3.5|v2.3.5|
|nodetool|ReleaseVersion: 5.0.9|ReleaseVersion: 5.0.9|ReleaseVersion: 5.0.9|
|jvm|openjdk version "17.0.20" 2026-07-21|openjdk version "17.0.20" 2026-07-21|openjdk version "17.0.20" 2026-07-21|
|built_image_id|sha256:31c620464d54be9714647a2c919dbe656d3f3cc4a2eb6a656e6350d6e1046132|sha256:ae3f567dfd635bccc3ca97b0bd3cd2d3c2b698eaaf4ffa6cdbfe227719c29396|sha256:e4ac9d87ef5f589b18139afafffb6cf8014d18cf60dadf7d7593160780d0e007|
|基础镜像RepoDigest|未记录/不可用|未记录|未记录|

原始采集文件：[versions-n1.txt](../results/raw/A/versions-n1.txt)、[versions-n2.txt](../results/raw/B/versions-n2.txt)、[versions-n3.txt](../results/raw/C/versions-n3.txt)。

节点Cassandra实际版本记录为5.0.9（nodetool亦一致）。三个自建镜像ID不同；正式实验快照显示各节点自身镜像ID跨轮不变，不能据此声称三镜像逐字节相同，也不能仅因ID不同断定数据库版本不同。

## 仓库配置声明与运行证据

|项目|值|证据属性|
|---|---|---|
|基础镜像标签|cassandra:5.0.9|Dockerfile声明；未按digest固定|
|自建镜像标签|dsa5208-cassandra:5.0.9|compose声明；实际ID见上表|
|系统附加包|iptables|Dockerfile安装，但未锁定包版本|
|数据中心/机架|dc1；rack1/rack2/rack3|拓扑快照与配置|
|容器网络|dsa5208-lab_default，NET_ADMIN|运行快照；7000、9042映射|
|RF|NetworkTopologyStrategy，dc1=3|三轮schema-before.txt一致|
|read_repair|BLOCKING|DESCRIBE实际输出|
|speculative_retry|NEVER|DESCRIBE实际输出；报告保留这个值|
|TTL|0|DESCRIBE实际输出|
|MAX_HEAP_SIZE|1G|配置值，未另采集运行时堆大小|
|HEAP_NEWSIZE|256M|配置值；原版本日志明确提示G1下忽略，不能写为生效值|
|业务请求超时|10秒|client.py实现声明|
|重试策略|FallthroughRetryPolicy|client.py实现声明|
|驱动/客户端Python|驱动锁文件见下；Python解释器版本未单独记录|不把锁文件当作pip freeze|

配置与实现：[Dockerfile](../Dockerfile), [compose.yaml](../compose.yaml), [client.py](../src/client.py), [requirements-lock.txt](../requirements-lock.txt)。

锁文件声明：

```text
cassandra-driver==3.30.1
click==8.5.0
Deprecated==1.3.1
geomet==1.1.0
wrapt==2.4.1
```

三轮schema证据：

- F1: [schema-before.txt](../results/raw/20260916T110624Z-cf03cc10-8c8c-4f06-9e0f-8bdd87b20538/member-a/schema-before.txt)；执行commit `8fac774568b3c9d9a20a74ecb0306ae7fa39cac3`。
- F2: [schema-before.txt](../results/raw/20260916T112400Z-35c1262b-8238-462b-a667-42746045efc1/member-a/schema-before.txt)；执行commit `88219c5807f64b2db1c9040f2442f1e5d073540b`。
- F3: [schema-before.txt](../results/raw/20260916T113921Z-d6670471-9ddb-4b18-97cc-7054b455edee/member-a/schema-before.txt)；执行commit `70cc2d632316b0a8c8297ac8acf862944163ba4d`。

三轮schema文件相同；计划记录的全部src/*.py指纹跨轮一致，commit变化不等于runner变化。可用batch-plan.json核对每轮源文件SHA256。

## 基础镜像digest的已知限制

三份原始版本文件的base_image_digest为空或unavailable。仓库内现有材料不能恢复实验时实际基础镜像RepoDigest，因此本汇总明确记为“未记录/无法由现有证据确认”，不补写推测值。本项资料披露已完成，但缺失的历史digest本身没有被恢复。

如果以后在原VM补采，只能作为带新时间的附加证据；不得重新pull/rebuild后冒充实验时镜像。原镜像已经不存在时保留此局限即可，无需为此重跑120条实验。

可选的只读补采（每台自己的VM执行，保留输出，不执行pull）：

```bash
cd ~/dsa5208
stamp=$(date -u +'%Y%m%dT%H%M%SZ')
out="results/raw/version-supplement-$(hostname -s)-$stamp"
mkdir -p "$out"
date -u +'%FT%TZ' > "$out/captured-utc.txt"
sudo docker inspect --format '{{.Image}}' cassandra > "$out/container-image-id.txt"
sudo docker image inspect cassandra:5.0.9 --format '{{.Id}} {{json .RepoDigests}}' > "$out/base-image.txt" 2>&1
sudo docker image inspect dsa5208-cassandra:5.0.9 --format '{{.Id}} {{json .RepoDigests}}' > "$out/built-image.txt" 2>&1
```

即使补采成功，也需核对本地标签是否仍指向实验所用镜像，不能仅凭当下同名标签证明历史一致。此补采尚未执行。

本文、[引用勘误](evidence-addendum.md)及[时间线](formal-timeline.md)由OpenAI Codex按现有证据生成，小组报告应在AI使用说明中披露。没有新增组员签名或伪造历史回执。
