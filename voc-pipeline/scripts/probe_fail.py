"""Gemma 형식 실패(응답이 비어 있고 55~60초 걸림)의 원인을 확인한다. 합성 데이터. LM Studio에 Gemma가 로드돼 있어야 한다.
실패한 행(pred_category 비어 있음)을 같은 프롬프트(cap2)·같은 설정(max_tokens 4000, temperature 0)으로 다시 호출해 finish_reason과 토큰 수를 기록하고,
max_tokens를 12000으로 올린 호출도 한 번 더 해서 답이 나오는지 본다. (가설: 추론이 max_tokens 4000을 다 써서 답이 끊김)
사용: python scripts/probe_fail.py <모델> <pred_tag> [pred_tag...]    결과 data/probe_fail.csv (글은 v3 정답 파일 두 개에서 id로 찾는다)"""
import csv, sys, os, re, json, time, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
model, tags = sys.argv[1], sys.argv[2:]
# classify.py의 SYSTEM(cap2)을 그대로 가져온다(import하면 실행되므로 앞부분만 exec).
os.environ["VOC_PROMPT"] = "cap2"; sys.argv = ["classify.py", model, "probe"]
ns = {"__file__": str(ROOT/"scripts"/"classify.py")}
exec(open(ROOT/"scripts"/"classify.py", encoding="utf-8").read().split("def ask")[0], ns)
SYSTEM = ns["SYSTEM"]
gold = {r["id"]: r for f in ("syn_voc_gold_v3.csv", "syn_voc_b_gold_v3.csv") for r in csv.DictReader(open(ROOT/"data"/f, encoding="utf-8-sig"))}
def call(text, max_tokens):
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
                       "max_tokens": max_tokens, "temperature": 0}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type": "application/json"})
    t0 = time.time(); d = json.load(urllib.request.urlopen(req, timeout=900)); sec = round(time.time() - t0, 1)
    ch = d["choices"][0]; m = ch["message"]; u = d.get("usage", {})
    content = m.get("content") or ""; reasoning = m.get("reasoning_content") or m.get("reasoning") or ""
    return dict(sec=sec, finish=ch.get("finish_reason"), completion_tokens=u.get("completion_tokens"), prompt_tokens=u.get("prompt_tokens"),
                content_len=len(content), reasoning_len=len(reasoning), has_json=bool(re.search(r"\{.*?\}", content, re.S)), content=re.sub(r"\s+", " ", content)[:120])
out = []
for tag in tags:
    for r in csv.DictReader(open(ROOT/"data"/f"pred_{tag}.csv", encoding="utf-8-sig")):
        if r["pred_category"]: continue
        for mt in (4000, 12000):
            try: res = call(gold[r["id"]]["text"], mt)
            except Exception as e: res = dict(sec=None, finish=f"error:{e}", completion_tokens=None, prompt_tokens=None, content_len=None, reasoning_len=None, has_json=None, content="")
            row = dict(tag=tag, id=r["id"], max_tokens=mt, **res); out.append(row); print(row, flush=True)
with open(ROOT/"data"/"probe_fail.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())) if out else None
    if w: w.writeheader(); w.writerows(out)
print("rows", len(out))
