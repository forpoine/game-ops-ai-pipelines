"""Set B 본문에서 이모지만 제거한 사본 data/syn_voc_b_noemoji_gold.csv 생성(라벨·다른 열은 그대로). 합성 데이터."""
import csv, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
emo = re.compile("[\U0001F300-\U0001FAFF☀-➿️‍]")
rows = list(csv.DictReader(open(ROOT/"data"/"syn_voc_b_gold.csv", encoding="utf-8-sig")))
n = 0
for r in rows:
    t = re.sub(r"\s+", " ", emo.sub("", r["text"])).strip()
    n += t != r["text"]; r["text"] = t
with open(ROOT/"data"/"syn_voc_b_noemoji_gold.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("changed", n, "of", len(rows))
