"""용어집 없이(baseline) vs 용어 보호(protected) 번역의 공식 표기 일치율 측정.
실행: PYTHONIOENCODING=utf-8 python scripts/measure.py --model google/gemma-4-12b-qat --mode baseline --n 40
결과: results/<model>_<mode>.json (문장별 출력과 일치 여부). LM Studio 로컬 서버 필요.
한 번 호출에 ko/ja/es를 JSON으로 함께 번역한다(호출 수 절감).
"""
import argparse, csv, json, random, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://localhost:1234/v1/chat/completions"
LANGS = ["ko", "ja", "es"]

ITEM_T = [
    "Use a {t} before the boss fight to recover your HP.",
    "Players can buy a {t} at the shop for 200 coins.",
    "Each trainer receives one {t} as a login reward.",
    "A {t} will be sent to your mailbox after maintenance.",
    "The drop rate of {t} has been increased during the event.",
]
MON_T = [
    "A wild {t} appeared near the lake during the event.",
    "The rate of encountering {t} has been doubled this weekend.",
    "Defeat {t} to earn a special reward.",
    "{t} has been added to the new season raid lineup.",
]

# 몬헌 측정용(2026-11-18, 사용자 요청): 장르 표현으로 바꾸고 문장 구조·길이·용어 위치를 다양하게.
# 지역명(Ancient Forest, Rotten Vale)은 사용자가 정한 것. 보호하지 않고 채점에서도 제외(대상 용어만 채점).
MHW_ITEM_T = [
    "Players can buy a {t} at the provisions shop for 200 zenny.",
    "Each hunter receives one {t} as a login reward.",
    "A {t} will be sent to your item box after maintenance.",
    "The drop rate of {t} has been increased during the event.",
    "Due to a display error, the description of {t} was shown incorrectly. This has been fixed.",
    "Hunters who log in during the festival will receive 3 {t}.",
    "Complete the daily bounty to receive {t} x5.",
    "The maximum number of {t} you can carry has been raised from 10 to 20.",
    "{t} can now be gathered in the Ancient Forest.",
    "We have fixed an issue where {t} could not be sold at the shop.",
    "Bring a {t} with you before heading to the Rotten Vale.",
    "As compensation, all hunters will receive 10 {t} by November 25.",
]
MHW_MON_T = [
    "{t} has been sighted in the Ancient Forest.",
    "{t} appears twice as often in the Rotten Vale this weekend.",
    "Hunt {t} to earn a special reward.",
    "{t} has been added to the new event quest lineup.",
    "Slay {t} within 15 minutes to receive bonus points.",
    "We have fixed an issue where {t} could become stuck in the Ancient Forest.",
    "The event quest featuring {t} will run until December 3.",
    "Capture {t} three times to unlock a limited title.",
    "After the update, {t} will no longer appear in the Rotten Vale.",
    "A stronger {t} will appear in the Ancient Forest from November 20.",
]
# 공지체 틀(2026-11-18, 사용자가 붙여 준 실제 한국어 공지 2건의 구조만 참고해 Claude가 영어로 새로 씀, 문장 복사 없음).
# HR 조건, ※ 개방 조건, 두 문장 이상, 게임 고유어(Tempered, Handler, Astera 등)가 섞임. 고유어는 보호·채점 안 함.
NOTICE_ITEM_T = [
    "HR 100 or above: clearing the arch-tempered quest now rewards {t} x3. ※ The event quest must be cleared first.",
    "From HR 50, {t} can be obtained repeatedly from optional quests that could only be cleared once in the story.",
    "※ {t} will be added to the provisions stockpile after you talk to the Quartermaster in Astera.",
    "{t} can now be gathered with low probability in the Rotten Vale during the event.",
    "Prepare {t} in advance before taking on the high-difficulty optional quest!",
    "Hunters at HR 21 or above will receive {t} x5 after clearing the investigation mission.",
    "The bonus reward for the endurance quest has been changed to {t}. ※ Rewards already received are not affected.",
    "Due to an issue, {t} was not shown in the item box. This will be fixed in the next update.",
    "Clear all special environment quests to unlock the option to craft {t} at the workshop.",
    "During the festival, {t} x10 will be delivered to all hunters who reach HR 100 or above.",
]
NOTICE_MON_T = [
    "Tempered {t} now appears at HR 100 or above. ※ Unlocked after clearing the special investigation quest.",
    "Starting from HR 50, you can repeatedly take on the {t} quest, which could only be challenged once in the story.",
    "{t} appears with low probability in the Rotten Vale during the event period and can be turned into a quest.",
    "Arch-tempered {t} joins the high-difficulty optional quest lineup. ※ Requires HR 100 or above.",
    "Hunt {t}, the apex of the Ancient Forest, and prepare your equipment in advance!",
    "After reaching HR 21, talk to the Handler in Astera to unlock the {t} investigation mission.",
    "A new endurance quest featuring {t} has been added. ※ Unlocked after clearing all event quests.",
    "{t} will be shown in the environment overview once you clear the specific mission unlocked at HR 50.",
    "Slay {t} twice in a row within 30 minutes to earn a limited guild card title.",
    "Known among hunters for its fierce attacks, {t} returns to the Rotten Vale. Craft resistant armor before you go!",
]


