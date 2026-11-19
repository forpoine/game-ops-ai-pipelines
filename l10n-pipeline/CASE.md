# 케이스 초안: 용어 보호 다국어 공지 파이프라인 + 자동 검수

## 한 줄
게임 용어는 번역이 아니라 매핑이라서, AI에게 용어를 맡기지 않고 문장만 맡기고 규칙으로 검수하는 다국어 공지 파이프라인을 만들고 잰 기록.

## Problem
- 다국어 공지에서 게임 용어는 공식 표기가 정답이다. 그런데 LLM은 이를 번역해 버린다. 예: Potion을 공식명(상처약 / キズぐすり)이 아닌 포션 / ポーション으로 옮긴다.
- 틀린 용어는 문장이 자연스러워서 눈으로 잡기 어렵고, 숫자·날짜 오류와 확률 합계 오류까지 섞이면 공지마다 사람이 언어별로 대조해야 한다.

## Research (잰 것)
- 공식 표기 정답지: PokéAPI에서 영·한·일·스페인어가 모두 있는 552개(아이템 154, 포켓몬 398).
- 같은 영어 문장 40개를 용어집 없이 3개 로컬 모델(Gemma 12B, gpt-oss 20B, Qwen3 14B)에 번역시켜 공식 표기가 그대로 들어간 비율을 셈.

| 모델 | 한국어 | 일본어 | 스페인어 |
|---|---|---|---|
| Gemma 12B | 7/40 | 3/40 | 14/40 |
| gpt-oss 20B | 3/40 | 2/40 | 17/40 |
| Qwen3 14B | 1/40 | 1/40 | 17/40 |

- 아이템이 포켓몬보다 훨씬 약했다(아이템 28개 중 한국어 일치 1~3개). 스페인어 포켓몬은 영어 이름 그대로가 정답인 경우가 많아 쉬웠다.
- 한계: 문장은 시드 고정 템플릿, 표본 40개. 소수점 단위 차이는 의미 없음.

## Action
1. 용어 보호: 원문의 용어를 ID로 표시(`{T:potion}`) → LLM에는 `[[T1]]` 자리표시자만 보내 주변 문장만 번역 → 돌아온 문장에 언어별 공식명을 코드로 삽입.
2. 검수기(LLM 없음, 규칙): 용어 공식명, 숫자·날짜·시각, 언어 누락, 글자 수 넘침, 확률 합 100%, 남은 자리표시자, 번역 안 된 영어 7종.
3. 사람 승인용 HTML 리포트: 공지별로 이슈를 빨갛게 표시하고 승인 체크.
3-1. Photoshop(JSX)로 공지 카드 20장(5종 × 4개 언어)을 렌더하고 본문 영역(880×520px, 28px)에 글자가 들어가는지 높이를 실측. 폰트는 한국어 Noto Sans KR, 일본어 Noto Sans JP.
4. 공지 5종(점검, 업데이트 노트, 시즌 이벤트, 보상 지급, 확률 정보)을 3개 모델로 번역해 검수.

## Insight
- 용어 보호를 하면 세 모델 모두 용어 자리표시자를 40/40 유지했다. 모델을 고르는 문제가 아니라 구조 문제였다. (이 40/40은 자리표시자 유지 여부이며 공식명 삽입은 코드가 해서 구조상 맞는다.)
- 모델이 틀리는 방식은 다양했고 매번 같지도 않았다. 1차 번역에서 Qwen3는 공지 1건의 자리표시자를 빼고 `{SERVICE}`로 바꿔 넣었고 검수기가 잡았다. 2차에서는 재현되지 않았다.
- 숫자만 보면 통과하지만 일본어 문장에 `3rd`, `Evening Lake`가 번역 안 된 채 남은 경우를 Photoshop 카드를 눈으로 보다가 발견했고, 영어 잔존 검사를 추가했다. 1차에서 세 모델 모두 공지 5종 중 2건씩 걸렸다.
- 원인 대부분이 가상 서비스의 이벤트명·상품명(Evening Lake, Hunter Box)이라, 이것도 보호 용어로 추가하고 다시 번역했다. 2차 이슈는 Gemma 1건(`3rd`), gpt-oss 1건(`Update v2.4`), Qwen3 0건. 용어로 다룰 범위를 넓히는 것이 모델을 바꾸는 것보다 효과가 컸다.
- 검수기를 실제 번역에 돌려 보니 오탐이 나왔고 규칙을 고쳤다: 일본어 날짜·시각 현지화(2026年12月3日, 午前2時), 스페인어 월 이름·서수·배수 단어. 숫자 비교는 "형식이 달라도 같은 값"을 알아봐야 했다.
- 몬헌 용어는 영어만 제공되는 데이터라 한국어는 직접 확정하고, 일본어·스페인어는 게임 데이터 표(팬 사이트)에서 가져왔다. 일반 웹 검색 요약은 아이템 일본어명을 두 개 틀리게 답해서 쓰지 않았다.

