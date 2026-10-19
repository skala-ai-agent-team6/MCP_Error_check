from pathlib import Path
from ultralytics import YOLO

HOME = Path.home() / "Downloads/Raphael_work"
MODEL = Path("weights/best.pt")
LABELS = HOME / "PCB/dataset/raw/pcb-defect-dataset/test/labels"
BEFORE = Path("results/test_before")
# 시험지(원본 사진) 폴더

model = YOLO(str(MODEL))
results = model.predict(source=str(BEFORE), save=True, project=str(Path("results").resolve()), name="test_after", exist_ok=True, verbose=False)
# 채점: 사진마다 박스 그려서 test_after에 저장

lines = ["파일 | 정답 | 모델 예측 | 결과", "---|---|---|---"]
for r in results:
    img = Path(r.path)
    label_file = LABELS / (img.stem + ".txt")
    answer = sorted(model.names[int(l.split()[0])] for l in label_file.read_text().split("\n") if l.strip())
    # 답안지(라벨 파일)에서 정답 결함 목록 읽기
    pred = sorted(model.names[int(c)] for c in r.boxes.cls)
    ok = "O" if answer == pred else "X"
    lines.append(f"{img.name} | {', '.join(answer)} | {', '.join(pred) or '(없음)'} | {ok}")

summary = "\n".join(lines)
Path("results/채점표.md").write_text(summary + "\n")
print(summary)
