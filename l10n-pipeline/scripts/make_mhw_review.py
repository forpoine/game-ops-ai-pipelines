"""몬헌 용어 EN·KO 검수표(사용자가 확인). glossary/mhw_poedb_terms.csv의 monster+item만(소재는 나중).
이미 사용자가 확정한 6개(glossary/몬헌_기입용.csv)는 표시만 하고 체크 대상에서 뺀다.
결과: out/mhw_review.html. 사용자가 틀린 줄에 고친 한국어를 쓰고 '결과 만들기' → 붙여 주면 반영.
실행: PYTHONIOENCODING=utf-8 python scripts/make_mhw_review.py
"""
import csv, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = [r for r in csv.DictReader((ROOT / "glossary" / "mhw_poedb_terms.csv").open(encoding="utf-8")) if r["type"] in ("monster", "item")]
done = {r["en"].strip().lower(): r["ko"] for r in csv.DictReader((ROOT / "glossary" / "몬헌_기입용.csv").open(encoding="utf-8")) if r.get("ko")}

trs = []
for i, r in enumerate(rows, 1):
    mine = done.get(r["en"].lower())
    st = f"<td class=ok>확정({html.escape(mine)})</td>" if mine else f"<td><input data-id='{r['api_id']}' data-en='{html.escape(r['en'], quote=True)}' placeholder='틀리면 고쳐 쓰기'></td>"
    trs.append(f"<tr><td>{i}</td><td>{'몬스터' if r['type']=='monster' else '아이템'}</td><td>{html.escape(r['en'])}</td><td class=ko>{html.escape(r['ko'])}</td>{st}</tr>")

page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>몬헌 용어 검수표</title>
<style>body{{font:15px/1.5 system-ui,'Malgun Gothic',sans-serif;max-width:900px;margin:0 auto;padding:12px 16px;color:#222}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:3px 8px}}th{{position:sticky;top:0;background:#eee}}
.ko{{font-weight:600}}.ok{{color:#2a7}}input{{width:100%;box-sizing:border-box}}textarea{{width:100%;height:120px}}
tr:nth-child(even){{background:#fafafa}}</style>
<h2>몬헌 월드 용어 검수표 (EN · KO, {len(rows)}개)</h2>
<p>한국어는 팬 데이터 사이트(mhw.poedb.tw) 값입니다. 공식 표기와 다르면 오른쪽 칸에 맞는 표기를 쓰세요. 맞으면 비워 두면 됩니다. 모르는 용어는 <b>?</b> 를 쓰면 제외합니다. 끝나면 아래 '결과 만들기' 결과를 Claude에게 붙여 주세요.</p>
<table><tr><th>#</th><th>종류</th><th>EN</th><th>KO (poedb)</th><th>수정</th></tr>{''.join(trs)}</table>
<p><button id=c style="font-size:16px;padding:6px 14px">결과 만들기</button></p><textarea id=o readonly></textarea>
<script>document.getElementById('c').onclick=()=>{{const f=[...document.querySelectorAll('input')].filter(i=>i.value.trim()).map(i=>i.dataset.id+' | '+i.dataset.en+' => '+i.value.trim());
document.getElementById('o').value='검수 완료 {len(rows)}개, 수정 '+f.length+'건\\n'+f.join('\\n')}};</script>"""
(ROOT / "out" / "mhw_review.html").write_text(page, encoding="utf-8")
print("written out/mhw_review.html", len(rows), "rows, 확정", sum(1 for r in rows if r["en"].lower() in done))
