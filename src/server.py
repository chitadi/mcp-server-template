#!/usr/bin/env python3
import os, sqlite3, tempfile, requests
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# ✅ One MCP instance only
mcp = FastMCP("News MCP Server")

@mcp.tool(description="Greet a user by name")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our MCP server on Render!"

@mcp.tool(description="Get information about the MCP server")
def get_server_info() -> dict:
    return {
        "server_name": "News MCP Server",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }

DB_URL = os.getenv(
    "DB_URL",
    "https://raw.githubusercontent.com/chitadi/news-agent-poke-mcp/data/newsletter.db"
)

def open_latest_db() -> sqlite3.Connection:
    resp = requests.get(DB_URL, timeout=20)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.write(resp.content)
    tmp.flush()
    return sqlite3.connect(tmp.name)

# --- Categories ---
VALID_CATEGORIES = {"tech", "startups", "business", "politics", "finance", "miscellaneous"}

@mcp.tool(description="Return recent articles from the last `hours`, optionally filtered by one or more categories.")
def latest_articles(
    categories: List[str],
    hours: int = 24,
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    conn = open_latest_db()
    cur = conn.cursor()

    query = """
        SELECT title, url, source_name, category, published_at
        FROM articles
        WHERE published_at >= datetime('now', ?)
    """
    params = [f'-{hours} hours']

    # ✅ Default to all categories if none provided
    if not categories:
        categories = list(VALID_CATEGORIES)

    valid = [c.lower() for c in categories if c.lower() in VALID_CATEGORIES]
    if valid:
        placeholders = ",".join("?" for _ in valid)
        query += f" AND category IN ({placeholders})"
        params.extend(valid)

    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return [
        {"title": r[0], "url": r[1], "source": r[2], "category": r[3], "published_at": r[4]}
        for r in rows
    ]

@mcp.tool(description="Return the most recent YouTube videos in the last `hours`, optionally filtered by channel.")
def latest_videos(
    hours: int = 24,
    limit: int = 50,
    channel: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Example: latest_videos(hours=24, limit=20, channel='Bloomberg')
    Returns YouTube videos stored in the DB, filtered by recency and optionally channel.
    """
    conn = open_latest_db()
    cur = conn.cursor()

    query = """
        SELECT title, url, channel_name, published_at
        FROM videos
        WHERE published_at >= datetime('now', ?)
    """
    params = [f'-{hours} hours']

    if channel:
        query += " AND channel_name = ?"
        params.append(channel)

    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return [
        {"title": r[0], "url": r[1], "channel": r[2], "published_at": r[3]}
        for r in rows
    ]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f"Starting FastMCP server on {host}:{port}")

    try:
        mcp.run(
            transport="http",
            host=host,
            port=port,
            stateless_http=True,
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
