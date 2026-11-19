"""Set B 정답 파일: 생성 1차 라벨에 사용자가 확정한 경계 사례 11건을 덮어쓴다(2026-11-17). 전부 합성 데이터.
CONFIRMED = id: (category, severity). 나머지 69건은 label_status=generated(미확인)."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIRMED = {
 "SYNB-0002": ("MON","S3"), "SYNB-0005": ("BUG","S2"), "SYNB-0007": ("OPS","S3"), "SYNB-0011": ("BUG","S2"),
 "SYNB-0014": ("BUG","S2"), "SYNB-0023": ("BUG","S2"), "SYNB-0040": ("MON","S4"), "SYNB-0054": ("BUG","S2"),
 "SYNB-0057": ("MON","S4"), "SYNB-0072": ("BAL","S3"), "SYNB-0079": ("MON","S2"),
}
rows = list(csv.DictReader(open(ROOT/"data"/"syn_voc_b_generated.csv", encoding="utf-8-sig")))
cols = list(rows[0].keys()) + ["orig_category","orig_severity"]
with open(ROOT/"data"/"syn_voc_b_gold.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows:
        r["orig_category"], r["orig_severity"] = r["gold_category"], r["gold_severity"]
        if r["id"] in CONFIRMED:
            r["gold_category"], r["gold_severity"] = CONFIRMED[r["id"]]; r["label_status"] = "confirmed"
        w.writerow(r)
ch = [(i,r) for i,r in ((r["id"],r) for r in rows) if i in CONFIRMED and (r["orig_category"],r["orig_severity"]) != CONFIRMED[i]]
print(len(rows), "rows; confirmed", len(CONFIRMED), "; changed vs first-pass", len(ch))
for i,r in ch: print(i, r["orig_category"], r["orig_severity"], "->", CONFIRMED[i])
