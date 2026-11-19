"""규칙 기반 급증 감지(AI 아님). 같은 클러스터 글이 W시간 창 안에 N건 이상이면 경보. 합성 데이터. LM Studio 불필요.
사용:
  python scripts/detect.py oracle a [N] [W]     # 정답 주제(gold_cluster)로 감지
  python scripts/detect.py pred   a [N] [W]     # data/cluster_<tag>.csv(cluster.py apply 결과)로 감지
  python scripts/detect.py shrink a [N] [W]     # 급증 25건을 k건으로 줄여가며 감지율(정답 주제 기준)
기본 N=5, W=3 (02_학습기록 6단계, 2026-11-18 사용자 선택)."""
import csv, sys, random, datetime as dt, pathlib, collections as C
ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {"a": "syn_voc_gold.csv", "b": "syn_voc_b_gold.csv"}
SURGE = "surge_notice_time_error"

def load(tag):
    rows = list(csv.DictReader(open(ROOT/"data"/FILES[tag], encoding="utf-8-sig")))
    for r in rows: r["t"] = dt.datetime.strptime(r["ts"], "%Y-%m-%d %H:%M")
    return rows

def alerts(events, N, W):
    """events: [(time, cluster_key, is_surge)] -> 클러스터별 첫 경보 [(cluster, alert_time, count, surge_in_window)]"""
    by = C.defaultdict(list)
    for t, k, s in events: by[k].append((t, s))
    out = []; win = dt.timedelta(hours=W)
    for k, v in by.items():
        v.sort()
        for i, (t, _) in enumerate(v):
            inw = [(u, s) for u, s in v[:i+1] if t - u < win]
            if len(inw) >= N:
                out.append((k, t, len(inw), sum(s for _, s in inw))); break
    return out

def summarize(rows, key, N, W, label):
    ev = [(r["t"], key(r), r["gold_cluster"] == SURGE) for r in rows]
    al = alerts(ev, N, W)
    surge_t = sorted(r["t"] for r in rows if r["gold_cluster"] == SURGE)
    print(f"[{label}] N={N}, W={W}시간: 경보 {len(al)}건")
    for k, t, n, s in sorted(al, key=lambda x: x[1]):
        kind = "급증 클러스터" if s * 2 >= n else "오탐(급증 아님)"
        lat = f", 급증 첫 글 후 {(t - surge_t[0]).total_seconds()/3600:.1f}시간" if s and surge_t else ""
        print(f"  {t:%m-%d %H:%M} 클러스터 {k} 창 안 {n}건(그중 급증 {s}건) -> {kind}{lat}")
    if surge_t and not any(s * 2 >= n for _, _, n, s in al): print("  ※ 급증을 놓침")

if __name__ == "__main__":
    mode, tag = sys.argv[1], sys.argv[2].lower()
    N = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    W = float(sys.argv[4]) if len(sys.argv) > 4 else 3
    rows = load(tag)
    if mode == "oracle":
        summarize(rows, lambda r: r["gold_cluster"], N, W, f"Set {tag.upper()} 정답 주제 기준")
    elif mode == "pred":
        import os; sfx = ("_" + os.environ["VOC_EMB"] if os.environ.get("VOC_EMB") else "") + ("_c" if os.environ.get("VOC_CENTER") == "1" else "")   # 언어 평균 보정 결과는 cluster_<tag>_c.csv
        m = {r["id"]: r["pred_cluster"] for r in csv.DictReader(open(ROOT/"data"/f"cluster_{tag}{sfx}.csv", encoding="utf-8-sig"))}
        summarize(rows, lambda r: m[r["id"]], N, W, f"Set {tag.upper()} 클러스터링 결과 기준")
    elif mode == "shrink":
        base = [r for r in rows if r["gold_cluster"] != SURGE]; surge = [r for r in rows if r["gold_cluster"] == SURGE]
        random.seed(3); print(f"급증 {len(surge)}건을 k건으로 줄였을 때 감지율(200회 무작위 부분표본), N={N}, W={W}시간")
        print("  k   감지율  평균 지연(시간, 감지된 경우)")
        for k in [25, 15, 10, 8, 6, 5, 4, 3]:
            hit = 0; lats = []
            for _ in range(200):
                sub = random.sample(surge, k)
                ev = [(r["t"], r["gold_cluster"], r["gold_cluster"] == SURGE) for r in base + sub]
                a = [x for x in alerts(ev, N, W) if x[0] == SURGE]
                if a: hit += 1; lats.append((a[0][1] - min(r["t"] for r in sub)).total_seconds() / 3600)
            print(f"  {k:>2}  {hit/200:5.2f}   {sum(lats)/len(lats):.1f}" if lats else f"  {k:>2}  {hit/200:5.2f}   -")
