# mechanical-mcp

기계 부품(모터 하우징, 축, 기어) 사진의 금속 표면 결함을 찾는 MCP 서버. FastMCP 4.1, Streamable HTTP.

## 도구
| 도구 | 입력 | 출력 |
|---|---|---|
| list_photos | 없음 | photo_ids |
| detect_surface_defects | photo_id, conf(기본 0.25) | is_defective, max_confidence, defect_counts, defects(type·confidence·box_xyxy), annotated_image, model |
| detect_dents | photo_id, conf(기본 0.25) | 위와 같은 모양. 결함 종류는 dent(찌그러짐), breakage(파손) |

- 결함 6종: crazing, inclusion, patches, pitted_surface, rolled-in_scale, scratches
- 없는 photo_id는 ToolError로 돌려주고, 있는 photo_id 목록을 메시지에 넣는다.
- photo_id 자리에 파일 경로를 넣어도 된다 (같은 PC의 에이전트 워커가 쓴다).
- 모든 도구 readOnlyHint.
- detect_dents는 자동차 외판 모델(`vineetsarpal/yolov11n-car-damage`)이다. 원래 이름(front-bumper-dent 등)을 그대로 내보내면
  GPT가 "자동차 얘기라 무시"해서 서버에서 dent / breakage로 바꿔 내보낸다. 교체는 환경변수 DENT_REPO, DENT_FILE.

## 실행
```bash
uv sync
uv run python server.py          # http://127.0.0.1:9104/mcp
uv run python test_client.py     # 다른 터미널에서. 전체 사진 시험
```

## 설정 (환경변수)
| 이름 | 기본값 | 뜻 |
|---|---|---|
| MODEL_REPO | hazemaaa/steel-defect-yolo11n | Hugging Face 모델 |
| MODEL_FILE | production/best.pt | 가중치 파일 |
| PHOTO_DIR | ./photos | photo_id = 이 폴더의 파일 이름(확장자 제외) |
| OUT_DIR | ./results | 박스 그린 사진 저장 위치 |
| HOST, PORT | 127.0.0.1, 9104 | 서버 주소 |

## 한계 (2026-10-20 시험)
- NEU 강판 사진 7장은 모두 맞혔다. 일반 사진 9장(녹, 긁힘, 모터 하우징)은 대부분 틀리거나 놓쳤다.
- 학습 데이터가 강판 클로즈업이라 배경이 많은 사진은 오탐이 많다. 찌그러짐·휨·균열은 못 찾는다.
- 일단 이 모델로 유지하고, 나중에 MODEL_REPO·MODEL_FILE만 바꿔 교체한다.
- 시험 기록: `시험기록.md`

## 예시 사진 (`photos/`, 30장)
- NEU 강판 결함 7장: 모델이 잘 맞히는 사진
- Wikimedia Commons 부품 사진 23장: 녹슨 기어·볼트·베어링·브레이크 디스크, 긁힌 금속판, 분해한 DC 모터·로터 등
- 출처와 라이선스: `사진출처.md`
- 정상 모터 사진(motor_dc, motor_open)에서도 patches·inclusion을 잡는다. 코일·구리 무늬를 결함으로 보는 오탐이다.
