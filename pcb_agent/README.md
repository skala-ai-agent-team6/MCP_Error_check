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

## 예시 결과 사진
- `results/test_before/`: 원본 시험 사진 10장
- `results/test_after/`: `compare.py`로 결함 박스를 그린 10장, 채점은 `results/채점표.md`
- `results/mcp_after/`: MCP 도구(`analyze_pcb_image`)로 돌린 5장

## MCP 도구 + LangGraph
- `mcp_server.py`: 진단 모델을 MCP 도구로 노출 (stdio)
  - `analyze_pcb_image(image_path, conf=0.25)`: 결함 목록·개수·박스 사진 경로
  - `list_sample_images()`: 시험용 사진 경로
- `graph.py`: LangGraph `inspect(MCP 호출) → 불량/정상 갈림길 → 보고`
```bash
uv pip install ultralytics "mcp<2" langgraph langchain-mcp-adapters
.venv/bin/python graph.py                 # 샘플 3장
.venv/bin/python graph.py 사진경로.jpg     # 원하는 사진
```
- Claude Code에 등록: `claude mcp add pcb-detector --scope user -- $PWD/.venv/bin/python $PWD/mcp_server.py`
- `mcp<2` 고정: langchain-mcp-adapters 0.3.1이 mcp 2.x와 아직 안 맞음

## GPT 에이전트 버전 (`gpt_agent.py`)
GPT(gpt-4o-mini)가 MCP 도구 설명을 보고 **스스로 골라서** 호출 → 결과 해석해 보고.
LangGraph: `agent(GPT) ⇄ tools(MCP)` 반복, 도구 안 부르면 끝.
```bash
uv pip install langchain-openai python-dotenv
.venv/bin/python gpt_agent.py "results/test_before/l_light_05_missing_hole_01_4_600.jpg 진단해줘"
```
키: 저장소 바깥 상위 폴더 `.env`의 `OPENAI_API_KEY` (커밋 금지)
