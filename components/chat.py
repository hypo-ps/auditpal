"""Chat interface component for AuditPal."""

import html
import re
import streamlit as st
from typing import List, Callable
from datetime import datetime

from config import PROMPT_TEMPLATES

_CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

_CITATION_CSS = """
<style>
.cite-marker {
    position: relative;
    display: inline-block;
    color: #0066cc;
    font-weight: 700;
    background: #e8f0fe;
    padding: 1px 6px;
    border-radius: 4px;
    margin: 0 2px;
    font-size: 0.78em;
    cursor: help;
    line-height: 1.2;
}
.cite-marker:hover { background: #d4e3fc; }
.cite-tooltip {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    width: max-content;
    max-width: 360px;
    min-width: 220px;
    background: #1f1f1f;
    color: #f1f3f4;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 400;
    text-align: left;
    z-index: 999999;
    box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    white-space: normal;
    line-height: 1.45;
    transition: opacity 0.12s, visibility 0.12s;
    user-select: text;
    cursor: text;
}
.cite-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    height: 10px;
}
.cite-marker:hover .cite-tooltip,
.cite-tooltip:hover {
    visibility: visible;
    opacity: 1;
}
.cite-tt-title {
    display: block;
    color: #8ab4f8;
    font-weight: 600;
    font-size: 11.5px;
    margin-bottom: 5px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.cite-tt-text { display: block; color: #e8eaed; font-style: italic; }
.cite-tt-empty { display: block; color: #9aa0a6; font-style: italic; }
</style>
"""


def _render_assistant_message(content: str, references: List[dict]):
    """Render an assistant message with inline hover-tooltip citations."""
    if not references:
        st.markdown(content)
        return

    refs_by_num = {
        r["citation_number"]: r for r in references if r.get("citation_number")
    }

    def _badge(n: int) -> str:
        ref = refs_by_num.get(n)
        if not ref:
            return f"[{n}]"
        title = html.escape(ref.get("source_title") or "Source")
        excerpt = ref.get("cited_text") or ""
        if excerpt:
            body_html = html.escape(excerpt[:400]).replace("\n", "<br>")
            body = f'<span class="cite-tt-text">{body_html}</span>'
        else:
            body = '<span class="cite-tt-empty">(no excerpt extracted)</span>'
        return (
            f'<span class="cite-marker">[{n}]'
            f'<span class="cite-tooltip">'
            f'<span class="cite-tt-title">{title}</span>{body}'
            f'</span></span>'
        )

    def _replace(match):
        nums = [int(n.strip()) for n in match.group(1).split(",")]
        return "".join(_badge(n) for n in nums)

    enhanced = _CITATION_PATTERN.sub(_replace, content)
    st.markdown(enhanced, unsafe_allow_html=True)


def render_chat(
    messages: List[dict],
    on_send: Callable[[str], str],
    on_clear: Callable,
    on_export: Callable[[str], None],
    disabled: bool = False
):
    """Render the chat interface."""

    st.markdown(_CITATION_CSS, unsafe_allow_html=True)

    # Header with actions
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown("## 💬 Chat")
    with col2:
        if st.button("🗑️ Clear", use_container_width=True, disabled=disabled):
            on_clear()
            st.rerun()
    with col3:
        export_format = st.selectbox(
            "Export",
            options=["", "Markdown", "PDF"],
            label_visibility="collapsed",
            disabled=disabled or not messages
        )
        if export_format:
            on_export(export_format.lower())
    
    if disabled:
        st.warning("⚠️ Add sources to start chatting")
        return
    
    # Quick templates
    with st.expander("🎯 Quick Templates", expanded=False):
        cols = st.columns(4)
        templates_list = list(PROMPT_TEMPLATES.items())[:8]  # Show first 8
        
        for idx, (key, template) in enumerate(templates_list):
            with cols[idx % 4]:
                if st.button(
                    template["name"].split(" ", 1)[0],  # Just emoji
                    key=f"quick_{key}",
                    help=template["name"],
                    use_container_width=True
                ):
                    st.session_state["pending_message"] = template["prompt"]
                    st.rerun()
    
    # Chat messages container
    chat_container = st.container()

    with chat_container:
        if not messages:
            st.info("👋 Ask a question about your documents!")
        else:
            for msg in messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "assistant":
                        _render_assistant_message(
                            msg["content"], msg.get("references", [])
                        )
                        if st.button("📋 Copy", key=f"copy_{hash(msg['content'][:50])}"):
                            st.toast("Copied to clipboard!")
                    else:
                        st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your documents...", disabled=disabled):
        _handle_message(prompt, messages, on_send, chat_container)
    
    # Handle pending message from template
    if "pending_message" in st.session_state:
        prompt = st.session_state.pop("pending_message")
        _handle_message(prompt, messages, on_send, chat_container)


def _handle_message(prompt: str, messages: List[dict], on_send: Callable, container):
    """Handle sending a message and getting response."""
    
    # Add user message
    messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    
    with container:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = on_send(prompt)
                    if isinstance(response, dict):
                        answer = response.get("answer", "")
                        references = response.get("references", [])
                    else:
                        answer = response
                        references = []

                    _render_assistant_message(answer, references)

                    messages.append({
                        "role": "assistant",
                        "content": answer,
                        "references": references,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "references": [],
                        "timestamp": datetime.now().isoformat()
                    })
