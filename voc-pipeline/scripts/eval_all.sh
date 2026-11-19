#!/bin/bash
# 프롬프트·모델 교체 전후 회귀 검사를 세 세트(A·B·C)에 한 번에 돌린다. LLM 없음(저장된 예측끼리 비교).
# 사용: bash scripts/eval_all.sh <baseline 접두> <candidate 접두>
#   예: bash scripts/eval_all.sh gemma_cap2 gemma_cap2_new   -> pred_gemma_cap2.csv / pred_gemma_b_cap2.csv / pred_gemma_c_cap2.csv 와 비교
#   candidate 예측 만들기: VOC_PROMPT=... VOC_GOLD=<세트 정답> python scripts/classify.py <모델> <태그>
# 세트 하나라도 FAIL이면 종료 코드 1. 이 프로젝트의 태그 규칙은 <모델>[_b|_c]_<프롬프트>.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
B=$1; C=$2; rc=0
model=${B%%_*}; bp=${B#*_}; cm=${C%%_*}; cp=${C#*_}
for s in "a syn_voc_gold_v3.csv" "b syn_voc_b_gold_v3.csv" "c syn_voc_c_gold.csv"; do
  set -- $s; mid=""; [ "$1" != a ] && mid="_$1"
  bt="${model}${mid}_${bp}"; ct="${cm}${mid}_${cp}"
  if [ ! -f "data/pred_$bt.csv" ] || [ ! -f "data/pred_$ct.csv" ]; then echo "-- set $1: pred_$bt 또는 pred_$ct 없음, 건너뜀"; continue; fi
  python scripts/eval_gate.py "$2" "$bt" "$ct" || rc=1
done
exit $rc
