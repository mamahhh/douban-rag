#!/usr/bin/env python3
"""
MCP Server for Douban RAG System.

Exposes your Douban history data to AI assistants via the Model Context Protocol.

Usage:
    python mcp_server.py

Or add to your MCP client configuration:
    {
        "mcpServers": {
            "douban-rag": {
                "command": "python",
                "args": ["/path/to/mcp_server.py"]
            }
        }
    }
"""

import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Import RAG components
from app.rag.settings import init_settings
from app.rag.ingestion import load_index, get_vector_store
from app.rag.engine import get_chat_engine
from app.core.config import settings

# Initialize the MCP server
server = Server("douban-rag")


@server.list_tools()
async def list_tools():
    """List available tools for the AI assistant."""
    return [
        Tool(
            name="search_douban",
            description="搜索用户的豆瓣历史记录（电影、书籍、音乐、游戏）。可以按媒体类型、评分、年份等筛选。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，可以是标题、标签、评论内容等"
                    },
                    "media_type": {
                        "type": "string",
                        "enum": ["movie", "book", "music", "game", "all"],
                        "description": "媒体类型过滤：movie(电影), book(书籍), music(音乐), game(游戏), all(全部)",
                        "default": "all"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_douban",
            description="用自然语言询问关于用户豆瓣历史的问题。AI会基于用户的电影、书籍、音乐和游戏记录回答。",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用自然语言提问，例如：'我最喜欢什么类型的电影？'、'推荐几本我可能喜欢的书'"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_stats",
            description="获取用户豆瓣历史的统计信息，包括各类型数量、评分分布等。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a tool and return results."""
    try:
        # Initialize settings if needed
        init_settings()
        
        if name == "search_douban":
            return await search_douban(
                query=arguments.get("query", ""),
                media_type=arguments.get("media_type", "all"),
                top_k=arguments.get("top_k", 5)
            )
        
        elif name == "ask_douban":
            return await ask_douban(
                question=arguments.get("question", "")
            )
        
        elif name == "get_stats":
            return await get_stats()
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def search_douban(query: str, media_type: str = "all", top_k: int = 5):
    """Search the Douban history database."""
    try:
        index = load_index()
        
        # Build the retriever with optional metadata filter
        retriever = index.as_retriever(similarity_top_k=top_k)
        
        # Retrieve nodes
        nodes = retriever.retrieve(query)
        
        # Filter by media type if specified
        if media_type != "all":
            nodes = [n for n in nodes if n.metadata.get("media_type") == media_type]
        
        if not nodes:
            return [TextContent(type="text", text="没有找到相关记录。")]
        
        # Format results
        results = []
        for i, node in enumerate(nodes, 1):
            meta = node.metadata
            title = meta.get("title", "未知")
            m_type = meta.get("media_type", "unknown")
            rating = meta.get("rating", 0)
            year = meta.get("year", "")
            
            type_emoji = {"movie": "🎬", "book": "📖", "music": "🎵", "game": "🎮"}.get(m_type, "📌")
            
            result = f"{i}. {type_emoji} **{title}**"
            if rating > 0:
                result += f" (我的评分: {rating}/10)"
            if year:
                result += f" [{year}]"
            
            # Add snippet of content
            text_snippet = node.text[:150] + "..." if len(node.text) > 150 else node.text
            result += f"\n   {text_snippet}"
            
            results.append(result)
        
        output = f"找到 {len(nodes)} 条相关记录：\n\n" + "\n\n".join(results)
        return [TextContent(type="text", text=output)]
    
    except Exception as e:
        if "collection" in str(e).lower() or "not found" in str(e).lower():
            return [TextContent(type="text", text="数据库为空，请先上传豆瓣数据文件。")]
        raise


async def ask_douban(question: str):
    """Ask a natural language question about Douban history."""
    try:
        chat_engine = get_chat_engine()
        response = chat_engine.chat(question)
        return [TextContent(type="text", text=str(response))]
    
    except Exception as e:
        if "collection" in str(e).lower() or "not found" in str(e).lower():
            return [TextContent(type="text", text="数据库为空，请先上传豆瓣数据文件。")]
        raise


async def get_stats():
    """Get statistics about the Douban history."""
    try:
        import chromadb
        
        db = chromadb.PersistentClient(path=settings.PERSIST_DIR)
        
        try:
            collection = db.get_collection("douban_history")
        except:
            return [TextContent(type="text", text="数据库为空，请先上传豆瓣数据文件。")]
        
        # Get all items
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        if not metadatas:
            return [TextContent(type="text", text="数据库为空。")]
        
        # Calculate stats
        total = len(metadatas)
        
        # Count by media type
        type_counts = {}
        rating_sum = 0
        rating_count = 0
        
        for meta in metadatas:
            mt = meta.get("media_type", "unknown")
            type_counts[mt] = type_counts.get(mt, 0) + 1
            
            rating = meta.get("rating", 0)
            if rating > 0:
                rating_sum += rating
                rating_count += 1
        
        avg_rating = rating_sum / rating_count if rating_count > 0 else 0
        
        # Format output
        type_names = {
            "movie": "🎬 电影",
            "book": "📖 书籍",
            "music": "🎵 音乐",
            "game": "🎮 游戏",
            "drama": "🎭 舞台剧",
            "unknown": "❓ 其他"
        }
        
        lines = [
            f"📊 **豆瓣历史统计**",
            f"",
            f"总记录数: **{total}** 条",
            f"平均评分: **{avg_rating:.1f}/10**",
            f"",
            f"**按类型分布:**"
        ]
        
        for mt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            name = type_names.get(mt, mt)
            pct = count / total * 100
            lines.append(f"  - {name}: {count} ({pct:.1f}%)")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"获取统计信息失败: {str(e)}")]


@server.list_resources()
async def list_resources():
    """List available resources."""
    return [
        Resource(
            uri="douban://stats",
            name="Douban History Stats",
            description="用户豆瓣历史的统计概览",
            mimeType="text/plain"
        )
    ]


@server.read_resource()
async def read_resource(uri: str):
    """Read a resource by URI."""
    if uri == "douban://stats":
        result = await get_stats()
        return result[0].text if result else "No data"
    return f"Unknown resource: {uri}"


async def main():
    """Run the MCP server."""
    print("Starting Douban RAG MCP Server...", file=sys.stderr)
    print("This server exposes your Douban history to AI assistants.", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