def load_terms(glossary="pokeapi"):
    if glossary == "mhw":  # 몬헌: 사용자가 ko를 검수한 몬스터·아이템만, type은 pokemon 자리에 monster
        with (ROOT / "glossary" / "mhw_poedb_terms.csv").open(encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if "user-verified" in r["note"]]
        for r in rows:
            if r["type"] == "monster":
                r["type"] = "pokemon"
        return [r for r in rows if all(r[lg] for lg in ("en", "ko", "ja", "es"))]
    with (ROOT / "glossary" / "pokeapi_terms.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_sentences(n, seed=7, glossary="pokeapi", tpl_set="basic"):
    rnd = random.Random(seed)
    terms = load_terms(glossary)
    # 영어와 한국어가 다른 항목만(영어 그대로 두는 오답이 정답처럼 보이지 않게)
    items = [t for t in terms if t["type"] == "item" and t["ko"] != t["en"]]
    mons = [t for t in terms if t["type"] == "pokemon"]
    n_item = round(n * 0.7)
    chosen = rnd.sample(items, n_item) + rnd.sample(mons, n - n_item)
    out = []
    for i, t in enumerate(chosen):
        if tpl_set == "notice":  # 공지체 틀
            tpl = rnd.choice(NOTICE_ITEM_T if t["type"] == "item" else NOTICE_MON_T)
        elif glossary == "mhw":  # 몬헌 전용 틀(장르 표현, 지역명은 보호·채점 안 함)
            tpl = rnd.choice(MHW_ITEM_T if t["type"] == "item" else MHW_MON_T)
        else:
            tpl = rnd.choice(ITEM_T if t["type"] == "item" else MON_T)
        out.append({"id": i, "term": t, "text": tpl.format(t=t["en"]),
                    "tagged": tpl.format(t=f"[[T1]]")})
    return out


def chat(model, system, user, max_tokens=4000):
    import os
    if os.environ.get("NOTHINK"):  # Qwen3: 생각 끄기(프롬프트 끝에 /no_think)
        user = user + " /no_think"
    body = json.dumps({"model": model, "temperature": 0.2, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(API, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        ch = json.loads(r.read())["choices"][0]
    # 원인 추적용: 종료 사유(length면 토큰 소진)와 원응답을 함께 돌려준다
    return (ch["message"].get("content") or ""), ch.get("finish_reason")


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


SYS_BASE = ("You translate game announcements. Translate the English sentence into Korean, "
            "Japanese and Spanish. Reply with only JSON: {\"ko\":\"...\",\"ja\":\"...\",\"es\":\"...\"}.")
SYS_PROT = ("You translate game announcements. Translate the English sentence into Korean, "
            "Japanese and Spanish. The token [[T1]] is a protected game term: copy it exactly "
            "as [[T1]] into every translation, do not translate or alter it. "
            "Reply with only JSON: {\"ko\":\"...\",\"ja\":\"...\",\"es\":\"...\"}.")


def norm(s):
    return re.sub(r"\s+", "", s).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", choices=["baseline", "protected"], required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--glossary", choices=["pokeapi", "mhw"], default="pokeapi")
    ap.add_argument("--tpl", choices=["basic", "notice"], default="basic")
    a = ap.parse_args()

    sents = build_sentences(a.n, glossary=a.glossary, tpl_set=a.tpl)
    res_dir = ROOT / "results"
    res_dir.mkdir(exist_ok=True)
    suffix = ("_mhw" if a.glossary == "mhw" else "") + ("_notice" if a.tpl == "notice" else "")
    out_path = res_dir / f"{a.model.replace('/', '_')}_{a.mode}{suffix}.json"
    results = []
    t0 = time.time()
    for s in sents:
        src = s["tagged"] if a.mode == "protected" else s["text"]
        attempts = []
        for _ in range(2):  # 빈 결과(파싱 실패)면 1회 재시도, 시도 기록은 모두 남김
            raw, fin = chat(a.model, SYS_PROT if a.mode == "protected" else SYS_BASE, src)
            tr = parse_json(raw)
            attempts.append({"finish": fin, "raw": raw})
            if all(tr.get(lg) for lg in LANGS):
                break
        rec = {"id": s["id"], "api_id": s["term"]["api_id"], "type": s["term"]["type"],
               "src": s["text"], "attempts": attempts, "langs": {}}
        for lg in LANGS:
            text = tr.get(lg, "")
            official = s["term"][lg]
            if a.mode == "protected":
                kept = "[[T1]]" in text
                final = text.replace("[[T1]]", official)
                ok = kept
            else:
                final, kept = text, None
                ok = norm(official) in norm(text)
            rec["langs"][lg] = {"out": final, "official": official, "placeholder_kept": kept, "match": ok}
        results.append(rec)
        print(s["id"], s["term"]["en"], {lg: rec["langs"][lg]["match"] for lg in LANGS},
              f"{time.time()-t0:.0f}s", flush=True)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    print("== summary", a.model, a.mode, "n=", len(results))
    for lg in LANGS:
        for kind in (None, "item", "pokemon"):
            rows = [r for r in results if kind in (None, r["type"])]
            m = sum(r["langs"][lg]["match"] for r in rows)
            print(f"{lg} {kind or 'all':8s} {m}/{len(rows)}")


if __name__ == "__main__":
    main()
