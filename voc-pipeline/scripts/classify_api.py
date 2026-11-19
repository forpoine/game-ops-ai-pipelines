"""상용 API로 같은 분류를 돌려 로컬 모델과 비교한다(2026-11-19). 프롬프트는 prompts.py(로컬과 같은 글자). 합성 데이터만 보낸다.
사용: python scripts/classify_api.py <claude|gemini> <model_id> <tag> [N]
  예: VOC_PROMPT=cap2 VOC_GOLD=syn_voc_gold_v3.csv python scripts/classify_api.py claude claude-haiku-5-5 haiku_cap2
      VOC_PROMPT=cap2 VOC_GOLD=syn_voc_gold_v3.csv python scripts/classify_api.py gemini <gemini 모델 id> gemini_cap2
키: ANTHROPIC_API_KEY, GEMINI_API_KEY 환경 변수 또는 voc-pipeline/.env (코드에 적지 않는다).
출력: data/pred_<tag>.csv. classify.py와 같은 열 + in_tok, out_tok(추론 토큰 포함). 비용은 scripts/cost.py가 토큰 x 단가로 계산.
형식 강제: 두 API 모두 JSON 스키마 구조화 출력을 쓴다. 실패(거절, 빈 응답, 오류)는 1회 재시도 후 needs_review=1.
설정: VOC_EFFORT(Claude effort, 기본 low), VOC_API_SLEEP(호출 사이 초, 무료 등급 분당 한도용, 기본 0).
"""
import csv, json, os, pathlib, re, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import build_system

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 키는 환경 변수 또는 voc-pipeline/.env(KEY=VALUE 줄, 공개 저장소에 넣지 않음)에서 읽는다. 이미 있는 환경 변수가 우선.
_env = ROOT / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8-sig").splitlines():
        if "=" in _l and not _l.lstrip().startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))
GOLD = ROOT / "data" / (os.environ.get("VOC_GOLD") or "syn_voc_gold.csv")
provider, model, tag = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = ROOT / "data" / f"pred_{tag}.csv"
SYSTEM = build_system(os.environ.get("VOC_PROMPT"))
VALID = {"category": ["BUG", "BAL", "MON", "OPS", "COM", "ETC"], "severity": ["S1", "S2", "S3", "S4"],
         "sentiment": ["pos", "neu", "neg"]}
SCHEMA = {"type": "object", "additionalProperties": False, "required": list(VALID),
          "properties": {k: {"type": "string", "enum": v} for k, v in VALID.items()}}
RETRY = int(os.environ.get("VOC_RETRY", "1"))
SLEEP = float(os.environ.get("VOC_API_SLEEP", "0"))

if provider == "claude":
    import anthropic
    client = anthropic.Anthropic()

    def ask(text):
        r = client.messages.create(
            model=model, max_tokens=4000, system=SYSTEM,
            messages=[{"role": "user", "content": text}],
            output_config={"effort": os.environ.get("VOC_EFFORT", "low"),
                           "format": {"type": "json_schema", "schema": SCHEMA}})
        if r.stop_reason == "refusal":
            return "", r.usage.input_tokens, r.usage.output_tokens, "refusal"
        raw = next((b.text for b in r.content if b.type == "text"), "")
        return raw, r.usage.input_tokens, r.usage.output_tokens, r.stop_reason
elif provider == "gemini":
    from google import genai
    from google.genai import types
    client = genai.Client()

    def ask(text):
        r = client.models.generate_content(
            model=model, contents=text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0,
                                               response_mime_type="application/json", response_json_schema=SCHEMA))
        u = r.usage_metadata
        out = (u.candidates_token_count or 0) + (getattr(u, "thoughts_token_count", 0) or 0)
        fin = r.candidates[0].finish_reason.name if r.candidates and r.candidates[0].finish_reason else ""
        return (r.text or ""), (u.prompt_token_count or 0), out, fin
else:
    sys.exit("provider: claude | gemini")


def parse(raw):
    m = re.search(r"\{.*?\}", raw or "", re.S)
    try:
        d = json.loads(m.group(0))
    except Exception:
        d = {}
    return d, all(d.get(k) in v for k, v in VALID.items())


rows = list(csv.DictReader(open(GOLD, encoding="utf-8-sig")))
n = int(sys.argv[4]) if len(sys.argv) > 4 else len(rows)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["id", "pred_category", "pred_severity", "pred_sentiment", "sec", "raw",
                                      "tries", "needs_review", "in_tok", "out_tok", "finish"])
    w.writeheader()
    for r in rows[:n]:
        t0 = time.time(); tries = 0; tin = tout = 0; d, ok, raw, fin = {}, False, "", ""
        while True:
            tries += 1
            try:
                raw, i, o, fin = ask(r["text"]); tin += i; tout += o
                d, ok = parse(raw)
            except Exception as e:  # 네트워크·한도 오류: SDK 재시도 후에도 실패하면 기록하고 다음 시도
                raw, fin = "", f"error:{type(e).__name__}"
                time.sleep(10)
            if ok or tries > RETRY:
                break
        sec = round(time.time() - t0, 2)
        w.writerow({"id": r["id"], "pred_category": d.get("category", ""), "pred_severity": d.get("severity", ""),
                    "pred_sentiment": d.get("sentiment", ""), "sec": sec, "raw": re.sub(r"\s+", " ", raw or "")[:200],
                    "tries": tries, "needs_review": 0 if ok else 1, "in_tok": tin, "out_tok": tout, "finish": fin})
        f.flush(); print(r["id"], d, sec, tin, tout, fin, flush=True)
        if SLEEP:
            time.sleep(SLEEP)
