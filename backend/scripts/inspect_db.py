from __future__ import annotations

import sqlite3
from pathlib import Path
import argparse

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(Path("data") / "skillpulse.db"))
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    cur.execute("SELECT role_bucket, COUNT(*) FROM postings GROUP BY role_bucket")
    print("Counts by role_bucket:")
    for row in cur.fetchall():
        print("  ", row)

    cur.execute("SELECT level_bucket, COUNT(*) FROM postings GROUP BY level_bucket")
    print("\nCounts by level_bucket:")
    for row in cur.fetchall():
        print("  ", row)

    cur.execute("SELECT source, COUNT(*) FROM postings GROUP BY source")
    print("\nCounts by source:")
    for row in cur.fetchall():
        print("  ", row)

    cur.execute("SELECT title, company, url FROM postings LIMIT ?", (args.limit,))
    print("\nSample rows:")
    for t, c, u in cur.fetchall():
        print(f"- {t} @ {c}\n  {u}\n")

    conn.close()

if __name__ == "__main__":
    main()
