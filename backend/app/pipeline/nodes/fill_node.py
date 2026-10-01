import os
import sys
import json
import asyncio
import logging
import threading
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState
from app.config import get_settings

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=get_settings().groq_api_key,
    temperature=0.3,
)

MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server.py")

MCP_CONFIG = {
    "search": {
        "command": sys.executable,
        "args": [MCP_SERVER_PATH],
        "transport": "stdio",
    }
}

_fill_semaphore = asyncio.Semaphore(3)


async def _search_and_fill(gap: dict, search_tool) -> dict:
    concept = gap["concept"]
    context = gap.get("context", "")

    search_results = ""
    sources = []

    if search_tool:
        try:
            query = f"explain {concept} simply with example"
            result = await search_tool.ainvoke({"query": query})
            search_results = str(result)

            for line in search_results.split("\n"):
                if line.startswith("URL:"):
                    sources.append(line.replace("URL:", "").strip())
        except Exception as e:
            search_results = f"Search unavailable: {str(e)}"

    prompt = f"""You are explaining a concept to a student who is taking a course.

The concept "{concept}" appeared in their lecture notes with this context:
"{context}"

{f"Here is relevant web search information:{chr(10)}{search_results[:2000]}" if search_results else ""}

Write:
1. A clear, beginner-friendly explanation (3-5 sentences)
2. One concrete real-world example
3. A flashcard question
4. The flashcard answer (1-2 sentences)

Return ONLY this JSON:
{{
  "explanation": "...",
  "example": "...",
  "flashcard_q": "What is {concept}?",
  "flashcard_a": "..."
}}
"""
    async with _fill_semaphore:
        try:
            response = await asyncio.to_thread(llm.invoke, [HumanMessage(content=prompt)])
            content = response.content.strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content.strip())
        except Exception:
            data = {
                "explanation": f"{concept} is a key concept in this domain.",
                "example": "See course materials for examples.",
                "flashcard_q": f"What is {concept}?",
                "flashcard_a": f"A concept related to {context[:100]}",
            }

    return {
        **gap,
        "explanation": data.get("explanation", "") + "\n\nExample: " + data.get("example", ""),
        "flashcard_q": data.get("flashcard_q", f"What is {concept}?"),
        "flashcard_a": data.get("flashcard_a", ""),
        "sources": sources[:3],
    }


async def _fill_all_gaps(gaps: list) -> list:
    search_tool = None
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.sessions import StdioConnection
        client = MultiServerMCPClient({
            "search": StdioConnection(
                transport="stdio",
                command=sys.executable,
                args=[MCP_SERVER_PATH],
            )
        })
        tools = await client.get_tools()
        search_tool = next((t for t in tools if t.name == "web_search"), None)
        logger.info("MCP search tool connected")
    except Exception as e:
        logger.warning(f"MCP search unavailable, using LLM only: {e}")
        search_tool = None

    tasks = [_search_and_fill(gap, search_tool) for gap in gaps]
    filled = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for i, result in enumerate(filled):
        if isinstance(result, Exception):
            gap = dict(gaps[i])
            gap["explanation"] = f"Could not fetch explanation: {str(result)}"
            gap["flashcard_q"] = f"What is {gaps[i]['concept']}?"
            gap["flashcard_a"] = ""
            gap["sources"] = []
            results.append(gap)
        else:
            results.append(result)

    return results


def _run_async_in_thread(coro):
    result = [None]
    exception = [None]

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as e:
            exception[0] = e
        finally:
            loop.close()

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()

    if exception[0]:
        raise exception[0]
    return result[0]


def fill_node(state: GapFinderState) -> dict:
    gaps = state.get("prioritized_gaps", [])

    if not gaps:
        return {"filled_gaps": [], "status": "No gaps to fill"}

    settings = get_settings()
    max_gaps = settings.max_gaps_to_fill
    gaps_to_fill = gaps[:max_gaps]

    filled = _run_async_in_thread(_fill_all_gaps(gaps_to_fill))

    total = len(gaps)
    filled_count = len(filled)
    msg = f"Filled {filled_count} gaps"
    if total > filled_count:
        msg += f" ({total - filled_count} lower-priority gaps skipped)"

    return {
        "filled_gaps": filled,
        "status": msg,
        "messages": [AIMessage(content=msg)],
    }
