import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

os.environ["YOLO_VERBOSE"] = "False"
# YOLO 잡담 끄기: stdio MCP는 표준출력이 대화 통로라 잡담이 섞이면 통신이 깨짐

from mcp.server.fastmcp import FastMCP
from ultralytics import YOLO

BASE = Path(__file__).parent
MODEL = YOLO(str(BASE / "weights/best.pt"))
# 진단 모델은 서버 켤 때 한 번만 로드 (매번 부르면 느림)
OUT_DIR = BASE / "results/mcp_after"

mcp = FastMCP("pcb-detector")


@mcp.tool()
def list_sample_images() -> dict:
    """시험용 PCB 사진 경로 목록을 돌려준다."""
    folders = [BASE / "results/test_before", BASE / "test_samples"]
    return {"images": [str(p) for f in folders for p in sorted(f.glob("*.jpg"))]}


@mcp.tool()
def analyze_pcb_image(image_path: str, conf: float = 0.25) -> dict:
    """PCB 사진 한 장에서 결함(mouse_bite, spur, missing_hole, short, open_circuit, spurious_copper)을 찾는다.

    image_path: 사진 절대경로. conf: 이 확신도 미만 탐지는 버림(0~1).
    결함 목록, 결함 종류별 개수, 박스 그린 사진 경로를 돌려준다.
    """
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"error": f"사진이 없어요: {path}"}

    with redirect_stdout(sys.stderr):
        # 혹시 남은 출력도 표준에러로 돌려 통신선 보호
        r = MODEL.predict(str(path), conf=conf, verbose=False)[0]

    defects = [
        {
            "type": MODEL.names[int(c)],
            "confidence": round(float(s), 3),
            "box_xyxy": [round(v) for v in b.tolist()],
        }
        for c, s, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy)
    ]
    counts = {}
    for d in defects:
        counts[d["type"]] = counts.get(d["type"], 0) + 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    annotated = OUT_DIR / path.name
    r.save(filename=str(annotated))
    # 박스 그린 사진 저장 (사람이 눈으로 확인용)

    return {
        "image": str(path),
        "is_defective": bool(defects),
        "defect_counts": counts,
        "defects": defects,
        "annotated_image": str(annotated),
    }


if __name__ == "__main__":
    mcp.run()
    # 기본은 stdio: 부르는 쪽(Claude Code, LangGraph)이 이 파일을 직접 실행해서 대화
