# game-ops-ai-pipelines

게임 서비스 운영 업무 두 가지를 로컬 LLM으로 자동화하고, 얼마나 맞는지 직접 잰 기록입니다. 원칙은 하나입니다: **AI는 초안을 만들고, 규칙과 사람이 검수한다.**

Two game-service operations tasks automated with local LLMs, with every number measured in this repo. One rule throughout: **the model drafts, rules and a person check.**

| 폴더 / Folder | 하는 일 / What it does |
|---|---|
| [`l10n-pipeline/`](l10n-pipeline/) | 게임 공지를 한·영·일·스페인어로 번역할 때 아이템·몬스터 이름이 공식 표기에서 벗어나지 않게 보호하고, 숫자·날짜·확률·글자 수를 규칙으로 검수 / Translates game notices (EN to KO/JA/ES) while locking item and monster names to official terms, then checks numbers, dates, probabilities and text length with rules |
| [`voc-pipeline/`](voc-pipeline/) | 유저 의견을 카테고리·심각도·감성으로 분류하고, 임베딩으로 묶어 급증을 감지하고, 담당 조직용 요약을 만듦 / Classifies player feedback (category, severity, sentiment), clusters it with embeddings, detects spikes and drafts summaries for the owning team |
| [`PROMPTS.md`](PROMPTS.md) | 두 파이프라인의 시스템 프롬프트 전문(코드에서 자동 추출) / Full system prompts, extracted from the code |

## 주요 결과 / Key results

모델: Gemma 4 12B (QAT), gpt-oss 20B, Qwen3 14B. 모두 LM Studio에서 양자화 모델로 로컬 실행(RTX 4080 SUPER 16GB).
Models: Gemma 4 12B (QAT), gpt-oss 20B, Qwen3 14B, all quantized and run locally in LM Studio (RTX 4080 SUPER 16GB).

**l10n-pipeline** (몬스터 헌터 용어 100문장, 공식 표기 일치 ko / ja / es)

| | Gemma | gpt-oss | Qwen3 |
|---|---|---|---|
| 통째 번역 / Plain translation | 6 / 10 / 39 | 4 / 7 / 34 | 4 / 6 / 32 |
| 용어 보호 / Term-protected | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |

- 용어 보호를 쓰면 공식명 정확도가 모델과 무관해진다. 그래서 가장 빠른 모델(gpt-oss, 문장당 약 3초, Gemma는 약 15초)을 고를 수 있다. / With protection, term accuracy no longer depends on the model, so the fastest model can be used.
- 한국어 검수 시험(오류 10개를 심은 15문장): 사람 1회 8/10, 193초. 검수기 10/10, 약 6ms. / Manual review test: one person found 8/10 in 193 s; the checker found 10/10 in about 6 ms.

**voc-pipeline** (합성 유저 의견, 세트별 정답은 사람이 확정한 것만 채점)

- 카테고리 정확도: Set A(150건) Gemma 141, gpt-oss 137. Set B(80건) Gemma 78, gpt-oss 73. / Category accuracy as above.
- 임베딩: bge-m3로 바꾸자 주제 군집 일치도(ARI)가 0.24에서 0.93(Set A)으로 올랐고, 급증 25건이 한 묶음으로 잡혔다. / Switching embeddings to bge-m3 raised cluster agreement (ARI) from 0.24 to 0.93 and kept a 25-post spike in one cluster.
- 자세한 수치와 해석: [`voc-pipeline/docs/04_결과요약.md`](voc-pipeline/docs/04_결과요약.md)

## 실행 / Run

Python 3.12, 표준 라이브러리 + numpy, scipy(VOC 군집만). LLM 호출은 LM Studio의 OpenAI 호환 서버 `http://localhost:1234/v1`.

```bash
export PYTHONIOENCODING=utf-8
# LLM 없이 바로 되는 것 / no LLM needed
cd l10n-pipeline && python scripts/test_checker.py && python scripts/plant_errors.py && python scripts/compare.py
cd ../voc-pipeline && VOC_GOLD=syn_voc_c_gold.csv python scripts/score.py gemma_c_cap2 gptoss_c_cap2
# LLM 측정 / with LM Studio running
python scripts/classify.py google/gemma-4-12b-qat mytag
```

각 폴더의 README와 스크립트 docstring에 사용법이 있습니다. / See each folder's README and script docstrings.

## 운영 안전장치 / Failure handling

- 형식이 깨진 응답은 같은 요청으로 1회 재시도, 그래도 실패하면 `needs_review=1`로 사람에게 넘김(`voc-pipeline/scripts/classify.py`). / Malformed output is retried once, then flagged for human review.
- 원응답과 종료 사유(`finish_reason`)를 저장해 빈 출력의 원인(추론에 토큰 소진)을 확인함(`l10n-pipeline/scripts/measure.py`). / Raw responses and finish reasons are saved.
- 긴 측정은 끝난 단계를 건너뛰고 다시 시작하도록 작성(`voc-pipeline/scripts/run_setc_measure.sh`, 재부팅으로 끊긴 뒤 같은 명령으로 이어감). / Long runs skip finished steps, so a rerun resumes after a crash.
- 검수기 회귀 테스트: `l10n-pipeline/scripts/test_checker.py`. / Checker regression tests.

## 한계 / Limitations

- VOC 데이터는 전부 합성(LLM 생성)이다. 실제 유저 글은 쓰지 않았다. / All VOC data is synthetic.
- l10n의 정답 용어는 실제 공식 표기(PokéAPI, 사람이 검수한 몬헌 288개)지만 문장 틀은 직접 만든 것이다. 일본어는 사람이 검증하지 않았다. / Terms are real official names; sentence templates are hand-made. Japanese was not human-verified.
- 검수기 규칙과 심은 오류를 같은 쪽에서 설계했으므로 검출률은 설계 범위 안의 값이다. / Checker rules and planted errors were designed together.
- 상용 API와의 비용·품질 비교는 아직 하지 않았다. 시드 1개, 표본이 작아 소수점 차이는 의미 없다. / No commercial-API comparison yet; single seed, small samples.

## 데이터와 권리 / Data and rights

- 게임 이름과 용어는 각 권리자의 것이며, 이 저장소는 개인 학습용 비공식 실험입니다. 이미지·로고는 없습니다. / Game names and terms belong to their owners. Unofficial personal study; no images or logos.
- 용어 출처: [PokéAPI](https://pokeapi.co/), mhw.poedb.tw(몬헌, 사람이 검수한 288행만 포함). 받는 스크립트는 `fetch_*.py`. / Term sources as listed; fetch scripts included.
- 서비스 이름은 가상(`{SERVICE}`)이고 공지·유저 글은 모두 지어낸 것입니다. / The service and all notices and posts are fictional.

## 만든 방식 / How it was built

코드는 Claude Code와 함께 작성했습니다. 분류 기준, 정답 라벨, 측정 전 예측, 결과 해석은 직접 정하고 확정했습니다.
Code was written with Claude Code. Classification criteria, gold labels, pre-measurement predictions and interpretation were decided by me.
