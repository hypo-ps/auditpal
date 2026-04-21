"""Export utilities for chat conversations."""

from typing import List
from datetime import datetime
from pathlib import Path
import io


def export_to_markdown(messages: List[dict], notebook_title: str = "AuditPal Chat") -> str:
    """Export chat messages to Markdown format."""
    
    lines = [
        f"# {notebook_title}",
        f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        ""
    ]
    
    for msg in messages:
        role = "**You:**" if msg["role"] == "user" else "**AuditPal:**"
        timestamp = msg.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = f" *({dt.strftime('%H:%M')})*"
            except:
                timestamp = ""
        
        lines.append(f"{role}{timestamp}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def export_to_pdf(messages: List[dict], notebook_title: str = "AuditPal Chat") -> bytes:
    """Export chat messages to PDF format."""
    
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, notebook_title, ln=True, align="C")
    
    # Export date
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # Messages
    for msg in messages:
        # Role header
        role = "You:" if msg["role"] == "user" else "AuditPal:"
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 150 if msg["role"] == "user" else 0)
        pdf.cell(0, 8, role, ln=True)
        
        # Content
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        # Handle multi-line content
        content = msg["content"]
        # Clean up markdown formatting for PDF
        content = content.replace("**", "").replace("*", "")
        content = content.replace("###", "").replace("##", "").replace("#", "")
        
        pdf.multi_cell(0, 6, content)
        pdf.ln(5)
        
        # Separator
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    
    # Return as bytes
    return pdf.output()


def get_download_filename(notebook_title: str, format: str) -> str:
    """Generate a download filename."""
    
    # Clean title for filename
    clean_title = "".join(c if c.isalnum() or c in " -_" else "" for c in notebook_title)
    clean_title = clean_title.replace(" ", "_")[:50]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    return f"{clean_title}_{timestamp}.{format}"
