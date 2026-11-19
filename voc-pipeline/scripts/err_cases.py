"""4단계 남은 심각도 오류(S3→S2, S4→S3 등)를 사례로 뽑는다. 합성 데이터. LM Studio 불필요(기존 pred 파일만 읽음).
사용: PYTHONIOENCODING=utf-8 python scripts/err_cases.py [a|b]
- 정답: v2(글 한 건은 S2까지), 예측: S1 금지 프롬프트(cap) 결과.
- 오류를 (1) 두 모델이 같은 오답을 낸 것(기준이 모호하거나 정답이 의심스러운 후보), (2) 한 모델만 틀린 것(모델 한계 후보)으로 나눈다.
- 주제(gold_cluster)별로 정답 심각도가 몇 가지인지도 본다(정답이 주제 안에서 갈리면 기준 모호 후보)."""
import csv, sys, pathlib, collections as C
ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = {"a": ("syn_voc_gold_v2.csv", "pred_gemma_cap.csv", "pred_gptoss_cap.csv"),
       "b": ("syn_voc_b_gold_v2.csv", "pred_gemma_b_cap.csv", "pred_gptoss_b_cap.csv")}
rd = lambda f: list(csv.DictReader(open(ROOT/"data"/f, encoding="utf-8-sig")))
tag = (sys.argv[1] if len(sys.argv) > 1 else "a").lower()
g_f, a_f, b_f = CFG[tag]
gold = {r["id"]: r for r in rd(g_f)}
pg = {r["id"]: r["pred_severity"] for r in rd(a_f)}; pp = {r["id"]: r["pred_severity"] for r in rd(b_f)}
ids = list(gold)
both, only_g, only_p = [], [], []
for i in ids:
    gs = gold[i]["gold_severity"]; a, b = pg.get(i, ""), pp.get(i, "")
    ea, eb = a != gs, b != gs
    if ea and eb and a == b: both.append((i, gs, a, b))
    elif ea and eb: both.append((i, gs, a, b))   # 둘 다 틀렸지만 서로 다른 오답
    elif ea: only_g.append((i, gs, a, b))
    elif eb: only_p.append((i, gs, a, b))
n = len(ids)
print(f"Set {tag.upper()} n={n}: 둘 다 틀림 {len(both)}, Gemma만 틀림 {len(only_g)}, gpt-oss만 틀림 {len(only_p)}, 둘 다 맞음 {n-len(both)-len(only_g)-len(only_p)}")
print("\n[오류 방향: 정답→예측]")
for name, d in [("Gemma", pg), ("gpt-oss", pp)]:
    c = C.Counter((gold[i]["gold_severity"], d[i]) for i in ids if d.get(i, "") != gold[i]["gold_severity"])
    print(f"  {name}:", ", ".join(f"{a}→{b or '빈값'} {k}" for (a, b), k in c.most_common()))
print("\n[주제별 정답 심각도 분포 / 모델 예측 분포(Gemma, gpt-oss)]")
by = C.defaultdict(list)
for i in ids: by[gold[i]["gold_cluster"]].append(i)
for k, v in sorted(by.items(), key=lambda x: -len(x[1])):
    gd = C.Counter(gold[i]["gold_severity"] for i in v); gm = C.Counter(pg.get(i, "") for i in v); gp = C.Counter(pp.get(i, "") for i in v)
    f = lambda c: " ".join(f"{s}:{n}" for s, n in sorted(c.items()))
    print(f"  {k:28} {len(v):>3}건  정답[{f(gd)}]  Gemma[{f(gm)}]  gpt-oss[{f(gp)}]")
def show(title, lst):
    print(f"\n[{title}] {len(lst)}건 (id 정답 / Gemma / gpt-oss | 주제 | 상태 | 글)")
    for i, gs, a, b in lst:
        g = gold[i]; t = g["text"].replace("\n", " ")
        print(f"  {i} {gs}/{a}/{b} | {g['gold_cluster']} | {g['label_status']}{'·ambiguous' if g['ambiguous']=='true' else ''} | {t[:110]}")
show("두 모델 모두 틀림", both); show("Gemma만 틀림", only_g); show("gpt-oss만 틀림", only_p)
