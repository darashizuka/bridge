"""
FillNode — Step 4 ⭐ The MCP Node
For each gap, uses the MCP web search tool (via langchain-mcp-adapters)
to fetch real explanations from the web, then uses the LLM to
synthesize a clean beginner-friendly explanation + flashcard.
"""
import os
import sys
import json
import asyncio
import threading
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from state import GapFinderState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

# Path to our custom MCP server
MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server.py")

MCP_CONFIG = {
    "search": {
        "command": sys.executable,   # Use current Python interpreter
        "args": [MCP_SERVER_PATH],
        "transport": "stdio"
    }
}


async def _search_and_fill(gap: dict, search_tool) -> dict:
    """Search the web for a concept and generate a clean explanation."""
    concept = gap["concept"]
    context = gap.get("context", "")

    search_results = ""
    sources = []

    if search_tool:
        try:
            query = f"explain {concept} simply with example"
            result = await search_tool.ainvoke({"query": query})
            search_results = str(result)

            # Extract URLs from results
            for line in search_results.split("\n"):
                if line.startswith("URL:"):
                    sources.append(line.replace("URL:", "").strip())
        except Exception as e:
            search_results = f"Search unavailable: {str(e)}"

    # Use LLM to synthesize explanation from search results
    prompt = f"""You are explaining a concept to a student who is taking a course.

The concept "{concept}" appeared in their lecture notes with this context:
"{context}"

Here is relevant web search information:
{search_results[:2000]}

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
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
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
            "flashcard_a": f"A concept related to {context[:100]}"
        }

    return {
        **gap,
        "explanation": data.get("explanation", "") + "\n\n**Example:** " + data.get("example", ""),
        "flashcard_q": data.get("flashcard_q", f"What is {concept}?"),
        "flashcard_a": data.get("flashcard_a", ""),
        "sources": sources[:3]
    }


async def _fill_all_gaps(gaps: list) -> list:
    """Run web search + fill for all gaps using MCP client."""
    client = MultiServerMCPClient(MCP_CONFIG)
    try:
        tools = await client.get_tools()
        search_tool = next((t for t in tools if t.name == "web_search"), None)
    except Exception as e:
        search_tool = None

    tasks = [_search_and_fill(gap, search_tool) for gap in gaps]
    filled = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions from individual tasks
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
    """Run an async coroutine in a dedicated thread with its own event loop.
    This avoids conflicts with existing event loops (e.g. in Gradio on Windows)."""
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
    """LangGraph node: fill gaps using MCP web search."""
    gaps = state.get("prioritized_gaps", [])

    if not gaps:
        return {"filled_gaps": [], "status": "⚠️ No gaps to fill"}

    # Limit to top 10 gaps to keep it fast for demo
    gaps_to_fill = gaps[:10]

    filled = _run_async_in_thread(_fill_all_gaps(gaps_to_fill))

    return {
        "filled_gaps": filled,
        "status": f"🌐 Filled {len(filled)} gaps via MCP web search",
        "messages": [AIMessage(content=f"Fetched explanations for {len(filled)} concepts")]
    }
