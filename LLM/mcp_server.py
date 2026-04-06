"""
MCP Server — runs as a separate process, communicates over stdio.
Start it with:  python mcp_server.py

Exposes:
  Tools     — DB queries + RAG search over the knowledge base
  Resources — The 3 PDF manuals as readable doc:// URIs
"""

import json
import sqlite3
import datetime
import os
import glob
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MaintenanceServer")

DB             = "maintenance.db"
KNOWLEDGE_PATH = "knowledge/*.pdf"
VECTOR_DB_PATH = "./vector_db_improved2"
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"
TOP_K          = 4


# ══════════════════════════════════════════════════════════════════════════════
# TOOLS — callable actions the LLM can invoke
# ══════════════════════════════════════════════════════════════════════════════

# ── Tool 1: List equipment by location ───────────────────────────────────────
@mcp.tool()
def list_equipment(location: str = "") -> str:
    """
    List equipment from the maintenance database.
    Optionally filter by location (Plant A, Plant B, Unit 1, Unit 2, Warehouse).
    Leave location empty to list all equipment.
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute(
                "SELECT id, name, serial_number, location, status FROM equipment WHERE location = ?",
                (location,)
            )
        else:
            cursor.execute("SELECT id, name, serial_number, location, status FROM equipment")
        rows = cursor.fetchall()

    if not rows:
        return json.dumps({"equipment": [], "count": 0})

    equipment = [
        {"id": r[0], "name": r[1], "serial_number": r[2], "location": r[3], "status": r[4]}
        for r in rows
    ]
    return json.dumps({"equipment": equipment, "count": len(equipment)})


# ── Tool 2: Get upcoming maintenance ─────────────────────────────────────────
@mcp.tool()
def get_upcoming_maintenance(days_ahead: int = 30) -> str:
    """
    Get equipment whose next maintenance is due within the specified number of days.
    Returns equipment name, maintenance type, and due date.
    """
    today  = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days_ahead)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.name, e.location, m.maintenance_type, m.next_due
            FROM equipment e
            JOIN maintenance_plan m ON e.id = m.equipment_id
            WHERE m.next_due <= ?
            ORDER BY m.next_due ASC
            """,
            (cutoff.isoformat(),)
        )
        rows = cursor.fetchall()

    if not rows:
        return json.dumps({"due": [], "count": 0, "as_of": today.isoformat()})

    due = [
        {"equipment": r[0], "location": r[1], "maintenance_type": r[2], "next_due": r[3]}
        for r in rows
    ]
    return json.dumps({"due": due, "count": len(due), "as_of": today.isoformat()})


# ── Tool 3: Get full details for a single equipment item ─────────────────────
@mcp.tool()
def get_equipment_details(equipment_name: str) -> str:
    """
    Get full details for a specific equipment item including its maintenance plan.
    equipment_name should match the name in the database, e.g. 'Fan-3' or 'Pump-7'.
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.id, e.name, e.serial_number, e.location, e.purchase_date, e.status,
                   m.maintenance_type, m.frequency_days, m.last_maintenance, m.next_due
            FROM equipment e
            JOIN maintenance_plan m ON e.id = m.equipment_id
            WHERE e.name = ?
            """,
            (equipment_name,)
        )
        row = cursor.fetchone()

    if not row:
        return json.dumps({"error": f"Equipment '{equipment_name}' not found"})

    return json.dumps({
        "id": row[0], "name": row[1], "serial_number": row[2],
        "location": row[3], "purchase_date": row[4], "status": row[5],
        "maintenance_type": row[6], "frequency_days": row[7],
        "last_maintenance": row[8], "next_due": row[9],
    })


# ── Tool 4: Maintenance stats by location ────────────────────────────────────
@mcp.tool()
def maintenance_stats_by_location() -> str:
    """
    Return a summary of total equipment count and overdue maintenance count per location.
    """
    today = datetime.date.today().isoformat()

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.location,
                   COUNT(e.id) AS total_equipment,
                   SUM(CASE WHEN m.next_due < ? THEN 1 ELSE 0 END) AS overdue_count
            FROM equipment e
            JOIN maintenance_plan m ON e.id = m.equipment_id
            GROUP BY e.location
            ORDER BY overdue_count DESC
            """,
            (today,)
        )
        rows = cursor.fetchall()

    stats = [
        {"location": r[0], "total_equipment": r[1], "overdue": r[2]}
        for r in rows
    ]
    return json.dumps({"stats": stats, "as_of": today})


# ── Tool 5: RAG — search the technical manuals knowledge base ─────────────────
@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 4) -> str:
    """
    Search the technical manuals knowledge base using semantic similarity.
    Use this to answer questions about equipment procedures, maintenance steps,
    installation instructions, troubleshooting, or any content from the manuals.
    Returns the most relevant text chunks with their source document and page number.

    Available manuals:
      - PWI_Pump.pdf         — Pump installation, operation and maintenance manual
      - compressed_air_manual.pdf — Compressed air system manual
      - heat_pump.pdf        — Heat pump manual
    """
    try:
        from langchain_community.embeddings import OllamaEmbeddings
        from langchain_chroma import Chroma

        embeddings  = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
        vectorstore = Chroma(persist_directory=VECTOR_DB_PATH, embedding_function=embeddings)
        retriever   = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": min(top_k, TOP_K)}
        )

        docs = retriever.invoke(query)

        if not docs:
            return json.dumps({"results": [], "query": query, "message": "No relevant content found."})

        results = [
            {
                "rank":    i + 1,
                "source":  doc.metadata.get("source", "unknown"),
                "page":    doc.metadata.get("page", "?"),
                "content": doc.page_content.strip(),
            }
            for i, doc in enumerate(docs)
        ]
        return json.dumps({"results": results, "query": query, "total": len(results)})

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


# ══════════════════════════════════════════════════════════════════════════════
# RESOURCES — read-only documents the client can fetch directly
# Each PDF is exposed as a  doc://<filename>  URI
# ══════════════════════════════════════════════════════════════════════════════

def _pdf_to_text(pdf_path: str) -> str:
    """Extract full text from a PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc   = fitz.open(pdf_path)
        pages = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                pages.append(f"--- Page {page_num} ---\n{text}")
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        return f"Error reading PDF: {e}"


@mcp.resource("doc://PWI_Pump.pdf")
def resource_pwi_pump() -> str:
    """
    Full text of the PWI Pump Installation, Operation and Maintenance Manual.
    Covers installation, operation, maintenance procedures, troubleshooting, and spare parts.
    """
    return _pdf_to_text("knowledge/PWI_Pump.pdf")


@mcp.resource("doc://compressed_air_manual.pdf")
def resource_compressed_air() -> str:
    """
    Full text of the Compressed Air System Manual.
    Covers compressed air system design, operation, maintenance and safety.
    """
    return _pdf_to_text("knowledge/compressed_air_manual.pdf")


@mcp.resource("doc://heat_pump.pdf")
def resource_heat_pump() -> str:
    """
    Full text of the Heat Pump Manual.
    Covers heat pump installation, operation, maintenance and troubleshooting.
    """
    return _pdf_to_text("knowledge/heat_pump.pdf")


if __name__ == "__main__":
    mcp.run(transport="stdio")