## Impact (잰 값)
- 공지 5종 번역+검수 소요(일본어·스페인어, 로컬 모델, 2회 실행): gpt-oss 18~19초, Qwen3 23~27초, Gemma 150~204초. 검수기는 5종을 1ms 미만.
- 수작업 검수(프로젝트 작성자 1명이 1회, 영어 원문과 한국어 번역을 용어표를 보며 눈으로만, 도구 없음): 15문장(정상 5, 한국어에 오류 10을 심음, 순서 섞고 정답 표시 없음)을 **193초(3분 13초)**에 검수해 심은 오류 10개 중 **8개**를 찾았고 정상 문장 1개를 잘못 표시했다(보상 만료일 14일 → 7일은 처음 놓친 것으로 채점했으나 검수자 재확인으로 찾은 것으로 정정). 놓친 2개와 이유:
  - 확률 합(갑옥 30% → 20%, 합 90%): 항목 하나하나는 그럴듯한 숫자라 문장만 읽어서는 이상하지 않다. 모든 확률을 더해 봐야 드러나는 오류다.
  - 용어(하이퍼볼 → 울트라볼): 울트라볼은 영어 Ultra Ball을 그대로 옮긴 말이라 자연스럽게 읽힌다. 반대로 공식명 하이퍼볼이 맞게 들어간 정상 문장을 오류로 표시했다. 용어표가 옆에 있어도 직역 표기는 통과시키고 공식 표기는 의심한 것이다.
  - 두 오류 모두 문장 자체는 자연스럽고, 합을 계산하거나 용어집과 대조해야 잡힌다. 검수기가 기계적으로 하는 일이 바로 이것이다. 같은 15문장을 검수기는 **약 6ms**에 10/10, 정상 문장 오탐 0. 한계: 1명 1회, 오류와 검수기를 같은 쪽(Claude)이 설계했다.
- 참고(1차 시험): 검수자가 읽지 못하는 스페인어·일본어에서는 사람이 10개 중 4개만 찾았지만 검수기는 언어를 몰라도 용어표·숫자 대조로 10개를 모두 잡았다. 담당자가 모든 언어를 읽지 못해도 검수가 되는 것이 이 도구의 차별점이다.
- 검수기 검출: 실제 번역에 오류 11개(용어 2, 숫자 3, 누락 2, 확률 1, 자리표시자 1, 넘침 1, 영어 잔존 1)를 심어 11/11 검출. 심기 전 원본 번역(2차 Gemma)에서도 이슈 1건이 나왔고 실제로 영어(`3rd`)가 남은 것이라 오탐이 아님. 단 검수기와 심은 오류를 같은 사람이 설계했으므로 "설계 범위 안의 검출률".
- Photoshop 실측: 카드 20장 모두 본문 영역(520px)에 들어감. 사용 높이 최대 en 127px, ko 126px, ja 126px, es 155px. 본문 영역에 들어가는 최대 글자 수는 선형 가정으로 추정(2차 번역 기준 ko 약 620자, ja 약 497자, es 약 999자). 실제 공지 본문은 약 200자 안팎이라 여유가 큼.

## 밝혀야 할 한계
- 일본어는 사람이 검증하지 않음. 몬헌 일본어·스페인어는 팬 사이트 데이터.
- 측정 문장은 템플릿 40개. 공지 5종은 지어낸 서비스·날짜·숫자. 가상 이벤트·상품명의 일본어·스페인어 표기는 이 프로젝트에서 정한 것.
- 글자 수 한도는 Photoshop 카드에서 잰 값으로 추정한 값(선형 가정). 실제 서비스 배너 규격이 아님. 카드 디자인은 단순한 샘플.

---

# Case draft (EN): Term-protected multilingual notice pipeline with automated review
> Draft (2026-11-18, written by Claude). Confirm or edit before it goes on the site or deck. Only values actually measured in this project; blanks are unmeasured.
> Nature: personal project. The service is fictional ({SERVICE}). Only text data from Monster Hunter and Pokémon is used (no images or logos, nothing that looks like an official notice).

## One line
Game terms are mapped, not translated. So the AI translates only the surrounding sentence, and rules review the result. This records building and measuring that pipeline.

## Problem
- In multilingual notices the official spelling of a game term is the right answer, but LLMs translate it. Example: Potion becomes the literal Korean/Japanese word instead of the official 상처약 / キズぐすり.
- Wrong terms hide inside fluent sentences, and with number, date and probability-sum errors on top, a person has to cross-check every notice in every language.

## Research (measured)
- Ground truth: 552 terms from PokéAPI that have English, Korean, Japanese and Spanish names (154 items, 398 Pokémon).
- 40 English sentences were translated without a glossary by three local models (Gemma 12B, gpt-oss 20B, Qwen3 14B). I counted how often the official spelling appeared.

| Model | Korean | Japanese | Spanish |
|---|---|---|---|
| Gemma 12B | 7/40 | 3/40 | 14/40 |
| gpt-oss 20B | 3/40 | 2/40 | 17/40 |
| Qwen3 14B | 1/40 | 1/40 | 17/40 |

