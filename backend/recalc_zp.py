import sys
sys.path.insert(0, "/app")
from sqlmodel import Session, text
from core.database import engine

with Session(engine) as s:
    rows = s.execute(text("""
        SELECT u.username,
            COALESCE(SUM(CASE WHEN sr.status = 'accrued' THEN sr.amount ELSE 0 END),0) as accrued,
            COALESCE(SUM(CASE WHEN sr.status = 'deducted' THEN sr.amount ELSE 0 END),0) as deducted,
            COALESCE(SUM(CASE WHEN sr.status = 'paid' THEN sr.amount ELSE 0 END),0) as paid
        FROM salary_records sr JOIN users u ON sr.user_id = u.id
        WHERE sr.period_start >= '2026-06-01' AND sr.period_start < '2026-07-01'
        GROUP BY u.username ORDER BY u.username
    """)).fetchall()
    for r in rows:
        d = dict(r._mapping)
        net = d["accrued"] + d["deducted"]
        remaining = net + d["paid"]
        print(f"{d[\"username\"]:10} +{d[\"accrued\"]:>10.0f} {d[\"deducted\"]:>10.0f} = {net:>10.0f} | paid {d[\"paid\"]:>10.0f} | to_pay {remaining:>10.0f}")
