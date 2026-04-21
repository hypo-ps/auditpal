"""Chat interface component for AuditPal."""

import streamlit as st
from typing import List, Callable
from datetime import datetime

from config import PROMPT_TEMPLATES


def render_chat(
    messages: List[dict],
    on_send: Callable[[str], str],
    on_clear: Callable,
    on_export: Callable[[str], None],
    disabled: bool = False
):
    """Render the chat interface."""
    
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
    chat_container = st.container(height=400)
    
    with chat_container:
        if not messages:
            st.info("👋 Ask a question about your documents!")
        else:
            for msg in messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant":
                        # Copy button for assistant messages
                        if st.button("📋 Copy", key=f"copy_{hash(msg['content'][:50])}"):
                            st.toast("Copied to clipboard!")
    
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
                    st.markdown(response)
                    
                    messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
