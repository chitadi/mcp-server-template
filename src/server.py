#!/usr/bin/env python3
import os
from fastmcp import FastMCP

mcp = FastMCP("Sample MCP Server")

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our sample MCP server running on Heroku!"

@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    return {
        "server_name": "Sample MCP Server",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )


# src/server.py
import os, sqlite3, tempfile, requests
from typing import List, Dict, Any

# ⬇️ Add these imports beside the template's existing imports
from mcp import mcp  # this exists in the template

# You can also wire this via environment variable on Render later
DB_URL = os.getenv(
    "DB_URL",
    "https://raw.githubusercontent.com/chitadi/news-agent-poke-mcp/data/newsletter.db"
)

def _open_latest_db() -> sqlite3.Connection:
    """Download the latest SQLite DB from GitHub raw and open a temp sqlite connection."""
    resp = requests.get(DB_URL, timeout=20)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.write(resp.content)
    tmp.flush()
    return sqlite3.connect(tmp.name)

@mcp.tool(description="Return the most recent articles in the last `hours`.")
def latest(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    conn = _open_latest_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, url, source_name, published_at
        FROM articles
        WHERE published_at >= datetime('now', ?)
        ORDER BY published_at DESC
        LIMIT ?
    """, (f'-{hours} hours', limit))
    rows = cur.fetchall()
    conn.close()
    return [
        {"title": r[0], "url": r[1], "source": r[2], "published_at": r[3]}
        for r in rows
    ]

@mcp.tool(description="Keyword search over titles/urls within the last `hours`.")
def search(q: str, hours: int = 48, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Example: q='startup' or q='fintech'
    """
    conn = _open_latest_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, url, source_name, published_at
        FROM articles
        WHERE published_at >= datetime('now', ?)
          AND (title LIKE ? OR url LIKE ?)
        ORDER BY published_at DESC
        LIMIT ?
    """, (f'-{hours} hours', f'%{q}%', f'%{q}%', limit))
    rows = cur.fetchall()
    conn.close()
    return [
        {"title": r[0], "url": r[1], "source": r[2], "published_at": r[3]}
        for r in rows
    ]

@mcp.tool(description="Count of articles per source in the last `hours`.")
def sources(hours: int = 24) -> List[Dict[str, Any]]:
    conn = _open_latest_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT source_name, COUNT(*)
        FROM articles
        WHERE published_at >= datetime('now', ?)
        GROUP BY source_name
        ORDER BY COUNT(*) DESC
    """, (f'-{hours} hours',))
    rows = cur.fetchall()
    conn.close()
    return [{"source": r[0], "count": r[1]} for r in rows]

# use npx.cmd @modelcontextprotocol/inspector on cmd to reach the dashboard and enter the url 
# https://fastmcp-server-zsi6.onrender.com/mcp for the mcp to be connected? then text poke it should work