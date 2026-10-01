import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from duckduckgo_search import DDGS

app = Server("bridge-search")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="Search the web for a clear, beginner-friendly explanation of a concept.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The concept or term to search for"}
                },
                "required": ["query"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "web_search":
        query = arguments.get("query", "")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            formatted = []
            for r in results:
                formatted.append(
                    f"Title: {r.get('title', '')}\n"
                    f"URL: {r.get('href', '')}\n"
                    f"Snippet: {r.get('body', '')}\n"
                )
            output = "\n---\n".join(formatted) if formatted else "No results found."
            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {str(e)}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
