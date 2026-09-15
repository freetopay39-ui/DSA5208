BASE_TS = 1_000_000


def meta(
    run_id,
    history,
    model,
    scenario,
    write_cl,
    read_cl,
    fault_verified=False,
    routing=None,
):
    return {
        "run_id": run_id,
        "history_id": history,
        "model": model,
        "scenario": scenario,

        "write_cl": write_cl,
        "read_cl": read_cl,

        "fault_verified": bool(
            fault_verified
        ),
        "routing": routing,
    }


def write(
    client,
    m,
    op,
    key,
    value,
    cl,
    session_id,
    dep=None,
    ts=None,
):
    q = """
    INSERT INTO dsa5208.items
    (history,k,value)
    VALUES (%s,%s,%s)
    """

    params = (
        m["history_id"],
        key,
        value,
    )

    if ts is not None:
        q += " USING TIMESTAMP %s"
        params += (ts,)

    mm = {
        **m,
        "session_id": session_id,
    }

    return client.execute(
        mm,
        op,
        "workload",
        "write",
        key,
        q,
        params,
        cl,
        value,
        dep,
        ts,
    )


def read(
    client,
    m,
    op,
    key,
    cl,
    session_id,
    phase="workload",
):
    mm = {
        **m,
        "session_id": session_id,
    }

    return client.execute(
        mm,
        op,
        phase,
        "read",
        key,

        """
        SELECT value
        FROM dsa5208.items
        WHERE history=%s AND k=%s
        """,

        (
            m["history_id"],
            key,
        ),

        cl,

        diagnostic_cl=(
            "ONE"
            if phase == "diagnostic"
            else None
        ),
    )


def value(record):
    x = record.get("returned")

    if isinstance(x, dict):
        return x.get("value")

    return None


def prepare(
    clients,
    run_id,
    history,
    model,
):
    """
    RYW / MR need v0 to exist on all replicas
    before the network partition.
    """

    if model not in {"ryw", "mr"}:
        return []

    m = meta(
        run_id,
        history,
        model,
        "prepare",
        "ALL",
        "ALL",
    )

    q = """
    INSERT INTO dsa5208.items
    (history,k,value)
    VALUES (%s,%s,%s)
    USING TIMESTAMP %s
    """

    return [
        clients["source"].execute(
            {
                **m,
                "session_id": "P",
            },

            0,
            "prepare",
            "write",
            "x",

            q,

            (
                history,
                "x",
                "v0",
                BASE_TS,
            ),

            "ALL",

            "v0",

            mutation_timestamp=BASE_TS,
        )
    ]


def ryw(clients, **args):
    m = meta(**args)
    out = []

    w = write(
        clients["source"],
        m,
        1,
        "x",
        "v1",
        m["write_cl"],
        "U",
        ts=BASE_TS + 1,
    )

    out.append(w)

    if w["status"] == "ok":
        out.append(
            read(
                clients["target"],
                m,
                2,
                "x",
                m["read_cl"],
                "U",
            )
        )

    return out


def mr(clients, **args):
    m = meta(**args)
    out = []

    w = write(
        clients["source"],
        m,
        1,
        "x",
        "v1",
        m["write_cl"],
        "P",
        ts=BASE_TS + 1,
    )

    out.append(w)

    if w["status"] != "ok":
        return out

    r1 = read(
        clients["source"],
        m,
        2,
        "x",
        m["read_cl"],
        "R",
    )

    out.append(r1)

    if (
        r1["status"] == "ok"
        and value(r1) == "v1"
    ):
        out.append(
            read(
                clients["target"],
                m,
                3,
                "x",
                m["read_cl"],
                "R",
            )
        )

    return out


def mw(clients, **args):
    m = meta(**args)
    out = []

    w1 = write(
        clients["source"],
        m,
        1,
        "a",
        "first-write",
        m["write_cl"],
        "U",
    )

    out.append(w1)

    if w1["status"] != "ok":
        return out

    w2 = write(
        clients["target"],
        m,
        2,
        "b",
        "second-write;depends-on=a",
        m["write_cl"],
        "U",
        "a",
    )

    out.append(w2)

    if w2["status"] != "ok":
        return out

    out += [
        read(
            clients["target"],
            m,
            3,
            "b",
            "ONE",
            "observer",
            "diagnostic",
        ),

        read(
            clients["target"],
            m,
            4,
            "a",
            "ONE",
            "observer",
            "diagnostic",
        ),
    ]

    return out


def wfr(clients, **args):
    m = meta(**args)
    out = []

    w1 = write(
        clients["source"],
        m,
        1,
        "a",
        "original-post",
        m["write_cl"],
        "P",
    )

    out.append(w1)

    if w1["status"] != "ok":
        return out

    r = read(
        clients["source"],
        m,
        2,
        "a",
        m["read_cl"],
        "U",
    )

    out.append(r)

    if (
        r["status"] != "ok"
        or value(r) != "original-post"
    ):
        return out

    w2 = write(
        clients["target"],
        m,
        3,
        "b",
        "reply;depends-on=a",
        m["write_cl"],
        "U",
        "a",
    )

    out.append(w2)

    if w2["status"] != "ok":
        return out

    out += [
        read(
            clients["target"],
            m,
            4,
            "b",
            "ONE",
            "observer",
            "diagnostic",
        ),

        read(
            clients["target"],
            m,
            5,
            "a",
            "ONE",
            "observer",
            "diagnostic",
        ),
    ]

    return out


RUNNERS = {
    "ryw": ryw,
    "mr": mr,
    "mw": mw,
    "wfr": wfr,
}
