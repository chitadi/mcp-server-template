#!/usr/bin/env python3
import os, sqlite3, tempfile, requests
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# ✅ One MCP instance only
mcp = FastMCP("News MCP Server")

@mcp.tool(description="Simple greeting function for testing connectivity",
    parameters=[
        {
            "name": "name",
            "type": "string",
            "description": "Name to greet",
            "required": False,
            "default": "World",
            "example": "Poke"
        }
    ],
    returns="""
        "message": "Hello, {name}! Welcome to the News MCP Server."
    """)
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our MCP server on Render!"

@mcp.tool(description="Get information about this MCP server's capabilities and status",
    returns="""
    {
        "server_name": "News MCP Server",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }
    """)
def get_server_info() -> dict:
    """
    Returns metadata about this MCP server including version, article count,
    available categories, and refresh schedule.
    
    Use this to understand the server's capabilities before making content requests.
    """
    return {
        "server_name": "News MCP Server",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0]
    }

@mcp.tool(description="Get comprehensive usage guide and best practices for this MCP server",
    returns="A structured dictionary of server info, categories, query workflow, examples, best practices, and common errors")
def get_usage_guide() -> dict:
    """
    Returns a structured onboarding guide for agents (e.g., Poke).
    This includes:
      - Server metadata
      - Available categories
      - Query workflow (steps 1-6)
      - Example queries (AI regulation, Indian startups, climate policy)
      - Best practices for filtering, evaluation, and presentation
      - Common errors and how to avoid them

    Intended usage:
      - Poke should call this once on startup
      - Use it to learn capabilities, valid categories, and formatting rules
    """
    return {
        "server_info": {
            "name": "News MCP Server",
            "version": "1.0.0",
            "description": "A comprehensive news aggregation and filtering service",
            "maintainer": "Adithya Chittem"
        },
        "available_categories": {
            "tech": "Technology news, product launches, AI, software, and industry trends",
            "startups": "Startup ecosystem, funding rounds, acquisitions, unicorns",
            "business": "Corporate developments, strategy, markets, and industry shifts",
            "finance": "Financial markets, investments, banking, and economic indicators",
            "politics": "Political developments, policy changes, elections, and governance",
            "miscellaneous": "General interest stories (international, society, culture, sports, etc.)"
        },
        "query_workflow": {
            "step_1_request_analysis": {
                "description": "Analyze user request for intent, domain, geography",
                "example": "For 'AI regulation in Europe' → key concepts: AI, regulation, Europe"
            },
            "step_2_category_selection": {
                "description": "Select relevant categories. Always validate against allowed categories.",
                "allowed": ["tech", "startups", "business", "finance", "politics", "miscellaneous"],
                "example": "AI regulation in Europe → categories=['tech','politics']"
            },
            "step_3_initial_query": {
                "description": "Use categories+time window to narrow dataset before semantic filtering",
                "example_query": {
                    "categories": ["tech", "politics"],
                    "hours": 24,
                    "limit": 1000
                },
                "purpose": "This reduces 1500+ raw articles to a manageable set (200–300)"
            },
            "step_4_semantic_filtering": {
                "description": "Apply NLP/semantic filtering in Poke (not MCP) to find truly relevant items",
                "techniques": [
                    "Entity recognition (European Commission, GDPR)",
                    "Geographic context (Europe, EU countries)",
                    "Concept matching (regulation, compliance, law)"
                ]
            },
            "step_5_content_evaluation": {
                "description": "Rank/filter articles for quality & diversity",
                "criteria": ["authority of source", "recency", "perspectives", "significance"]
            },
            "step_6_presentation": {
                "description": "Format results clearly for the user",
                "example_template": {
                    "title": "Article title",
                    "source": "Publication - Category",
                    "url": "Direct link",
                    "summary": "2-3 sentence concise summary",
                    "significance": "1-2 sentence explanation of broader implications"
                }
            }
        },
        "example_queries": {
            "ai_regulation": {
                "user_request": "Show me what's happening with AI regulation in Europe",
                "category_selection": ["tech", "politics"],
                "semantic_filters": ["AI", "regulation", "Europe", "European Commission", "GDPR"]
            },
            "indian_startups": {
                "user_request": "What's new in the Indian startup ecosystem?",
                "category_selection": ["startups", "business", "tech"],
                "semantic_filters": ["India", "funding", "Bangalore", "Mumbai", "venture capital"]
            },
            "climate_policy": {
                "user_request": "Latest developments in climate policy",
                "category_selection": ["politics", "miscellaneous"],
                "semantic_filters": ["climate change", "emissions", "policy", "agreement"]
            }
        },
        "best_practices": {
            "article_selection": [
                "Always use allowed categories",
                "Combine multiple categories when domain overlaps (e.g. tech+politics)",
                "Use semantic filtering after category filtering",
                "Prefer authoritative sources, balance with diverse perspectives"
            ],
            "presentation": [
                "Start with the most significant story",
                "Use concise summaries (2-3 sentences)",
                "Explain why it matters in 1-2 sentences",
                "Group by sub-themes when multiple stories are returned"
            ]
        },
        "common_errors": {
            "missing_categories": "The 'categories' parameter is required",
            "invalid_category": "Only use valid categories: tech, startups, business, finance, politics, miscellaneous",
            "parameter_format": "Categories must be a list, even for one category: ['tech']"
        }
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

@mcp.tool(description="Retrieve latest news articles filtered by categories",
    parameters=[
        {
            "name": "categories",
            "type": "array",
            "description": "List of categories to filter articles by. Allowed: tech, startups, business, finance, politics, miscellaneous",
            "required": True,
            "items": {"type": "string"},
            "example": ["tech", "politics"]
        },
        {
            "name": "hours",
            "type": "integer",
            "description": "Number of hours to look back for articles",
            "required": False,
            "default": 24,
            "example": 72
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum number of articles to return",
            "required": False,
            "default": 1000,
            "example": 500
        }
    ],
    returns="""
    [
        {
            "title": "Article title",
            "url": "https://example.com/article",
            "source": "Publication name",
            "category": "tech",
            "published_at": "2025-09-17T14:30:00Z"
        },
        ...
    ]
    """
)
def latest_articles(
    categories: List[str],
    hours: int = 24,
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Retrieves news articles filtered by specified categories from the past N hours.
    
    This tool should be used for *initial dataset narrowing*. Poke should apply
    semantic filtering afterwards to extract user-specific intent.

    ✅ Best practices:
      1. Always pass categories as a list, even for a single category: ["tech"]
      2. Combine categories for overlapping queries (e.g. ["tech","politics"])
      3. Set `limit` high for broad queries where semantic filtering will follow

    Example usage:
      - AI regulation in Europe:
        latest_articles(categories=["tech", "politics"], hours=24, limit=1000)
      - Indian startup ecosystem:
        latest_articles(categories=["startups", "business"], hours=24, limit=1000)
    """
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

@mcp.tool(
    description="Retrieve the most recent YouTube videos stored in the database",
    parameters=[
        {
            "name": "hours",
            "type": "integer",
            "description": "Number of hours to look back for videos",
            "required": False,
            "default": 24,
            "example": 48
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum number of videos to return",
            "required": False,
            "default": 50,
            "example": 20
        },
        {
            "name": "channel",
            "type": "string",
            "description": "Optional: filter videos by channel name",
            "required": False,
            "example": "Bloomberg"
        }
    ],
    returns="""
    [
        {
            "title": "Video title",
            "channel": "Channel name",
            "url": "https://example.com/video",
            "published_at": "2025-09-17T14:30:00Z"
        },
        ...
    ]
    """
)
def latest_videos(
    hours: int = 24,
    limit: int = 50,
    channel: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves video content from the past N hours.

    ✅ Best practices:
      1. Use channel filter for targeted requests
      2. Adjust `hours` depending on whether you want breaking videos or deep backlog
      3. Combine with semantic filtering for topics ("AI regulation", "founder interview")

    Example usage:
      - Tech product launches:
        latest_videos(hours=168, limit=50, channel="The Verge")
      - Business analysis shows:
        latest_videos(hours=72, limit=50, channel="Bloomberg")
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
