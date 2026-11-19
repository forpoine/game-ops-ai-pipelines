"""합성 VOC 본문을 임베딩해 data/emb_<tag>.npy 로 저장. 전부 합성 데이터.
사용: python scripts/embed.py <a|b>   (a: Set A 150건, b: Set B 80건)
LM Studio 임베딩 모델만 쓴다. LLM을 내리거나 올리지 않는다(다른 작업이 쓰는 중일 수 있음).
nomic-embed-text-v1.5는 용도 접두어를 권장해서 'clustering: '을 붙인다.
다국어 비교(2026-11-18): VOC_EMB=m3 이면 bge-m3(접두어 없음)로 data/emb_<tag>_m3.npy 에 저장(nomic 결과는 그대로 둠)."""
import csv, sys, json, os, pathlib, urllib.request
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {"a": "syn_voc_gold.csv", "b": "syn_voc_b_gold.csv"}
EMB = os.environ.get("VOC_EMB", "")
MODEL, PREFIX = {"": ("text-embedding-nomic-embed-text-v1.5", "clustering: "), "m3": (os.environ.get("VOC_EMB_ID", "bge-m3"), "")}[EMB]
SFX = f"_{EMB}" if EMB else ""
tag = sys.argv[1].lower()
rows = list(csv.DictReader(open(ROOT/"data"/FILES[tag], encoding="utf-8-sig")))
vecs = []
for i in range(0, len(rows), 32):
    batch = [PREFIX + r["text"] for r in rows[i:i+32]]
    body = json.dumps({"model": MODEL, "input": batch}).encode()
    req = urllib.request.Request("http://localhost:1234/v1/embeddings", body, {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300))["data"]
    vecs += [x["embedding"] for x in sorted(d, key=lambda x: x["index"])]
    print(i + len(batch), "/", len(rows), flush=True)
np.save(ROOT/"data"/f"emb_{tag}{SFX}.npy", np.array(vecs, dtype=np.float32))
print("saved", ROOT/"data"/f"emb_{tag}{SFX}.npy", np.array(vecs).shape)
