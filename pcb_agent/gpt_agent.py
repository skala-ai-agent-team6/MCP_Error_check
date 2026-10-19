import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

BASE = Path(__file__).parent
load_dotenv(BASE.parent.parent / ".env", override=True)
# 키는 16주차 폴더 .env의 OPENAI_API_KEY. override: ~/.zshrc에 있는 옛 키보다 .env 키를 우선

CLIENT = MultiServerMCPClient(
    {
        "pcb": {
            "command": sys.executable,
            "args": [str(BASE / "mcp_server.py")],
            "transport": "stdio",
        }
    }
)

SYSTEM = (
    "너는 로봇청소기 수리 진단 에이전트다. PCB 사진이 주어지면 analyze_pcb_image 도구로 진단하고, "
    "결함 종류·개수·확신도를 근거로 한국어로 짧게 보고해라. 확신도 0.5 미만은 '재확인 필요'로 표시해라."
)


async def build_graph():
    tools = await CLIENT.get_tools()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)
    # GPT에게 MCP 도구 설명서를 쥐여 줌 → 필요하면 GPT가 스스로 도구 호출

    async def agent(state: MessagesState) -> dict:
        return {"messages": [await llm.ainvoke([("system", SYSTEM), *state["messages"]])]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    # 갈림길: GPT가 도구를 부르면 tools로, 아니면 끝
    builder.add_edge("tools", "agent")
    # 도구 결과를 들고 다시 GPT에게 → 해석해서 답
    return builder.compile()


async def main():
    question = " ".join(sys.argv[1:]) or "시험용 사진 목록에서 앞의 2장을 진단해줘"
    graph = await build_graph()
    out = await graph.ainvoke({"messages": [("user", question)]})
    for m in out["messages"]:
        for call in getattr(m, "tool_calls", []) or []:
            print(f"[도구 호출] {call['name']} {call['args']}")
    print("\n" + out["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
    # 사용법: python gpt_agent.py "results/test_before/... 사진 진단해줘"
