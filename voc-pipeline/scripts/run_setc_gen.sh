#!/bin/bash
# Set C 글 생성 대기열(2026-11-18): Gemma 설정 재측정(run_gemma_long.sh)이 끝나면 Qwen3로 바꿔 80건을 생성하고 1차 정답 파일을 만든다. 합성 데이터.
# 두 LLM 동시 로드 금지: Gemma 언로드 후 Qwen3 로드, 끝나면 언로드.
# 사용: nohup bash scripts/run_setc_gen.sh > data/setc_gen_run.log 2>&1 < /dev/null &   (끝나면 data/setc_gen.done)
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
rm -f data/setc_gen.done
while [ ! -f data/gemma_long.done ]; do sleep 30; done
lms unload --all
lms load qwen3-14b -y
lms ps
python scripts/generate_voc_c.py > data/generate_c.log 2>&1
python scripts/make_gold_c.py >> data/generate_c.log 2>&1
touch data/setc_gen.done
echo done
