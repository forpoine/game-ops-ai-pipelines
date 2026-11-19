"""Photoshop(JSX)로 공지 카드(5종 x en/ko/ja/es = 20장)를 렌더하고 글자가 본문 영역에 들어가는지 실측한다. LLM 없음.
- 입력: notices/translated_<모델>.json (기본 Gemma). 본문 = en 원문, ko 원문, ja/es 번역(용어 치환 후)
- 카드: 1000x720px, 본문 영역 880x520px, 28px. 폰트 ko NotoSansKR-Regular, ja NotoSansJP-Regular, en/es ArialMT
- 측정: 본문 글자가 차지한 높이를 bounds로 읽음(박스를 4000px로 열어 잘림 없이). 520px 초과면 overflow.
- 카드는 "SAMPLE (synthetic data)" 표기. 로고·이미지 없음. 공식 공지처럼 보이지 않게 일반 디자인.
- Photoshop은 -r 로 실행하고 끝나면 스크립트가 종료(app.quit). 작업 파일은 ASCII 경로(스크래치패드)에 두고 결과만 복사.
실행: PYTHONIOENCODING=utf-8 python scripts/make_cards.py [translated_파일명]
"""
import json, shutil, subprocess, sys, time
from pathlib import Path
from checker import ROOT, load_glossary
from notices import render, load_notices

import os, tempfile
SC = Path(os.environ.get("PS_WORK") or Path(tempfile.gettempdir())/"l10n_ps")  # ASCII 경로 권장
PS = os.environ.get("PHOTOSHOP_EXE", r"C:\Program Files\Adobe\Adobe Photoshop 2026\Photoshop.exe")
FONT = {"en": "ArialMT", "ko": "NotoSansKR-Regular", "ja": "NotoSansJP-Regular", "es": "ArialMT"}
BODY_H = 520

JSX = r"""
#target photoshop
app.displayDialogs = DialogModes.NO;
app.preferences.rulerUnits = Units.PIXELS;
app.preferences.typeUnits = TypeUnits.PIXELS;
var BASE = "%BASE%";
function readText(p){var f=new File(p);f.encoding="UTF-8";f.open("r");var t=f.read();f.close();return t;}
function writeText(p,s){var f=new File(p);f.encoding="UTF-8";f.open("w");f.write(s);f.close();}
function color(r,g,b){var c=new SolidColor();c.rgb.red=r;c.rgb.green=g;c.rgb.blue=b;return c;}
function addText(doc,contents,font,size,col,x,y,w,h){
  var l=doc.artLayers.add(); l.kind=LayerKind.TEXT; var t=l.textItem;
  if(w){t.kind=TextType.PARAGRAPHTEXT; t.position=[x,y]; t.width=w; t.height=h;} else {t.position=[x,y];}
  t.font=font; t.size=size; t.color=col; t.contents=contents; return l;
}
try {
  var cards = eval("(" + readText(BASE+"input.json") + ")");
  new Folder(BASE+"cards").create();
  var res = [];
  for (var i=0;i<cards.length;i++){
    var c=cards[i];
    var doc=app.documents.add(1000,720,72,"card",NewDocumentMode.RGB,DocumentFill.WHITE);
    doc.selection.select([[0,0],[1000,0],[1000,90],[0,90]]); doc.selection.fill(color(43,47,58)); doc.selection.deselect();
    addText(doc,c.header,"ArialMT",28,color(255,255,255),40,58,0,0);
    var body=addText(doc,c.body,c.font,28,color(34,34,34),60,130,880,4000);
    var bottom=body.bounds[3].value;
    var used=bottom-130;
    body.textItem.height=%BODY_H%;
    addText(doc,"SAMPLE (synthetic data, not an official notice)","ArialMT",18,color(120,120,120),60,700,0,0);
    doc.saveAs(new File(BASE+"cards/"+c.name+".png"), new PNGSaveOptions(), true, Extension.LOWERCASE);
    res.push('{"name":"'+c.name+'","used":'+Math.round(used)+',"font":"'+c.font+'"}');
    doc.close(SaveOptions.DONOTSAVECHANGES);
  }
  writeText(BASE+"measure.json","["+res.join(",")+"]");
  writeText(BASE+"done.txt","ok");
} catch(e) { writeText(BASE+"done.txt","ERR "+e+" line "+e.line); }
app.quit();
"""


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "translated_google_gemma-4-12b-qat.json"
    g = load_glossary()
    notices = json.loads((ROOT / "notices" / name).read_text(encoding="utf-8"))
    cards = []
    for n in notices:
        short = n["id"].split("-")[0]
        texts = {"en": n["en"], "ko": n["tr"]["ko"], "ja": n["tr"]["ja"], "es": n["tr"]["es"]}
        for lg, body in texts.items():
            cards.append({"name": f"{short}_{lg}", "header": f"{short}  |  {lg.upper()}  |  NOTICE SAMPLE",
                          "body": body, "font": FONT[lg], "lang": lg, "chars": len(body)})
    SC.mkdir(parents=True, exist_ok=True)
    for f in ("done.txt", "measure.json"):
        (SC / f).unlink(missing_ok=True)
    shutil.rmtree(SC / "cards", ignore_errors=True)
    (SC / "input.json").write_text(json.dumps(cards, ensure_ascii=True), encoding="utf-8")  # \u 이스케이프(eval용)
    base = str(SC).replace("\\", "/") + "/"
    (SC / "cards.jsx").write_text(JSX.replace("%BASE%", base).replace("%BODY_H%", str(BODY_H)), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Start-Process '{PS}' -ArgumentList '-r','{SC / 'cards.jsx'}'"], check=True)
    t0 = time.time()
    while not (SC / "done.txt").exists():
        if time.time() - t0 > 420:
            sys.exit("timeout: Photoshop이 끝나지 않음(대화상자 가능성). 스크래치패드 ps 폴더 확인")
        time.sleep(3)
    status = (SC / "done.txt").read_text(encoding="utf-8")
    if status != "ok":
        sys.exit("JSX 오류: " + status)
    meas = {m["name"]: m for m in json.loads((SC / "measure.json").read_text(encoding="utf-8"))}
    out = ROOT / "out" / "cards"
    out.mkdir(parents=True, exist_ok=True)
    for p in (SC / "cards").glob("*.png"):
        shutil.copy(p, out / p.name)
    rows, dens = [], {}
    for c in cards:
        m = meas[c["name"]]
        rows.append({"name": c["name"], "lang": c["lang"], "chars": c["chars"], "used_px": m["used"],
                     "fits": m["used"] <= BODY_H, "font": c["font"]})
        d = dens.setdefault(c["lang"], [0, 0])
        d[0] += c["chars"]; d[1] += m["used"]
    # 언어별 추정 최대 글자 수: (총 글자/총 사용높이) x 영역 높이. 선형 가정이라 추정값.
    cap = {lg: int(ch / used * BODY_H) for lg, (ch, used) in dens.items()}
    result = {"card_px": [1000, 720], "body_area_px": [880, BODY_H], "font_px": 28, "rows": rows,
              "estimated_capacity_chars": cap, "source": name}
    (ROOT / "results" / "ps_measure.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("cards:", len(list(out.glob('*.png'))), "| 넘침", sum(not r["fits"] for r in rows), "/", len(rows))
    print("최대 사용 높이(px):", {lg: max(r["used_px"] for r in rows if r["lang"] == lg) for lg in cap})
    print("추정 최대 글자 수(880x520, 28px):", cap)


if __name__ == "__main__":
    main()
