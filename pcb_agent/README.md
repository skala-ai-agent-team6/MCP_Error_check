# PCB_AGENT_DEMO

PCB 결함 검출 모델(YOLO11n)을 사진에 돌려 보고 정답과 비교하는 데모.
나중에 MCP 도구(`analyze_pcb_image`)로 감싸 오케스트레이터가 부르게 할 예정.

## 모델
- `weights/best.pt`: YOLO11n을 PCB 결함 데이터셋(6종)으로 파인튜닝
- 학습 코드: 팀 PCB 프로젝트(RohEunSeo/PCB) 기반, 2026-10-06 로컬에서 **2 epoch만** 학습 (mAP50 0.40)
- 10장 시험 결과 3장 정답 (missing_hole은 잘 맞히고 short/spur/spurious_copper는 약함) → 추가 학습 필요

## 실행
```bash
uv venv --python 3.11 && uv pip install ultralytics
.venv/bin/python compare.py   # results/test_before 10장 → results/test_after + 채점표.md
```
정답 비교용 라벨 경로는 `compare.py`의 `LABELS`.
