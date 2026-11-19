"""형식 실패 행 재시도 실험(2026-11-18). 합성 데이터. LM Studio에 해당 모델이 로드돼 있어야 한다.
배경: 컨텍스트 16384, max_tokens 12000으로 늘려도 Set A에서 같은 8건이 다시 실패했다. 한도 문제가 아니라 추론이 끝나지 않는 글이라면,
같은 요청을 다시 보내면 답이 나오는지(호출마다 결과가 달라지는지) 본다. 실패 처리 방식(재시도 대 사람 검수) 판단 근거용.
pred_<tag>.csv에서 pred_category가 빈 행을 같은 프롬프트(cap2)·같은 설정으로 최대 TRIES번 다시 호출하고 매 호출의 finish_reason과 토큰 수를 남긴다.
사용: VOC_MAX_TOKENS=12000 python scripts/retry_fail.py <모델> <pred_tag> [pred_tag...]   결과 data/retry_fail.csv"""
import csv, sys, os, re, json, time, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIES = 2
model, tags = sys.argv[1], sys.argv[2:]
os.environ["VOC_PROMPT"] = "cap2"; sys.argv = ["classify.py", model, "probe"]
ns = {"__file__": str(ROOT/"scripts"/"classify.py")}
exec(open(ROOT/"scripts"/"classify.py", encoding="utf-8").read().split("def ask")[0], ns)
SYSTEM = ns["SYSTEM"]
MT = int(os.environ.get("VOC_MAX_TOKENS", "12000"))
gold = {r["id"]: r for f in ("syn_voc_gold_v3.csv", "syn_voc_b_gold_v3.csv") for r in csv.DictReader(open(ROOT/"data"/f, encoding="utf-8-sig"))}
def call(text):
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
                       "max_tokens": MT, "temperature": 0}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type": "application/json"})
    t0 = time.time(); d = json.load(urllib.request.urlopen(req, timeout=900)); sec = round(time.time() - t0, 1)
    ch = d["choices"][0]; u = d.get("usage", {}); content = ch["message"].get("content") or ""
    m = re.search(r"\{.*?\}", content, re.S)
    try: j = json.loads(m.group(0))
    except Exception: j = {}
    return dict(sec=sec, finish=ch.get("finish_reason"), completion_tokens=u.get("completion_tokens"),
                pred_category=j.get("category", ""), pred_severity=j.get("severity", ""), pred_sentiment=j.get("sentiment", ""))
out = []
for tag in tags:
    for r in csv.DictReader(open(ROOT/"data"/f"pred_{tag}.csv", encoding="utf-8-sig")):
        if r["pred_category"]: continue
        for k in range(1, TRIES + 1):
            try: res = call(gold[r["id"]]["text"])
            except Exception as e: res = dict(sec=None, finish=f"error:{e}", completion_tokens=None, pred_category="", pred_severity="", pred_sentiment="")
            row = dict(tag=tag, id=r["id"], try_no=k, max_tokens=MT, **res); out.append(row); print(row, flush=True)
            if res["pred_category"]: break
with open(ROOT/"data"/"retry_fail.csv", "w", newline="", encoding="utf-8-sig") as f:
    if out:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("rows", len(out))
