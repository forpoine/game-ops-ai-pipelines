"""baseline(용어집 없이) 오답을 유형으로 나눈다. LLM 없음, 저장된 결과만 사용.
유형: empty(빈 출력) / english_kept(영어 이름 그대로 둠) / other(다른 말로 옮김: 직역·음역 등)
출력: results/baseline_분석.md (유형별 개수 + 같은 문장에 대한 세 모델 출력 예시)
실행: PYTHONIOENCODING=utf-8 python scripts/analyze_baseline.py
"""
import json
from checker import ROOT, load_glossary

G = load_glossary()
MODELS = [("Gemma 12B", "google_gemma-4-12b-qat"), ("gpt-oss 20B", "openai_gpt-oss-20b"), ("Qwen3 14B", "qwen3-14b")]
LANGS = ["ko", "ja", "es"]
data = {m: json.load(open(ROOT / "results" / f"{f}_baseline.json", encoding="utf-8")) for m, f in MODELS}


def norm(s):
    return "".join(s.split()).lower()


def kind(rec, lg):
    v = rec["langs"][lg]
    if v["match"]:
        return "match"
    if not v["out"]:
        return "empty"
    if norm(G[rec["api_id"]]["en"]) in norm(v["out"]):
        return "english_kept"
    return "other"


lines = ["# baseline 오답 유형 (용어집 없이 번역, n=40)", "",
         "- match: 공식 표기가 들어감 / english_kept: 영어 이름을 그대로 둠 / other: 다른 말로 옮김(직역·음역 등) / empty: 빈 출력", ""]
for lg in LANGS:
    lines += [f"## {lg}", "", "| 모델 | match | english_kept | other | empty |", "|---|---|---|---|---|"]
    for m, _ in MODELS:
        c = {k: 0 for k in ("match", "english_kept", "other", "empty")}
        for r in data[m]:
            c[kind(r, lg)] += 1
        lines.append(f"| {m} | {c['match']} | {c['english_kept']} | {c['other']} | {c['empty']} |")
    lines.append("")

# 같은 문장(시드 고정)에 대한 세 모델 출력 비교: 아이템 8개
lines += ["## 예시: 같은 문장, 세 모델의 한국어/일본어 출력 (아이템 8개)", ""]
base = data[MODELS[0][0]]
shown = 0
for i, r in enumerate(base):
    if r["type"] != "item" or shown >= 8:
        continue
    shown += 1
    t = G[r["api_id"]]
    lines += [f"**{r['src']}**  공식: ko `{t['ko']}` / ja `{t['ja']}` / es `{t['es']}`", ""]
    for m, _ in MODELS:
        rr = data[m][i]
        assert rr["id"] == r["id"] and rr["api_id"] == r["api_id"]
        lines.append(f"- {m}: ko {'O' if rr['langs']['ko']['match'] else 'X'} `{rr['langs']['ko']['out']}` | ja {'O' if rr['langs']['ja']['match'] else 'X'} `{rr['langs']['ja']['out']}`")
    lines.append("")
out = ROOT / "results" / "baseline_분석.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:40]))
print("saved", out)
