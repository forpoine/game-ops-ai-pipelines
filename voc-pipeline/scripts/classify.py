"""합성 VOC를 LM Studio 모델로 분류(카테고리·심각도·감성). 전부 합성 데이터.
사용: python scripts/classify.py <model_id> <tag> [N]   예: classify.py google/gemma-4-12b-qat gemma 5
입력 data/syn_voc_gold.csv (정답 열은 모델에 보내지 않음), 출력 data/pred_<tag>.csv
실패 처리(2026-11-18 사용자 확정): 형식이 깨진 응답은 같은 요청으로 한 번 다시 보내고, 그래도 실패하면 needs_review=1(사람 검수).
VOC_RETRY=0이면 재시도하지 않는다(이 코드 추가 전 측정과 같은 동작)."""
import csv, sys, json, pathlib, urllib.request, re, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
import os
GOLD = ROOT/"data"/(os.environ.get("VOC_GOLD") or ("syn_voc_b_gold.csv" if os.environ.get("VOC_SET")=="b" else "syn_voc_gold.csv"))
model, tag = sys.argv[1], sys.argv[2]
OUT = ROOT/"data"/f"pred_{tag}.csv"
from prompts import build_system
SYSTEM = build_system(os.environ.get("VOC_PROMPT"))
# VOC_SCHEMA=1: LM Studio 구조화 출력(response_format json_schema)으로 형식을 강제(2026-11-19 실험). 기본은 끔(이전 측정과 같은 동작).
SCHEMA = {"type":"json_schema","json_schema":{"name":"voc_label","strict":True,"schema":{
    "type":"object","additionalProperties":False,"required":["category","severity","sentiment"],
    "properties":{"category":{"type":"string","enum":["BUG","BAL","MON","OPS","COM","ETC"]},
                  "severity":{"type":"string","enum":["S1","S2","S3","S4"]},
                  "sentiment":{"type":"string","enum":["pos","neu","neg"]}}}}}
def ask(text):
    req_body = {"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":text}],
                "max_tokens":int(os.environ.get("VOC_MAX_TOKENS","4000")),"temperature":0}
    if os.environ.get("VOC_SCHEMA") == "1": req_body["response_format"] = SCHEMA
    body = json.dumps(req_body).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["choices"][0]["message"]["content"]
RETRY = int(os.environ.get("VOC_RETRY", "1"))
VALID = {"category":{"BUG","BAL","MON","OPS","COM","ETC"},"severity":{"S1","S2","S3","S4"},"sentiment":{"pos","neu","neg"}}
def parse(raw):
    m = re.search(r"\{.*?\}", raw or "", re.S)
    try: d = json.loads(m.group(0))
    except Exception: d = {}
    return d, all(d.get(k) in v for k, v in VALID.items())
rows = list(csv.DictReader(open(GOLD, encoding="utf-8-sig")))
n = int(sys.argv[3]) if len(sys.argv) > 3 else len(rows)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["id","pred_category","pred_severity","pred_sentiment","sec","raw","tries","needs_review"]); w.writeheader()
    for r in rows[:n]:
        t0 = time.time(); tries = 0
        while True:
            tries += 1; raw = ask(r["text"]); d, ok = parse(raw)
            if ok or tries > RETRY: break
        sec = round(time.time()-t0, 1)
        w.writerow({"id":r["id"],"pred_category":d.get("category",""),"pred_severity":d.get("severity",""),
                    "pred_sentiment":d.get("sentiment",""),"sec":sec,"raw":re.sub(r"\s+"," ",raw or "")[:200],
                    "tries":tries,"needs_review":0 if ok else 1})
        f.flush(); print(r["id"], d, sec, flush=True)
