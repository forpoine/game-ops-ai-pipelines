# voc-pipeline

합성 유저 의견(한·영 혼합) → LLM 분류(카테고리·심각도·감성) → 임베딩 군집 → 급증 감지 → 담당 조직용 요약 → 사람 검수. 데이터는 전부 합성입니다.

Synthetic player feedback (Korean and English) → LLM classification → embedding clusters → spike detection → summaries for the owning team → human review. All data is synthetic.

## 폴더 / Layout
- `docs/01_분류기준.md` 카테고리·심각도·감성 기준과 경계 규칙 / classification criteria
- `docs/03_사고대응시나리오.md` 공지 오기 → 급증 감지 → 정정 → 재발 방지 한 장 / incident walkthrough
- `docs/04_결과요약.md` 측정 결과와 한계 / results and limitations
- `data/syn_voc*_gold*.csv` 합성 의견과 정답(`label_status=confirmed`만 사람이 확정) / synthetic posts and labels
- `data/pred_<model>_<set>_<prompt>.csv` 모델 예측 / predictions
- `scripts/` 생성, 분류, 채점, 임베딩, 군집, 감지, 요약 / generation, classification, scoring, embedding, clustering, detection, summaries

## 실행 / Run
```bash
export PYTHONIOENCODING=utf-8
# 채점만(LLM 없음) / score saved predictions
VOC_GOLD=syn_voc_gold_v3.csv python scripts/score.py gemma_cap2 gptoss_cap2
# 분류(LM Studio 필요) / classify
VOC_PROMPT=cap2 python scripts/classify.py google/gemma-4-12b-qat mytag
# 임베딩 → 군집 → 급증 감지 / embed, cluster, detect
VOC_EMB=m3 python scripts/embed.py a && python scripts/cluster.py sweep a && python scripts/detect.py oracle a
```
환경 변수: `VOC_SET=b|c`, `VOC_GOLD=<파일>`, `VOC_PROMPT=cap|cap2`, `VOC_RETRY=0|1`, `VOC_MAX_TOKENS`. Qwen3는 프롬프트 끝에 `/no_think`.
