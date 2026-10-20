import asyncio
import json
import sys

from fastmcp import Client

URL = "http://127.0.0.1:9104/mcp"


async def main():
    async with Client(URL) as client:
        tools = await client.list_tools()
        print("도구:", [t.name for t in tools])

        ids = (await client.call_tool("list_photos", {})).data["photo_ids"]
        targets = sys.argv[1:] or ids
        for pid in targets:
            r = (await client.call_tool("detect_surface_defects", {"photo_id": pid})).data
            print(f"{pid:28} {r['defect_counts'] or '결함 없음'}  최고 {r['max_confidence']}")

        try:
            await client.call_tool("detect_surface_defects", {"photo_id": "없는사진"})
        except Exception as e:
            print("없는 id 테스트 →", str(e)[:80])


if __name__ == "__main__":
    asyncio.run(main())
    # 사용법: 서버를 켠 뒤 uv run python test_client.py [photo_id ...]
