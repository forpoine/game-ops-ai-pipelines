"""별명 판정 시트(2026-11-24). extracted_ko.json의 오답 표기를 용어별로 모아 HTML 한 장으로 만든다.
용어별 글 목록(out/alias_list.txt)도 같이 만든다. 판정은 results/alias_judgments.tsv에 적고 score_alias.py로 채점한다.
한글이 없는 표기(영어 그대로)와 빈 표기는 시트에 넣지 않는다(공식 한국어명일 수 없으므로 자동으로 오답).
사용: PYTHONIOENCODING=utf-8 python scripts/make_alias_sheet.py -> out/alias_sheet.html
"""
import html, json, re
from collections import defaultdict
from measure import ROOT

X = json.loads((ROOT / "results" / "extracted_ko.json").read_text(encoding="utf-8"))
SHORT = {"google_gemma-4-12b-qat": "Gemma", "openai_gpt-oss-20b": "gpt-oss", "qwen3-14b": "Qwen",
         "claude-haiku-5-5": "Haiku", "gemini-3.5-flash-lite": "Gemini"}
HANGUL = re.compile(r"[가-힣]")
groups = defaultdict(lambda: {"meta": None, "spans": defaultdict(set)})
skipped = 0
for x in X:
    if x["match"]:
        continue
    sp = (x["span"] or "").strip()
    if not sp or x["bad"] or not HANGUL.search(sp):
        skipped += 1
        continue
    g = groups[x["api_id"]]
    g["meta"] = x
    g["spans"][re.sub(r"\s+", " ", sp)].add(SHORT[x["model"]])

cards, n_span = [], 0
for api_id, g in sorted(groups.items(), key=lambda kv: (kv[1]["meta"]["type"], kv[1]["meta"]["official"])):
    m = g["meta"]
    rows = []
    for sp, models in sorted(g["spans"].items(), key=lambda kv: -len(kv[1])):
        n_span += 1
        rows.append(f'<label class="s"><input type="checkbox" data-alias="{html.escape(sp)}"> '
                    f'<b>{html.escape(sp)}</b> <small>{", ".join(sorted(models))}</small></label>')
    kind = "몬스터" if m["type"] == "pokemon" else "아이템"
    cards.append(f'''<div class="c" data-id="{html.escape(api_id)}" data-off="{html.escape(m["official"])}">
<div class="h">{kind} · {html.escape(m["en"])}</div><div class="o">공식(월드): <b>{html.escape(m["official"])}</b></div>
{"".join(rows)}<input class="note" placeholder="메모(예: 라이즈 공식명, 용어집이 틀림 등)"></div>''')

page = f'''<!doctype html><meta charset="utf-8"><title>별명 판정</title>
<style>body{{font:15px/1.6 system-ui,sans-serif;max-width:860px;margin:24px auto;padding:0 16px;background:#fafafa;color:#222}}
.c{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px 14px;margin:10px 0}}.c.done{{border-color:#4a8}}
.h{{font-size:12px;color:#777}}.o{{margin:2px 0 6px}}.s{{display:block;margin:2px 0}}small{{color:#999}}
.note{{font:inherit;width:60%;margin-top:6px}}#bar{{position:sticky;top:0;background:#fafafa;padding:8px 0;border-bottom:1px solid #ddd;z-index:1}}
textarea{{width:100%;height:140px}}</style>
<div id="bar"><b>모델이 쓴 한국어 표기 중 다른 시리즈 공식명 고르기</b> · 용어 {len(cards)}개, 표기 {n_span}개 · 체크한 표기 <span id="cnt">0</span>개
<button onclick="out()">결과 복사</button><br><small>몬헌 다른 시리즈(라이즈, 와일즈, 4G 등)에서 쓰는 공식 한국어명이면 체크. 체크 안 한 표기는 오답으로 둔다. 모르면 비워 두고 메모에 "모름".</small></div>
{"".join(cards)}
<textarea id="res" placeholder="결과 복사를 누르면 여기에 나옵니다"></textarea>
<script>
const cnt=()=>{{document.getElementById('cnt').textContent=document.querySelectorAll('input[data-alias]:checked').length;
document.querySelectorAll('.c').forEach(c=>c.classList.toggle('done',!!c.querySelector('input:checked')||!!c.querySelector('.note').value))}};
document.addEventListener('input',cnt);
function out(){{const L=[];document.querySelectorAll('.c').forEach(c=>{{const id=c.dataset.id;
c.querySelectorAll('input[data-alias]:checked').forEach(i=>L.push(['ALIAS',id,i.dataset.alias].join('\\t')));
const n=c.querySelector('.note').value.trim();if(n)L.push(['NOTE',id,n].join('\\t'))}});
const t=L.join('\\n')||'(체크 없음)';document.getElementById('res').value=t;navigator.clipboard&&navigator.clipboard.writeText(t)}}
</script>'''
(ROOT / "out" / "alias_sheet.html").write_text(page, encoding="utf-8")

# 복사해 붙이기 좋은 글 목록(2026-11-24 사용자 요청). 번호 -> api_id 대응은 alias_list.json에 둔다.
lines, index = [], []
for n, (api_id, g) in enumerate(sorted(groups.items(), key=lambda kv: (kv[1]["meta"]["type"], kv[1]["meta"]["official"])), 1):
    m = g["meta"]
    spans = [sp for sp, _ in sorted(g["spans"].items(), key=lambda kv: -len(kv[1]))]
    lines.append(f'{n}. {m["en"]} | 월드 공식: {m["official"]} | 모델 표기: {" / ".join(spans)}')
    index.append({"n": n, "api_id": api_id, "official": m["official"], "spans": spans})
(ROOT / "out" / "alias_list.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(ROOT / "out" / "alias_list.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
print("용어", len(cards), "표기", n_span, "시트에서 뺀 오답(영어 그대로·빈 표기·추출 실패)", skipped)
