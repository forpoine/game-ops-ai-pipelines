#!/bin/bash
# Set C 분류 측정 대기열(2026-11-18, 사용자 부재 중 실행). 합성 데이터.
# Set C 글 확인·재생성이 끝난 뒤 실행. 정답 확정 전이므로 채점·결과 공개는 사용자가 정답을 확정한 뒤에 한다(정답이 모델 예측에 끌리지 않게).
# Gemma는 늘린 설정(컨텍스트 16384, max_tokens 12000). 이어서 Set A·B 형식 실패 행 재시도 실험. 그다음 gpt-oss(기본 설정 4000).
# 재실행 시 이미 80행이 다 찬 pred 파일과 retry_fail.csv가 있는 단계는 건너뛴다(2026-11-18 재부팅으로 중단된 뒤 추가).
# 두 LLM 동시 로드 금지. 사용: nohup bash scripts/run_setc_measure.sh > data/setc_measure_run.log 2>&1 < /dev/null &   (끝나면 data/setc_measure.done)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
rm -f data/setc_measure.done
lms unload --all
lms load google/gemma-4-12b-qat -c 16384 -y
lms ps
full() { [ -f "data/pred_$1.csv" ] && [ "$(wc -l < data/pred_$1.csv)" -ge 81 ]; }
for p in cap cap2; do
  full gemma_c_$p && continue
  VOC_PROMPT=$p VOC_MAX_TOKENS=12000 VOC_GOLD=syn_voc_c_gold.csv python scripts/classify.py google/gemma-4-12b-qat gemma_c_$p > data/classify_gemma_c_$p.log 2>&1
done
[ -f data/retry_fail.csv ] || VOC_MAX_TOKENS=12000 python scripts/retry_fail.py google/gemma-4-12b-qat gemma_cap2_long gemma_b_cap2_long > data/retry_fail.log 2>&1
lms unload --all
lms load openai/gpt-oss-20b -y
lms ps
for p in cap cap2; do
  full gptoss_c_$p && continue
  VOC_PROMPT=$p VOC_GOLD=syn_voc_c_gold.csv python scripts/classify.py openai/gpt-oss-20b gptoss_c_$p > data/classify_gptoss_c_$p.log 2>&1
done
lms unload --all
touch data/setc_measure.done
echo done
