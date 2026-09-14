import json


def load(path, history, model):
    with open(
        path,
        encoding="utf-8",
    ) as f:
        rows = [
            json.loads(x)
            for x in f
            if x.strip()
        ]

    return sorted(
        [
            r
            for r in rows
            if r.get("history_id") == history
            and r.get("model") == model
        ],
        key=lambda r: r.get(
            "operation_id",
            -1,
        ),
    )


def val(record):
    x = record.get("returned")

    if isinstance(x, dict):
        return x.get("value")

    return None


def op(rows, n):
    return next(
        (
            r
            for r in rows
            if r.get("operation_id") == n
        ),
        None,
    )


def ryw(rows):
    w = op(rows, 1)
    r = op(rows, 2)

    if (
        not w
        or w["status"] != "ok"
    ):
        return (
            "blocked",
            "successful write(v1) not established",
        )

    if (
        not r
        or r["status"] != "ok"
    ):
        return (
            "blocked",
            "follow-up read did not succeed",
        )

    if (
        val(r) == "v0"
        or r.get("returned") is None
    ):
        return (
            "witness",
            "successful write(v1) followed by old/missing value",
        )

    return (
        "no_witness_observed",
        f"follow-up read returned {val(r)!r}",
    )


def mr(rows):
    first = op(rows, 2)
    second = op(rows, 3)

    if (
        not first
        or first.get("status") != "ok"
        or val(first) != "v1"
    ):
        return (
            "inconclusive",
            "first read did not establish v1",
        )

    if (
        not second
        or second.get("status") != "ok"
    ):
        return (
            "blocked",
            "second read did not succeed",
        )

    if val(second) == "v0":
        return (
            "witness",
            "same reader observed v1 then v0",
        )

    return (
        "no_witness_observed",
        f"second read returned {val(second)!r}",
    )


def dependency_check(
    rows,
    model,
):
    if model == "mw":
        for n in (1, 2):
            r = op(rows, n)

            if (
                not r
                or r.get("status") != "ok"
            ):
                return (
                    "blocked",
                    "both ordered writes did not succeed",
                )

        b = op(rows, 3)
        a = op(rows, 4)

    else:
        seen = op(rows, 2)
        write_b = op(rows, 3)

        if (
            not seen
            or seen.get("status") != "ok"
            or val(seen) != "original-post"
        ):
            return (
                "inconclusive",
                "U did not establish read(a)=original-post",
            )

        if (
            not write_b
            or write_b.get("status") != "ok"
        ):
            return (
                "blocked",
                "dependent write(b) did not succeed",
            )

        b = op(rows, 4)
        a = op(rows, 5)

    if (
        not b
        or not a
        or b.get("status") != "ok"
        or a.get("status") != "ok"
    ):
        return (
            "inconclusive",
            "diagnostic reads are incomplete",
        )

    bad_state = (
        val(b) is not None
        and a.get("returned") is None
    )

    verified_partition = (
        b.get("scenario")
        == "partition_cross_side"

        and b.get("fault_verified")

        and a.get("fault_verified")
    )

    if (
        bad_state
        and verified_partition
    ):
        return (
            "witness",
            "verified isolated n3 has dependent b but not predecessor a",
        )

    if bad_state:
        return (
            "inconclusive",
            "b without a observed, but verified partition evidence is missing",
        )

    return (
        "no_witness_observed",
        "diagnostic state did not show b without a",
    )


def mw(rows):
    return dependency_check(
        rows,
        "mw",
    )


def wfr(rows):
    return dependency_check(
        rows,
        "wfr",
    )


CHECKERS = {
    "ryw": ryw,
    "mr": mr,
    "mw": mw,
    "wfr": wfr,
}