- Items were much weaker than Pokémon (1 to 3 of 28 items matched in Korean). Spanish Pokémon names were easy because the English name is often the official one.
- Limits: seeded template sentences, only 40 samples. Small differences are not meaningful.

## Action
1. Term protection: mark terms by ID (`{T:potion}`), send only `[[T1]]` placeholders to the LLM so it translates the surrounding sentence, then insert the official name per language in code.
2. Reviewer (no LLM, rules): seven checks on official term, numbers/dates/times, missing language, length overflow, probability sum of 100%, leftover placeholders, untranslated English.
3. A human-approval HTML report that flags issues per notice with an approve checkbox.
3-1. Rendered 20 notice cards (5 notices x 4 languages) in Photoshop (JSX) and measured the text height against the body area (880x520 px, 28 px). Fonts: Noto Sans KR for Korean, Noto Sans JP for Japanese.
4. Five notice types (maintenance, update notes, season event, reward distribution, probability info) translated by the three models and reviewed.

## Insight
- With term protection all three models kept the term placeholder in 40 of 40 cases. The problem was structural, not a matter of picking a model. (This 40/40 measures placeholder retention; the official name is inserted by code, so it is correct by construction.)
- Models failed in different ways, and not the same way each run. In the first run Qwen3 dropped a placeholder in one notice and put `{SERVICE}` in its place; the reviewer caught it. It did not happen again in the second run.
- Numbers alone passed a Japanese sentence that still contained `3rd` and `Evening Lake` untranslated. I noticed it while looking at the Photoshop cards and added an untranslated-English check. In the first run all three models got 2 issues across the five notices.
- Most of those came from the fictional service's event and product names (Evening Lake, Hunter Box), so I added them as protected terms and translated again. Second-run issues: Gemma 1 (`3rd`), gpt-oss 1 (`Update v2.4`), Qwen3 0. Widening what counts as a term helped more than switching models.
- Running the reviewer on real translations produced false alarms and I fixed the rules: localized Japanese dates and times (2026年12月3日, 午前2時), and Spanish month names, ordinals and multiplier words. Number comparison has to recognize the same value in a different format.
- Monster Hunter data only had English, so I confirmed the Korean names myself and took Japanese and Spanish from a game-data table (a fan site). A general web search summary gave two wrong Japanese item names, so I did not use it.

## Impact (measured)
- Translate and review five notices (Japanese and Spanish, local models, two runs): gpt-oss 18 to 19 s, Qwen3 23 to 27 s, Gemma 150 to 204 s. The reviewer takes under 1 ms for all five.
- Manual review (the project author, one person, one run, English source against Korean translation, by eye with a glossary and no tools): 15 sentences (5 clean, 10 errors planted in Korean, shuffled, no answer marks) took **193 s (3 min 13 s)**. The person found **8 of the 10** planted errors and wrongly flagged 1 clean sentence (the reward expiry change, 14 days → 7 days, was first scored as missed and corrected to found after the reviewer rechecked). The 2 misses and why:
  - Probability sum (one rate changed 30% → 20%, total 90%): each rate looks plausible on its own, so the sentence reads fine. The error only shows when all rates are added up.
  - Term (하이퍼볼 → 울트라볼, a literal rendering of Ultra Ball): the literal name reads naturally. The person instead flagged the clean sentence that correctly used the official name 하이퍼볼. Even with the glossary at hand, the literal name passed and the official name looked suspicious.
  - Both errors sit in natural-sounding sentences and are caught only by adding up numbers or checking against the glossary, which is exactly the mechanical work the reviewer does. The reviewer took about **6 ms** on the same 15 sentences, 10 of 10 with 0 false alarms. Limits: one person, one run, and the errors and the reviewer were designed by the same side (Claude).
- Note (first test): in Spanish and Japanese, which the reviewer cannot read, the person found 4 of 10 while the tool caught all 10 by checking the glossary and numbers without reading the language. Review that works even when no one on the team reads every language is what sets this tool apart.
- Reviewer detection: 11 errors planted in real translations (2 term, 3 number, 2 missing, 1 probability, 1 placeholder, 1 overflow, 1 leftover English); 11 of 11 detected. The unmodified original (second-run Gemma) also raised 1 issue, a real case of English (`3rd`) left in the text, not a false alarm. The reviewer and the planted errors were designed by the same person, so this is a detection rate within the design scope.
- Photoshop measurement: all 20 cards fit the body area (520 px). Maximum used height: en 127 px, ko 126 px, ja 126 px, es 155 px. Estimated maximum characters in the body area, assuming linear scaling: based on the second run, ko about 620, ja about 497, es about 999. The actual notices are around 200 characters, so there is plenty of room.

## Limits to disclose
- Japanese was not verified by a person. Monster Hunter Japanese and Spanish come from a fan site.
- The measurement sentences are 40 templates. The five notices use invented services, dates and numbers. The Japanese and Spanish names of the fictional event and product were chosen in this project.
- Length limits are estimates from the Photoshop card measurement (linear assumption), not a real service banner spec. The card design is a simple sample.
