"""공지 5종 용어 보호 번역: 영어 원문의 {T:id}를 [[T1]].. 자리표시자로 바꿔 LLM에 보내고(주변 문장만 번역),
돌아온 ja/es 문장의 자리표시자를 언어별 공식명으로 치환한다. ko는 사람이 쓴 원문을 그대로 쓴다.
결과: notices/translated_<model>.json (원응답 포함). 이어서 report로 검수.
실행: PYTHONIOENCODING=utf-8 python scripts/translate_notices.py --model google/gemma-4-12b-qat
"""
import argparse, json, re, time
from pathlib import Path
from checker import ROOT, load_glossary, check_notice
from measure import chat, parse_json
from notices import load_notices, render, TAG

SYS = ("You translate game service announcements from English into Japanese and Spanish. "
       "Tokens like [[T1]], [[T2]] are protected game terms: copy each one exactly as written, "
       "do not translate, inflect or drop them. Also copy {SERVICE} exactly. "
       "Keep all numbers, dates, times and percentages unchanged. "
       "Reply with only JSON: {\"ja\":\"...\",\"es\":\"...\"}.")


def tag(text, order):
    """{T:id} -> [[Tn]] (등장 순서대로). order는 id 목록(같은 용어가 두 번 나오면 같은 번호)."""
    def sub(m):
        if m.group(1) not in order:
            order.append(m.group(1))
        return f"[[T{order.index(m.group(1)) + 1}]]"
    return TAG.sub(sub, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    g = load_glossary()
    out, t0 = [], time.time()
    for n in load_notices():
        order = []
        src = tag(n["en"], order)
        attempts = []
        for _ in range(2):
            raw, fin = chat(a.model, SYS, src, max_tokens=7000)  # 4000에서 N2가 토큰 소진으로 비었음
            tr = parse_json(raw)
            attempts.append({"finish": fin, "raw": raw})
            if tr.get("ja") and tr.get("es"):
                break
        tr_final = {"ko": render(n["ko"], g, "ko")}
        kept = {}
        for lg in ("ja", "es"):
            text = tr.get(lg, "")
            kept[lg] = all(f"[[T{i+1}]]" in text for i in range(len(order)))
            for i, tid in enumerate(order):
                official = g[tid].get(lg) or g[tid]["en"]
                text = text.replace(f"[[T{i+1}]]", official)
            tr_final[lg] = text.replace("{SERVICE}", "{SERVICE}")
        iss = check_notice({"en": render(n["en"], g, "en"), "terms": n["terms"], "tr": tr_final,
                            "prob": n.get("prob")}, g)
        out.append({"id": n["id"], "en": render(n["en"], g, "en"), "terms": n["terms"],
                    "prob": n.get("prob"), "tr": tr_final, "placeholders_kept": kept,
                    "issues": iss, "attempts": attempts})
        print(n["id"], "이슈", len(iss), [f"{x['lang']}:{x['kind']}" for x in iss], f"{time.time()-t0:.0f}s", flush=True)
    path = ROOT / "notices" / f"translated_{a.model.replace('/', '_')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", path)


if __name__ == "__main__":
    main()
