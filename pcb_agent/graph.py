import asyncio
import json
import sys
from pathlib import Path
from typing import TypedDict

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, StateGraph

BASE = Path(__file__).parent
CLIENT = MultiServerMCPClient(
    {
        "pcb": {
            "command": sys.executable,
            "args": [str(BASE / "mcp_server.py")],
            "transport": "stdio",
        }
    }
)
# MCP 서버 연결 정보: Claude Code에 등록한 것과 같은 서버를 LangGraph도 부름


class State(TypedDict):
    image_path: str
    result: dict
    report: str


async def call_tool(name: str, args: dict):
    tools = {t.name: t for t in await CLIENT.get_tools()}
    out = await tools[name].ainvoke(args)
    # 어댑터는 MCP 응답을 텍스트 블록 목록으로 돌려줌 → JSON 풀기
    if isinstance(out, list):
        out = out[0]["text"] if isinstance(out[0], dict) else out[0]
    return json.loads(out) if isinstance(out, str) else out


async def inspect(state: State) -> dict:
    return {"result": await call_tool("analyze_pcb_image", {"image_path": state["image_path"]})}
    # 1번 노드: MCP 도구로 진단 모델 호출


def route(state: State) -> str:
    return "defect_report" if state["result"].get("is_defective") else "ok_report"
    # 갈림길: 불량이면 불량 보고, 아니면 정상 보고


def defect_report(state: State) -> dict:
    r = state["result"]
    counts = ", ".join(f"{k} {v}개" for k, v in r["defect_counts"].items())
    return {"report": f"[불량] {Path(r['image']).name}: {counts}\n  → PCB 보드 담당 확인 필요\n  박스 사진: {r['annotated_image']}"}


def ok_report(state: State) -> dict:
    r = state["result"]
    if "error" in r:
        return {"report": f"[확인불가] {r['error']}"}
    return {"report": f"[정상] {Path(state['image_path']).name}: 결함 없음"}


builder = StateGraph(State)
builder.add_node("inspect", inspect)
builder.add_node("defect_report", defect_report)
builder.add_node("ok_report", ok_report)
builder.add_edge(START, "inspect")
builder.add_conditional_edges("inspect", route, ["defect_report", "ok_report"])
builder.add_edge("defect_report", END)
builder.add_edge("ok_report", END)
graph = builder.compile()


async def main():
    images = sys.argv[1:] or (await call_tool("list_sample_images", {}))["images"]
    for img in images[:3] if not sys.argv[1:] else images:
        out = await graph.ainvoke({"image_path": img})
        print(out["report"])


if __name__ == "__main__":
    asyncio.run(main())
    # 사용법: python graph.py [사진경로 ...]  (안 주면 샘플 3장)
