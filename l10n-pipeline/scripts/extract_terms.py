"""용어집 없이 번역(baseline)한 결과에서 모델이 대상 용어를 어떻게 옮겼는지 뽑는다(2026-11-24, 별명 채점 준비).
방법: 오답 문장마다 Claude Haiku 5.5에게 "영어 용어 X에 해당하는 부분을 한국어 문장에서 그대로 베껴라(조사 빼고)"라고 묻는다.
돌려받은 글자가 문장에 실제로 있는지 코드로 확인하고, 없으면 bad로 표시한다. 정답 문장은 묻지 않는다.
(처음엔 protected 원응답과 difflib로 맞대는 방식을 썼으나 조사·빈칸이 섞여 바꿨다.)
사용: PYTHONIOENCODING=utf-8 python scripts/extract_terms.py
출력: results/extracted_ko.json, 캐시 results/extract_cache_ko.json(같은 문장·용어는 다시 묻지 않음)
키: measure_api.py와 같음(../voc-pipeline/.env).
"""
import json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_api  # noqa: F401  (.env 로드)
from measure import ROOT
import anthropic

LANG = "ko"
MODELS = ["google_gemma-4-12b-qat", "openai_gpt-oss-20b", "qwen3-14b", "claude-haiku-5-5", "gemini-3.5-flash-lite"]
SUFFIX = {"mhw": "_mhw", "notice": "_mhw_notice"}
SYSTEM = ("You are given an English game term and a Korean sentence that translates an English sentence containing it. "
          "Copy, character for character, the part of the Korean sentence that renders the English term. "
          "Leave out Korean particles attached after it (이/가/을/를/은/는/의/에/로/와/과 etc.) and counts like '10개'. "
          "If the term was left in English, copy the English. If no part of the sentence renders it, return an empty string.")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["term"],
          "properties": {"term": {"type": "string"}}}
client = anthropic.Anthropic()
cache_path = ROOT / "results" / f"extract_cache_{LANG}.json"
cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
usage = [0, 0]


def ask(en, sent):
    key = en + "\t" + sent
    if key not in cache:
        r = client.messages.create(
            model="claude-haiku-5-5", max_tokens=1000, system=SYSTEM,
            messages=[{"role": "user", "content": f"English term: {en}\nKorean sentence: {sent}"}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}})
        usage[0] += r.usage.input_tokens; usage[1] += r.usage.output_tokens
        raw = next((b.text for b in r.content if b.type == "text"), "{}")
        try:
            cache[key] = json.loads(raw).get("term", "")
        except Exception:
            cache[key] = None
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    return cache[key]


terms = {}
for row in __import__("csv").DictReader(open(ROOT / "glossary" / "mhw_poedb_terms.csv", encoding="utf-8-sig")):
    terms[row["api_id"]] = row["en"]

out = []
for m in MODELS:
    for tpl, suf in SUFFIX.items():
        for r in json.load(open(ROOT / "results" / f"{m}_baseline{suf}.json", encoding="utf-8")):
            lg = r["langs"][LANG]
            en = terms[r["api_id"]]
            rec = {"model": m, "tpl": tpl, "id": r["id"], "api_id": r["api_id"], "type": r["type"], "en": en,
                   "official": lg["official"], "match": lg["match"], "out": lg["out"], "span": None, "bad": False}
            if not lg["match"] and lg["out"]:
                sp = ask(en, lg["out"])
                rec["span"] = sp
                rec["bad"] = sp is None or (sp != "" and sp not in lg["out"])
            out.append(rec)
        print(m, tpl, "done", flush=True)

(ROOT / "results" / f"extracted_{LANG}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
wrong = [x for x in out if not x["match"]]
print("오답", len(wrong), "빈 추출", sum(x["span"] == "" for x in wrong), "문장에 없는 추출", sum(x["bad"] for x in wrong),
      f"이번 호출 토큰 in {usage[0]:,} / out {usage[1]:,} (${usage[0] / 1e6 * 0.10 + usage[1] / 1e6 * 0.50:.4f})")
