"""정답 v3: v2 정답에 심각도 경계 규칙 3개(01의 1-2 아래, 2026-11-18)를 행별로 적용한다. 합성 데이터. LM Studio 불필요.
입력 data/syn_voc_gold_v2.csv, syn_voc_b_gold_v2.csv -> 출력 data/syn_voc_gold_v3.csv, syn_voc_b_gold_v3.csv
v2 파일은 보존하고, 바뀐 행은 `severity_v2`(바뀌기 전 값)와 `v3_rule`(적용한 규칙)에 남긴다.
규칙 A: 구매 전에 알 수 있던 패키지 구성·월정액 혜택이 아쉽다는 불만 -> S4
규칙 B: 보상 못 받음, 진행 손실을 동반한 튕김(약속·재화 손실) -> S2
규칙 C: 퀘스트 완료 표시 안 됨 -> S2 (사용자가 이미 S2로 판단한 유형)
행별로 글을 읽고 정했다. 판단 보류: SYNB-0074(튕김, "중요한 전략을 잃는"이 진행 손실인지 불명확)는 바꾸지 않았다.
규칙 1(쉽다는 난이도 불만 S4)과 노트 불일치 S3은 정답이 이미 같아 바꿀 행이 없다."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CHANGES = {
    "syn_voc_gold_v2.csv": ("syn_voc_gold_v3.csv", {
        "SYN-0013": ("S4", "A"), "SYN-0047": ("S4", "A"), "SYN-0116": ("S4", "A"), "SYN-0131": ("S4", "A"),
        "SYN-0070": ("S2", "B"), "SYN-0141": ("S2", "B"), "SYN-0128": ("S2", "B"), "SYN-0066": ("S2", "C")}),
    "syn_voc_b_gold_v2.csv": ("syn_voc_b_gold_v3.csv", {
        "SYNB-0031": ("S4", "A"), "SYNB-0036": ("S4", "A"), "SYNB-0073": ("S4", "A"), "SYNB-0048": ("S4", "A"),
        "SYNB-0065": ("S2", "B"), "SYNB-0067": ("S2", "B"), "SYNB-0075": ("S2", "B"), "SYNB-0071": ("S2", "B")}),
}
for src, (dst, ch) in CHANGES.items():
    rows = list(csv.DictReader(open(ROOT/"data"/src, encoding="utf-8-sig")))
    fields = list(rows[0].keys()) + ["severity_v2", "v3_rule"]
    n = 0
    with open(ROOT/"data"/dst, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            r["severity_v2"] = r["gold_severity"]; r["v3_rule"] = ""
            if r["id"] in ch:
                new, rule = ch[r["id"]]
                assert r["gold_severity"] != new, r["id"]
                r["gold_severity"] = new; r["v3_rule"] = rule; n += 1
            w.writerow(r)
    assert n == len(ch), (src, n, len(ch))
    print(f"{src} -> {dst}: {n}건 변경")
