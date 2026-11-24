"""세 모델 비교표. 측정(results/*.json)과 공지 번역(notices/translated_*.json, 현재 검수기로 재검수).
실행: PYTHONIOENCODING=utf-8 python scripts/compare.py
"""
import json
from checker import ROOT, load_glossary, check_notice

G = load_glossary()
MODELS = ["google_gemma-4-12b-qat", "openai_gpt-oss-20b", "qwen3-14b"]
# 상용 API(measure_api.py, 2026-11-24). 몬헌 측정만 돌렸다. 단가 $/1M(입력, 출력)은 voc-pipeline 02에 기록한 공식 가격(2026-11-19 확인).
API_MODELS = {"claude-haiku-5-5": (0.10, 0.50), "gemini-3.5-flash-lite": (0.30, 2.50)}


def rate(rows, lg):
    return f"{sum(x['langs'][lg]['match'] for x in rows)}/{len(rows)}"


def main():
    print("## 용어집 없이(baseline) 공식 표기 일치, 전체 n=40 (빈 출력은 불일치로 셈)")
    print("| 모델 | ko | ja | es | 빈 출력 | 아이템만 ko/ja/es(n=28) | 포켓몬만 ko/ja/es(n=12) |")
    print("|---|---|---|---|---|---|---|")
    for m in MODELS:
        r = json.load(open(ROOT / "results" / f"{m}_baseline.json", encoding="utf-8"))
        empty = sum(not all(v["out"] for v in x["langs"].values()) for x in r)
        it = [x for x in r if x["type"] == "item"]; mo = [x for x in r if x["type"] == "pokemon"]
        print(f"| {m} | {rate(r,'ko')} | {rate(r,'ja')} | {rate(r,'es')} | {empty} | "
              + "/".join(rate(it, lg).split("/")[0] for lg in ("ko", "ja", "es")) + f" of {len(it)} | "
              + "/".join(rate(mo, lg).split("/")[0] for lg in ("ko", "ja", "es")) + f" of {len(mo)} |")
    print("\n## 용어 보호(protected): 자리표시자 유지 = 공식명 치환 성공")
    for m in MODELS:
        r = json.load(open(ROOT / "results" / f"{m}_protected.json", encoding="utf-8"))
        print(f"{m}: ko {rate(r,'ko')}, ja {rate(r,'ja')}, es {rate(r,'es')}")
    for suf, title in (("mhw", "몬헌 용어(사용자 검수 288개, 몬헌 전용 틀 22개)"),
                       ("mhw_notice", "몬헌 용어, 공지체 틀 20개(실제 한국어 공지 구조 참고)")):
      print(f"\n## {title}: baseline 일치 | protected 유지")
      for m in MODELS + list(API_MODELS):
        try:
            b = json.load(open(ROOT / "results" / f"{m}_baseline_{suf}.json", encoding="utf-8"))
            p = json.load(open(ROOT / "results" / f"{m}_protected_{suf}.json", encoding="utf-8"))
        except FileNotFoundError:
            print(f"{m}: 아직 없음")
            continue
        empty = sum(not all(v["out"] for v in x["langs"].values()) for x in b)
        it = [x for x in b if x["type"] == "item"]; mo = [x for x in b if x["type"] == "pokemon"]
        sub = lambda rows: "/".join(rate(rows, lg).split("/")[0] for lg in ("ko", "ja", "es")) + f" of {len(rows)}"
        print(f"{m}: baseline ko {rate(b,'ko')} ja {rate(b,'ja')} es {rate(b,'es')} "
              f"(빈 출력 {empty}; 아이템 {sub(it)}, 몬스터 {sub(mo)}) | "
              f"protected ko {rate(p,'ko')} ja {rate(p,'ja')} es {rate(p,'es')}")
        if m in API_MODELS:
            pin, pout = API_MODELS[m]
            tin = sum(x["in_tok"] for x in b + p); tout = sum(x["out_tok"] for x in b + p)
            sec = sorted(x["sec"] for x in b + p)
            print(f"  └ 두 조건 {len(b) + len(p)}문장: 입력 {tin:,} / 출력 {tout:,} 토큰, "
                  f"${tin / 1e6 * pin + tout / 1e6 * pout:.4f}(실측 토큰 x 단가), 지연 중앙값 {sec[len(sec) // 2]:.2f}초")
    print("\n## 공지 5종 번역(현재 검수기 기준 이슈)")
    for m in MODELS:
        notices = json.load(open(ROOT / "notices" / f"translated_{m}.json", encoding="utf-8"))
        tot, detail = 0, []
        for n in notices:
            iss = check_notice({"en": n["en"], "terms": n["terms"], "tr": n["tr"], "prob": n.get("prob")}, G)
            tot += len(iss)
            detail += [f"{n['id'][:2]} {x['lang']}:{x['kind']}" for x in iss]
        kept = sum(all(n["placeholders_kept"].values()) for n in notices)
        print(f"{m}: 이슈 {tot}건 {detail or ''} | 자리표시자 전부 유지 {kept}/{len(notices)}")


if __name__ == "__main__":
    main()
