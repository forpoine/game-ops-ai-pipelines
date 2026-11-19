"""임베딩을 계층 클러스터링(코사인 거리, average linkage)하고 정답 주제(gold_cluster)와 비교한다. 합성 데이터.
LM Studio를 쓰지 않는다(numpy, scipy만). 임베딩은 scripts/embed.py가 만든 data/emb_<tag>.npy.
사용:
  python scripts/cluster.py sweep a            # Set A에서 임계값 훑기(표 출력)
  python scripts/cluster.py apply b 0.35       # 정한 임계값을 Set B에 고정 적용, data/cluster_b.csv 저장
정답 주제 개수는 클러스터링에 쓰지 않는다(채점에만 쓴다).
다국어 비교: VOC_EMB=m3 이면 emb_<tag>_m3.npy를 읽고 cluster_<tag>_m3.csv로 저장, 훑기 구간 0.01~0.60."""
import csv, sys, re, os, pathlib, collections as C
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {"a": "syn_voc_gold.csv", "b": "syn_voc_b_gold.csv"}
SURGE = "surge_notice_time_error"

def comb2(x): return x * (x - 1) / 2
def ari(gold, pred):
    n = len(gold); ct = C.Counter(zip(gold, pred))
    a = C.Counter(gold); b = C.Counter(pred)
    s = sum(comb2(v) for v in ct.values()); sa = sum(comb2(v) for v in a.values()); sb = sum(comb2(v) for v in b.values())
    exp = sa * sb / comb2(n); mx = (sa + sb) / 2
    return 1.0 if mx == exp else (s - exp) / (mx - exp)
def purity(gold, pred):
    by = C.defaultdict(list)
    for g, p in zip(gold, pred): by[p].append(g)
    return sum(C.Counter(v).most_common(1)[0][1] for v in by.values()) / len(gold)
def cluster(emb, thr):
    x = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    z = linkage(x, method="average", metric="cosine")
    return fcluster(z, t=thr, criterion="distance")
def surge_stats(gold, pred):
    ids = [i for i, g in enumerate(gold) if g == SURGE]
    if not ids: return None
    by = C.Counter(pred[i] for i in ids); best, hit = by.most_common(1)[0]
    size = sum(1 for p in pred if p == best)
    return dict(pieces=len(by), recall=hit / len(ids), precision=hit / size, size=size)
CENTER = os.environ.get("VOC_CENTER") == "1"   # 사후 보정: 글의 언어 묶음별 평균 벡터를 빼고 클러스터링(원본 결과를 본 뒤에 추가한 설계, 02 5단계)
def detect_lang(t):
    """정답 라벨(lang)을 쓰지 않는 규칙 기반 언어 판별: 한글 비율로 ko/en/mixed."""
    t = t.replace("{SERVICE}", ""); h = len(re.findall(r"[가-힣]", t)); l = len(re.findall(r"[A-Za-z]", t))
    if h + l == 0: return "ko"
    r = h / (h + l); return "ko" if r >= 0.85 else ("en" if r <= 0.15 else "mixed")
def lang_center(rows, emb):
    x = emb / np.linalg.norm(emb, axis=1, keepdims=True); g = np.array([detect_lang(r["text"]) for r in rows])
    for k in set(g):
        if (g == k).sum() >= 3: x[g == k] -= x[g == k].mean(0)
    return x
EMBSFX = "_" + os.environ["VOC_EMB"] if os.environ.get("VOC_EMB") else ""
def load(tag):
    rows = list(csv.DictReader(open(ROOT/"data"/FILES[tag], encoding="utf-8-sig")))
    emb = np.load(ROOT/"data"/f"emb_{tag}{EMBSFX}.npy")
    return rows, (lang_center(rows, emb) if CENTER else emb)
SUFFIX = EMBSFX + ("_c" if CENTER else "")
def report(rows, pred):
    gold = [r["gold_cluster"] for r in rows]; pred = list(pred)
    return dict(k=len(set(pred)), single=sum(1 for v in C.Counter(pred).values() if v == 1),
                ari=ari(gold, pred), pur=purity(gold, pred), surge=surge_stats(gold, pred), gold_k=len(set(gold)))

if __name__ == "__main__":
    mode, tag = sys.argv[1], sys.argv[2].lower()
    rows, emb = load(tag)
    if mode == "sweep":
        print(f"Set {tag.upper()} n={len(rows)} 정답 주제 {len(set(r['gold_cluster'] for r in rows))}개(채점용)")
        print("임계값  클러스터수  단독  ARI    순도   급증(조각수 재현율 정밀도)")
        for thr in (np.arange(0.30, 1.201, 0.05) if CENTER else np.arange(0.01, 0.601 if EMBSFX else 0.201, 0.01)):
            r = report(rows, cluster(emb, thr)); s = r["surge"]
            sg = f"{s['pieces']:>3}  {s['recall']:.2f}  {s['precision']:.2f}" if s else "-"
            print(f"{thr:.3f}  {r['k']:>6}   {r['single']:>4}  {r['ari']:.3f}  {r['pur']:.3f}   {sg}")
    elif mode == "apply":
        thr = float(sys.argv[3]); pred = cluster(emb, thr); r = report(rows, pred)
        print(f"Set {tag.upper()} 임계값 {thr}: 클러스터 {r['k']}개(정답 {r['gold_k']}개), 단독 {r['single']}, ARI {r['ari']:.3f}, 순도 {r['pur']:.3f}, 급증 {r['surge']}")
        with open(ROOT/"data"/f"cluster_{tag}{SUFFIX}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f); w.writerow(["id", "gold_cluster", "pred_cluster", "text"])
            for row, p in zip(rows, pred): w.writerow([row["id"], row["gold_cluster"], int(p), row["text"]])
