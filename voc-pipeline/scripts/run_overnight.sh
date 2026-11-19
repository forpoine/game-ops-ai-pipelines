#!/bin/bash
# cap2 재측정(run_cap2.sh)이 끝난 뒤 이어지는 야간 후속 작업. 사용자 답변 없이 돌릴 수 있는 것만. 합성 데이터.
# 순서(두 LLM 동시 로드 금지): [gpt-oss 로드 상태] 반복 측정 -> [Gemma 로드] 형식 실패 원인 확인, 요약 초안, Gemma 반복 측정 -> 보고서.
# 사용: nohup bash scripts/run_overnight.sh > data/overnight_run.log 2>&1 < /dev/null &   (끝나면 data/overnight.done, 보고서 data/overnight_report.txt)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
rm -f data/overnight.done data/overnight_report.txt
while [ ! -f data/cap2_v3.done ]; do sleep 30; done
A=syn_voc_gold_v3.csv; B=syn_voc_b_gold_v3.csv
run() { VOC_PROMPT=cap2 VOC_GOLD=$3 python scripts/classify.py "$1" "$2" > "data/classify_$2.log" 2>&1; }
# 1) gpt-oss가 로드된 상태: 같은 조건 반복(실행 간 흔들림)
run openai/gpt-oss-20b gptoss_cap2_r2 $A
run openai/gpt-oss-20b gptoss_b_cap2_r2 $B
# 2) Gemma로 교체
lms unload --all
lms load google/gemma-4-12b-qat -y
python scripts/probe_fail.py google/gemma-4-12b-qat gemma_cap2 gemma_b_cap2 > data/probe_fail.log 2>&1
python scripts/summarize.py > data/summarize.log 2>&1
run google/gemma-4-12b-qat gemma_b_cap2_r2 $B
# 3) 보고서(규칙 기반 계산, LM Studio 불필요)
{
  echo "# cap2 재측정과 야간 후속 보고서 (합성 데이터, 정답 v3 기준)"
  echo; echo "## 1. cap2 심각도 정확도(옛 프롬프트 cap의 v3 재채점과 비교)"
  echo "-- Set A cap (옛 프롬프트)"; VOC_GOLD=$A python scripts/score.py gemma_cap gptoss_cap | grep -E "^==|전체"
  echo "-- Set A cap2"; VOC_GOLD=$A python scripts/score.py gemma_cap2 gptoss_cap2 | grep -E "^==|전체|오답"
  echo "-- Set B cap (옛 프롬프트)"; VOC_GOLD=$B python scripts/score.py gemma_b_cap gptoss_b_cap | grep -E "^==|전체"
  echo "-- Set B cap2"; VOC_GOLD=$B python scripts/score.py gemma_b_cap2 gptoss_b_cap2 | grep -E "^==|전체|오답"
  echo; echo "## 2. 실행 간 흔들림(같은 조건 두 번)"
  echo "-- Set A gpt-oss"; python scripts/compare_runs.py $A gptoss_cap2 gptoss_cap2_r2
  echo "-- Set B gpt-oss"; python scripts/compare_runs.py $B gptoss_b_cap2 gptoss_b_cap2_r2
  echo "-- Set B Gemma"; python scripts/compare_runs.py $B gemma_b_cap2 gemma_b_cap2_r2
  echo; echo "## 3. 키워드 상향 규칙(cap2 예측 위)"
  python scripts/keyword_rule.py $A gemma_cap2 gptoss_cap2; python scripts/keyword_rule.py $B gemma_b_cap2 gptoss_b_cap2
  echo; echo "## 4. Gemma 형식 실패 원인(probe_fail)"; cat data/probe_fail.log | tail -40
  echo; echo "## 5. 요약 초안 규칙 확인(summarize)"; cat data/summarize.log | tail -20
} > data/overnight_report.txt 2>&1
touch data/overnight.done
echo done
