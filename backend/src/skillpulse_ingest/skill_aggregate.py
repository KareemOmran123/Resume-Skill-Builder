from __future__ import annotations

from typing import Any

from .models import IngestionQuery
from .storage_sqlite import SQLiteStore


def aggregate_skills(db: str, q: IngestionQuery, top_n: int) -> list[dict[str, Any]]:
    store = SQLiteStore(db)
    try:
        postings_count = store.get_postings_count(q)
        if postings_count == 0:
            return []

        where_sql, params = store._posting_where_clause(q)
        cur = store.conn.cursor()
        rows = cur.execute(
            f"""
            SELECT ps.skill AS name, COUNT(DISTINCT ps.posting_id) AS count
            FROM posting_skills ps
            JOIN postings p ON p.id = ps.posting_id
            WHERE {where_sql} AND ps.count > 0
            GROUP BY ps.skill
            """,
            params,
        ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            count = int(row["count"])
            # Denominator is total filtered postings, not only postings with extracted skills.
            pct = round(100 * count / postings_count)
            items.append({"name": row["name"], "count": count, "pct": pct})

        # Stable deterministic order for frontend display and test reproducibility.
        items.sort(key=lambda x: (-x["pct"], -x["count"], x["name"]))
        return items[:top_n]
    finally:
        store.close()
