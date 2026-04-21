"""Pre-built prompt templates for accountants."""

import streamlit as st
from typing import Callable
from config import PROMPT_TEMPLATES


def render_templates(on_template_select: Callable[[str], None]):
    """Render the prompt templates panel."""
    
    st.markdown("### 🎯 Quick Actions")
    st.caption("Click a template to use it")
    
    # Group templates by category
    categories = {}
    for key, template in PROMPT_TEMPLATES.items():
        cat = template["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, template))
    
    # Render by category
    for category, templates in categories.items():
        st.markdown(f"**{category}**")
        
        cols = st.columns(2)
        for idx, (key, template) in enumerate(templates):
            with cols[idx % 2]:
                if st.button(
                    template["name"],
                    key=f"template_{key}",
                    use_container_width=True,
                    help=template["prompt"][:100] + "..."
                ):
                    on_template_select(template["prompt"])
        
        st.write("")  # Spacing


def render_templates_inline(on_template_select: Callable[[str], None]):
    """Render templates as an inline selector (compact version)."""
    
    with st.expander("🎯 Quick Templates", expanded=False):
        template_names = {
            f"{t['name']}": t["prompt"] 
            for t in PROMPT_TEMPLATES.values()
        }
        
        selected = st.selectbox(
            "Choose a template",
            options=[""] + list(template_names.keys()),
            format_func=lambda x: x if x else "Select a template..."
        )
        
        if selected and selected in template_names:
            st.caption(f"*{template_names[selected][:100]}...*")
            if st.button("Use this template", use_container_width=True):
                on_template_select(template_names[selected])
