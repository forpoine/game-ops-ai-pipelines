"""Set B: spec_b의 각 행에 맞는 합성 VOC 본문을 LM Studio(qwen3-14b)로 생성. 전부 합성.
사용: python scripts/generate_voc.py [N]   (N이면 앞 N건만 시험)
출력: data/syn_voc_b_generated.csv (label_status=generated, is_synthetic=true)"""
import csv, sys, json, pathlib, urllib.request, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC, OUT = ROOT/"data"/"syn_voc_b_spec.csv", ROOT/"data"/"syn_voc_b_generated.csv"
MODEL = "qwen3-14b"
CAT = {"BUG":"버그·오류","BAL":"밸런스","MON":"과금·확률","OPS":"운영·공지","COM":"커뮤니티·불건전 이용","ETC":"기타(제안·칭찬·문의)"}
SEV = {"S1":"매우 긴급(다수 영향)","S2":"높음","S3":"보통","S4":"낮음"}
SENT = {"pos":"긍정","neu":"중립(차분한 어조)","neg":"부정"}
LANG = {"ko":"한국어","en":"영어","mixed":"한국어와 영어가 섞인 말투"}
def prompt(r):
    p = (f"가상의 모바일 게임 {{SERVICE}}에 유저가 남긴 의견 한 건을 써라.\n"
         f"- 주제: {r['seed']}\n- 언어: {LANG[r['lang']]}\n- 어조: {SENT[r['gold_sentiment']]}\n"
         f"- 문제의 급한 정도(글에 드러나게, 직접 단계명은 쓰지 말 것): {SEV[r['gold_severity']]}\n"
         f"- 말투: {r['style']}, 분량: {r['length']}. 이모티콘·오타 약간 허용.\n"
         "- 실제 게임 이름·캐릭터·실명·계정 ID 금지. 게임은 '이 게임'이나 {SERVICE}로만 부른다.\n")
    if r["ambiguous"] == "true":
        p += f"- 이 글은 '{CAT[r['gold_category']]}' 문제가 핵심이지만 '{CAT[r['secondary_category']]}' 이야기도 살짝 섞어 판단이 갈리게 쓴다.\n"
    if r["lang"] == "en":
        p += "- 반드시 영어로만 쓴다. 한글 사용 금지.\n"
    if r["lang"] == "mixed":
        p += "- 한국어 문장 안에 영어 단어·구를 자연스럽게 섞는다.\n"
    p += "출력은 유저 글 본문만, 따옴표·설명 없이. /no_think"
    return p
def ask(p):
    body = json.dumps({"model":MODEL,"messages":[{"role":"user","content":p}],"max_tokens":3000,"temperature":0.9}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/chat/completions", body, {"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"].strip().strip('"')
rows = list(csv.DictReader(open(SPEC, encoding="utf-8-sig")))
cols = ["id","ts","lang","style","length","text","gold_category","gold_severity","gold_sentiment","gold_cluster","ambiguous","label_status","is_synthetic"]
def gen(r):
    t = re.sub(r"\s+", " ", re.sub(r"<think>.*?</think>", "", ask(prompt(r)), flags=re.S)).strip()
    return {**{k:r[k] for k in cols if k in r}, "text":t, "label_status":"generated", "is_synthetic":"true"}
if len(sys.argv) > 2 and sys.argv[1] == "--ids":   # 지정한 id만 다시 생성해 기존 파일에 덮어쓴다
    ids = set(sys.argv[2:])
    cur = list(csv.DictReader(open(OUT, encoding="utf-8-sig")))
    spec = {r["id"]: r for r in rows}
    for k, row in enumerate(cur):
        if row["id"] in ids:
            cur[k] = gen(spec[row["id"]]); print("regen", row["id"], cur[k]["text"][:70], flush=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(cur)
else:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows[:n]:
            row = gen(r); w.writerow(row); f.flush()
            print(r["id"], r["gold_category"], r["gold_severity"], "|", row["text"][:70], flush=True)
