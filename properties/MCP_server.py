"""
LuxeEstate MCP Server
=====================
Exposes LuxeEstate's property search, chatbot, and booking tools as
Model Context Protocol (MCP) tools.

This lets Claude Desktop (or any MCP client) call:
  - search_properties   → query live DB
  - ask_luxe_ai         → run a message through the NIM-powered chatbot
  - book_call           → create a lead/appointment

Running standalone (for Claude Desktop):
  python mcp_server.py

Claude Desktop config (~/.config/claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "luxeestate": {
        "command": "python",
        "args": ["/path/to/LuxeEstate_updated/mcp_server.py"],
        "env": {
          "DJANGO_SETTINGS_MODULE": "LuxeEstate.settings",
          "PYTHONPATH": "/path/to/LuxeEstate_updated"
        }
      }
    }
  }

Requirements:
  pip install mcp django
"""

from __future__ import annotations

import json
import os
import sys

# Bootstrap Django before importing anything from the project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LuxeEstate.settings")

import django
django.setup()

# Now safe to import project code
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("luxeestate")


# ── Tool: search_properties ────────────────────────────────────────────────

@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="search_properties",
            description=(
                "Search LuxeEstate's live property database. "
                "Returns matching properties with price, location, BHK, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name (e.g. Mumbai, Bangalore)"},
                    "property_type": {
                        "type": "string",
                        "enum": ["apartment", "house", "villa", "plot", "commercial"],
                        "description": "Type of property",
                    },
                    "min_price": {"type": "number", "description": "Minimum price in INR"},
                    "max_price": {"type": "number", "description": "Maximum price in INR"},
                    "bedrooms": {"type": "integer", "description": "Number of bedrooms (BHK)"},
                    "listing_type": {
                        "type": "string",
                        "enum": ["sale", "rent"],
                        "description": "Whether to buy or rent",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 5)"},
                },
            },
        ),
        types.Tool(
            name="ask_luxe_ai",
            description=(
                "Send a natural-language message to the LuxeEstate AI chatbot (powered by NVIDIA NIM). "
                "The bot handles property searches, EMI calculations, appointment scheduling, and more. "
                "Pass a session_id to maintain conversation context across multiple turns."
            ),
            inputSchema={
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {"type": "string", "description": "User's message"},
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID to continue a conversation",
                    },
                },
            },
        ),
        types.Tool(
            name="book_call",
            description=(
                "Book a property viewing / consultation call. "
                "Creates a Lead and Appointment in the LuxeEstate database."
            ),
            inputSchema={
                "type": "object",
                "required": ["name", "contact"],
                "properties": {
                    "name": {"type": "string", "description": "Visitor's full name"},
                    "contact": {"type": "string", "description": "Phone number or email"},
                    "property_id": {"type": "integer", "description": "Property ID (optional)"},
                    "preferred_datetime": {
                        "type": "string",
                        "description": "Preferred date/time string (e.g. 'Saturday 3 PM')",
                    },
                    "notes": {"type": "string", "description": "Any additional notes"},
                },
            },
        ),
    ]


# ── Tool handler ───────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_properties":
        return await _search_properties(arguments)
    if name == "ask_luxe_ai":
        return await _ask_luxe_ai(arguments)
    if name == "book_call":
        return await _book_call(arguments)
    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


# ── Tool implementations ───────────────────────────────────────────────────

async def _search_properties(args: dict):
    from properties.models import Property
    from django.db.models import Q

    qs = Property.objects.filter(is_active=True)

    if args.get("city"):
        qs = qs.filter(city__icontains=args["city"])
    if args.get("property_type"):
        qs = qs.filter(property_type=args["property_type"])
    if args.get("listing_type"):
        qs = qs.filter(listing_type=args["listing_type"])
    if args.get("bedrooms"):
        qs = qs.filter(bedrooms=args["bedrooms"])
    if args.get("min_price"):
        qs = qs.filter(price__gte=args["min_price"])
    if args.get("max_price"):
        qs = qs.filter(price__lte=args["max_price"])

    limit = min(int(args.get("limit", 5)), 10)
    results = []
    for p in qs[:limit]:
        results.append({
            "id": p.pk,
            "title": p.title,
            "city": p.city,
            "location": p.location,
            "property_type": p.property_type,
            "listing_type": p.listing_type,
            "bedrooms": p.bedrooms,
            "bathrooms": getattr(p, "bathrooms", None),
            "area_sqft": getattr(p, "area_sqft", None),
            "price": str(p.price),
            "url": f"/detail/{p.pk}/",
        })

    output = json.dumps({"count": len(results), "properties": results}, indent=2, default=str)
    return [types.TextContent(type="text", text=output)]


# In-memory session store for MCP (no cache backend available standalone)
_mcp_sessions: dict[str, dict] = {}

async def _ask_luxe_ai(args: dict):
    from properties.chatbot_service import LuxeChatbot

    message = args["message"]
    session_id = args.get("session_id", "mcp_default")

    conversation_state = _mcp_sessions.get(session_id)
    bot = LuxeChatbot()
    result = bot.process_message(message, conversation_state=conversation_state)

    # Persist state
    if result.get("conversation_state"):
        _mcp_sessions[session_id] = result["conversation_state"]

    response_text = result.get("response") or result.get("message") or ""

    # Append property summaries if present
    properties = result.get("properties") or []
    if properties:
        lines = [f"\n\nFound {len(properties)} propert(y/ies):"]
        for p in properties[:5]:
            lines.append(
                f"• {p.get('title')} | {p.get('city')} | ₹{p.get('price')} | {p.get('bedrooms')} BHK | ID:{p.get('id')}"
            )
        response_text += "\n".join(lines)

    return [types.TextContent(type="text", text=response_text)]


async def _book_call(args: dict):
    from properties.models import Lead, Appointment, Property
    from django.utils import timezone

    # Create or update lead
    lead = Lead.objects.create(
        name=args["name"],
        contact=args["contact"],
        intent="buy",
        status="new",
        notes=args.get("notes", "Booked via MCP / Telegram"),
    )

    # Attach property if given
    property_obj = None
    if args.get("property_id"):
        try:
            property_obj = Property.objects.get(pk=args["property_id"])
        except Property.DoesNotExist:
            pass

    # Create appointment
    appt_data = {
        "lead": lead,
        "status": "scheduled",
        "notes": args.get("preferred_datetime", ""),
    }
    if property_obj:
        appt_data["property"] = property_obj

    Appointment.objects.create(**appt_data)

    result = {
        "success": True,
        "lead_id": lead.pk,
        "message": (
            f"✅ Booking confirmed for {args['name']}. "
            f"An agent will contact you at {args['contact']} shortly."
        ),
    }
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ── Entry point ────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())