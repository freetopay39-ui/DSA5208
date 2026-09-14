#!/usr/bin/env python3
"""
A 专用：生成 DSA5208 Project 1 的事前预测表 (docs/predictions.csv)。
规则来自 _MANUAL.md 第 8 节，逐条写出理由和"什么结果会证伪它"。
生成后 A 必须逐行人工复核，改动直接编辑 CSV 并在 decision-log 记录。
"""
import csv, itertools, pathlib

MODELS = ["RYW", "MR", "MW", "WFR"]
CONFIGS = [("ONE", "ONE"), ("QUORUM", "QUORUM"), ("ALL", "ONE"), ("ONE", "ALL")]
SCENARIOS = [
    "normal",                 # 三节点健康
    "node_stop",              # n3 容器停止，客户端在存活节点
    "partition_majority",     # 2+1 分区，客户端在 n1/n2 侧
    "partition_minority",     # 2+1 分区，客户端在 n3 侧
    "partition_cross_side",   # 定向历史：前驱在多数侧，后继/读在隔离侧
]

# --- 可用性规则：该 CL 的操作在该场景下能否完成 ---
# 值: ok / fail  （fail = Unavailable 或 timeout）
AVAIL = {
    "normal":              {"ONE": "ok",   "QUORUM": "ok",   "ALL": "ok"},
    "node_stop":           {"ONE": "ok",   "QUORUM": "ok",   "ALL": "fail"},
    "partition_majority":  {"ONE": "ok",   "QUORUM": "ok",   "ALL": "fail"},
    "partition_minority":  {"ONE": "ok",   "QUORUM": "fail", "ALL": "fail"},
    "partition_cross_side":{"ONE": "ok",   "QUORUM": "fail", "ALL": "fail"},  # 跨侧那一步
}

VERDICTS = {
    "violation_expected":    "预期能观察到该模型的反例（witness）",
    "no_violation_expected": "预期观察不到反例；这不等于证明该模型成立",
    "possible_not_primary":  "理论上可能出现，但本场景不是主要构造路径；如实记录",
    "blocked_expected":      "预期因可用性被阻断，历史无法完成；记 blocked，不记 violation",
}

def predict(model, wcl, rcl, scen):
    wa, ra = AVAIL[scen][wcl], AVAIL[scen][rcl]

    # 1) 任一必要操作不可用 -> blocked
    if wa == "fail" or ra == "fail":
        which = []
        if wa == "fail": which.append(f"写 {wcl}")
        if ra == "fail": which.append(f"读 {rcl}")
        return ("blocked_expected",
                f"{scen} 下 {'、'.join(which)} 无法满足副本数要求，历史不能完成",
                "若该操作竟然成功返回，说明故障未真正生效——先验证故障注入，再重跑")

    # 2) 定向跨侧分区：低 CL 是主要反例构造路径
    if scen == "partition_cross_side":
        if (wcl, rcl) == ("ONE", "ONE"):
            if model == "RYW":
                return ("violation_expected",
                        "多数侧 ONE 写返回后，隔离侧 n3 未收到该更新；同一逻辑客户端在 n3 的 ONE 读预期返回旧值",
                        "若 n3 读到新值，检查分区是否真的生效（iptables 计数、n1 侧 status）")
            if model == "MR":
                return ("violation_expected",
                        "同一 reader 先在 n1 读到 v1（前置条件），切到隔离的 n3 ONE 读预期倒退到 v0",
                        "若 n3 也返回 v1，说明分区前已复制或分区未生效")
            if model in ("MW", "WFR"):
                return ("violation_expected",
                        "前驱 a 写在多数侧、后继 b 写在隔离的 n3；n3 上诊断读预期 b 存在而 a 不存在",
                        "若 a 也在 n3 上出现，说明 a 在分区前已到达 n3，或前驱 key 被复用")
        return ("blocked_expected",
                f"跨侧步骤需要 {wcl}/{rcl}，分区下该侧无法满足副本要求",
                "记为 blocked，不得写成'该配置保证了该模型'")

    # 3) 正常 / 单节点停止 / 多数侧：强配置预期无反例
    if (wcl, rcl) == ("QUORUM", "QUORUM"):
        base = "W+R=4>3，同键单写者受控测试下 quorum 交集非空"
        if model in ("RYW", "MR"):
            return ("no_violation_expected",
                    base + ("；read_repair=BLOCKING 支持单调 quorum 读" if model == "MR" else ""),
                    "出现反例须先排查：写超时未计入前置条件？多写者干扰？timestamp 乱序？")
        return ("no_violation_expected",
                "不能由 quorum 交集直接推出跨键因果的副本应用顺序；本受控观察预期看不出异常",
                "报告必须写明：看不出异常 ≠ 保证 MW/WFR")

    if (wcl, rcl) == ("ALL", "ONE"):
        return ("no_violation_expected",
                "成功的 ALL 写已到达全部副本，后续任意单副本读预期可见",
                "反例通常来自写超时（结果不确定）而非真正违反；须单列超时历史")

    if (wcl, rcl) == ("ONE", "ALL"):
        return ("no_violation_expected",
                "ALL 读接触全部副本，成功写预期可被发现",
                "反例须检查是否混入了 diagnostic 阶段的 ONE 读")

    # (ONE, ONE) 在 normal / node_stop / partition_majority
    if model in ("RYW", "MR"):
        return ("possible_not_primary",
                "W+R=2≤3 不提供保证；但健康链路复制极快，反例概率低。若观察到即为有效反例",
                "零反例只能写成'在 N 条有效历史中未观察到'，不得写成保证成立")
    return ("possible_not_primary",
            "无一般性跨对象因果保证；健康链路下预期难以构造缺前驱状态",
            "候选需同副本证据，否则标 inconclusive")

rows = []
for model, (wcl, rcl), scen in itertools.product(MODELS, CONFIGS, SCENARIOS):
    v, why, falsify = predict(model, wcl, rcl, scen)
    rows.append({
        "model": model,
        "write_cl": wcl,
        "read_cl": rcl,
        "scenario": scen,
        "write_available": AVAIL[scen][wcl],
        "read_available": AVAIL[scen][rcl],
        "predicted_verdict": v,
        "verdict_meaning": VERDICTS[v],
        "rationale": why,
        "falsifier": falsify,
        "observed_verdict": "",     # 实验后由 B/C 填
        "match": "",                # 实验后填 yes/no/na
    })

out = pathlib.Path.home() / "dsa5208" / "docs" / "predictions.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

from collections import Counter
print(f"wrote {len(rows)} rows -> {out}")
for k, n in Counter(r["predicted_verdict"] for r in rows).most_common():
    print(f"  {k}: {n}")
