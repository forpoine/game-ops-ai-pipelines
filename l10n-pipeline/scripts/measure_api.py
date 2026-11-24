"""상용 API로 measure.py와 같은 측정(용어집 없이 vs 용어 보호)을 돌린다(2026-11-24, voc-pipeline classify_api.py 방식).
문장(시드 7), 시스템 프롬프트, 채점은 measure.py를 그대로 가져다 쓴다. 다른 점은 아래 세 가지다.
  - 형식: JSON 스키마 구조화 출력(ko/ja/es 문자열)으로 강제한다(로컬은 프롬프트로만 요청).
  - 샘플링: Claude 5.5 계열은 temperature를 받지 않아 기본값이다. Gemini는 로컬과 같은 0.2.
  - 거절(refusal)은 다른 모델로 넘기지 않고 실패로 기록한다(측정에 다른 모델이 섞이지 않게).
사용: PYTHONIOENCODING=utf-8 python scripts/measure_api.py <claude|gemini> <model_id> --mode baseline --glossary mhw --n 100 [--tpl notice]
  예: python scripts/measure_api.py claude claude-haiku-5-5 --mode baseline --glossary mhw --n 100
키: ANTHROPIC_API_KEY, GEMINI_API_KEY 환경 변수 또는 ../voc-pipeline/.env (코드에 적지 않고, 출력하지 않는다).
설정: L10N_EFFORT(Claude effort, 기본 low), L10N_API_SLEEP(호출 사이 초, Gemini 무료 등급용, 기본 0).
출력: results/<model_id>_<mode>[_mhw][_notice].json. measure.py와 같은 형식 + 문장별 in_tok, out_tok(추론 포함), sec.
"""
import argparse, json, os, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure import ROOT, LANGS, SYS_BASE, SYS_PROT, build_sentences, parse_json, norm

_env = ROOT.parent / "voc-pipeline" / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8-sig").splitlines():
        if "=" in _l and not _l.lstrip().startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))

SCHEMA = {"type": "object", "additionalProperties": False, "required": LANGS,
          "properties": {lg: {"type": "string"} for lg in LANGS}}


def make_ask(provider, model):
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic()

        def ask(system, text):
            r = client.messages.create(
                model=model, max_tokens=4000, system=system,
                messages=[{"role": "user", "content": text}],
                output_config={"effort": os.environ.get("L10N_EFFORT", "low"),
                               "format": {"type": "json_schema", "schema": SCHEMA}})
            if r.stop_reason == "refusal":
                return "", r.usage.input_tokens, r.usage.output_tokens, "refusal"
            raw = next((b.text for b in r.content if b.type == "text"), "")
            return raw, r.usage.input_tokens, r.usage.output_tokens, r.stop_reason
        return ask
    if provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client()

        def ask(system, text):
            r = client.models.generate_content(
                model=model, contents=text,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.2,
                                                   response_mime_type="application/json",
                                                   response_json_schema=SCHEMA))
            u = r.usage_metadata
            out = (u.candidates_token_count or 0) + (getattr(u, "thoughts_token_count", 0) or 0)
            fin = r.candidates[0].finish_reason.name if r.candidates and r.candidates[0].finish_reason else ""
            return (r.text or ""), (u.prompt_token_count or 0), out, fin
        return ask
    sys.exit("provider: claude | gemini")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("provider", choices=["claude", "gemini"])
    ap.add_argument("model")
    ap.add_argument("--mode", choices=["baseline", "protected"], required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--glossary", choices=["pokeapi", "mhw"], default="pokeapi")
    ap.add_argument("--tpl", choices=["basic", "notice"], default="basic")
    a = ap.parse_args()

    ask = make_ask(a.provider, a.model)
    sleep = float(os.environ.get("L10N_API_SLEEP", "0"))
    sents = build_sentences(a.n, glossary=a.glossary, tpl_set=a.tpl)
    suffix = ("_mhw" if a.glossary == "mhw" else "") + ("_notice" if a.tpl == "notice" else "")
    out_path = ROOT / "results" / f"{a.model.replace('/', '_')}_{a.mode}{suffix}.json"
    system = SYS_PROT if a.mode == "protected" else SYS_BASE
    # L10N_RESUME=1: 기존 결과에서 모든 시도가 API 오류(error:, 예: 503 과부하)인 문장만 다시 묻는다.
    # 모델이 낸 답(틀린 번역, 형식 실패)은 측정 대상이므로 다시 묻지 않는다.
    keep = {}
    if os.environ.get("L10N_RESUME") == "1" and out_path.exists():
        old = json.loads(out_path.read_text(encoding="utf-8"))
        keep = {r["id"]: r for r in old if not all(x["finish"].startswith("error:") for x in r["attempts"])}
    results = []
    t_all = time.time()
    for s in sents:
        if s["id"] in keep:
            results.append(keep[s["id"]]); continue
        src = s["tagged"] if a.mode == "protected" else s["text"]
        attempts, tr, tin, tout = [], {}, 0, 0
        t0 = time.time()
        for _ in range(2):  # 빈 결과·오류면 1회 재시도, 시도 기록은 모두 남김
            try:
                raw, i, o, fin = ask(system, src)
                tin += i; tout += o
            except Exception as e:  # SDK 자체 재시도 후에도 실패한 경우(키는 메시지에 들어가지 않음)
                raw, fin = "", f"error:{type(e).__name__}:{re.sub(r'\s+', ' ', str(e))[:150]}"
                time.sleep(10)
            tr = parse_json(raw)
            attempts.append({"finish": fin, "raw": raw})
            if all(tr.get(lg) for lg in LANGS):
                break
        rec = {"id": s["id"], "api_id": s["term"]["api_id"], "type": s["term"]["type"], "src": s["text"],
               "attempts": attempts, "in_tok": tin, "out_tok": tout, "sec": round(time.time() - t0, 2),
               "langs": {}}
        for lg in LANGS:
            text = tr.get(lg, "")
            official = s["term"][lg]
            if a.mode == "protected":
                kept = "[[T1]]" in text
                final, ok = text.replace("[[T1]]", official), kept
            else:
                final, kept = text, None
                ok = norm(official) in norm(text)
            rec["langs"][lg] = {"out": final, "official": official, "placeholder_kept": kept, "match": ok}
        results.append(rec)
        print(s["id"], s["term"]["en"], {lg: rec["langs"][lg]["match"] for lg in LANGS},
              f"{rec['sec']}s", tin, tout, attempts[-1]["finish"], flush=True)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        if sleep:
            time.sleep(sleep)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")  # 이어하기로 건너뛴 뒤쪽 줄까지 저장

    print("== summary", a.model, a.mode, suffix or "pokeapi", "n=", len(results),
          f"{time.time() - t_all:.0f}s, in {sum(r['in_tok'] for r in results):,} / out {sum(r['out_tok'] for r in results):,} tok")
    for lg in LANGS:
        for kind in (None, "item", "pokemon"):
            rows = [r for r in results if kind in (None, r["type"])]
            print(f"{lg} {kind or 'all':8s} {sum(r['langs'][lg]['match'] for r in rows)}/{len(rows)}")


if __name__ == "__main__":
    main()
