import csv
import sys
from collections import defaultdict
from pathlib import Path

def total_duration_by_operation(path: Path) -> dict[str, float]:
    """
    Reads the ProcMon CSV log at `path`.
    - Line 1 is the header.
    - Line 2 is ProcMon config (skip).
    - Lines beginning with ';' (env vars) are skipped.
    - Returns a dict: { Operation: total_duration_ms }.
    """
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(text) < 3:
        raise RuntimeError(f"Log too short: {path}")

    header = next(csv.reader([text[0]]))
    # find the column indices
    try:
        op_i  = header.index("Operation")
        dur_i = header.index("Duration")
    except ValueError as e:
        raise RuntimeError(f"Missing column in {path}: {e}")

    totals: dict[str, float] = defaultdict(float)

    # iterate over data lines (skip line 2, then skip any ';' lines)
    for line in text[2:]:
        if not line or line.lstrip().startswith(";"):
            continue
        row = next(csv.reader([line]))
        if len(row) <= max(op_i, dur_i):
            continue
        op = row[op_i]
        try:
            dur = float(row[dur_i])
        except ValueError:
            continue
        totals[op] += dur

    return totals

def main(file1: str, file2: str):
    p1, p2 = Path(file1), Path(file2)
    t1 = total_duration_by_operation(p1)
    t2 = total_duration_by_operation(p2)

    all_ops = sorted(set(t1) | set(t2))
    name1, name2 = p1.name, p2.name

    # header
    print(f"{'Operation':40s} {name1:>12s} {name2:>12s} {'Diff':>12s}")
    print("-" * (40 + 12*3 + 3))

    for op in all_ops:
        v1 = t1.get(op, 0.0)
        v2 = t2.get(op, 0.0)
        diff = v2 - v1
        print(f"{op:40s} {v1:12.3f} {v2:12.3f} {diff:12.3f}")


    t1_total = sum(t1.values())
    t2_total = sum(t2.values())
    print(f"\n{'Total':40s} {t1_total:12.3f} {t2_total:12.3f} {t2_total - t1_total:12.3f}")


if __name__ == "__main__":
    main('Logfile_Debug.CSV', 'Logfile_Network.CSV')