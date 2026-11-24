#!/bin/sh
# 상용 API 측정(2026-11-24): 몬헌 n=100, 몬헌 틀·공지체 틀 x baseline·protected. Claude와 Gemini는 동시에 돈다.
# 시험 실행(5문장) 결과는 results/smoke_api/.
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")/.."
run4() { # $1 provider, $2 model, $3 log 접두
  for tpl in basic notice; do
    for mode in baseline protected; do
      python scripts/measure_api.py "$1" "$2" --mode $mode --glossary mhw --n 100 --tpl $tpl > results/log_api_$3_${tpl}_$mode.txt 2>&1
    done
  done
}
run4 claude claude-haiku-5-5 haiku &
L10N_API_SLEEP=4 run4 gemini gemini-3.5-flash-lite gemini &
wait
touch results/api.done
