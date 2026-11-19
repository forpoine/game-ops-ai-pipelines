#!/bin/sh
# 이벤트명·상품명을 보호 용어로 추가한 뒤 공지 5종 재번역(3모델 순서대로, 한 번에 하나만 로드).
export PYTHONIOENCODING=utf-8
LMS="${LMS:-lms}"  # LM Studio CLI (PATH에 없으면 LMS=경로 로 지정)
cd "$(dirname "$0")/.."
run() { $LMS unload --all > /dev/null 2>&1; $LMS load "$1" -y > results/load2_$2.txt 2>&1; python scripts/translate_notices.py --model "$1" > results/log2_$2_notices.txt 2>&1; }
run google/gemma-4-12b-qat gemma
run openai/gpt-oss-20b gptoss
NOTHINK=1 run qwen3-14b qwen
$LMS unload --all > /dev/null 2>&1
touch results/notices2.done
