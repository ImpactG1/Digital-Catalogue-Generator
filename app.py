"""
Digital Catalogue Generator - Interactive Luxury Studio
Streamlit Web Application for autonomous catalogue page generation.
"""

import os
import io
import time
from typing import List, Optional
import streamlit as st
from PIL import Image
from catalogue_core import PhotorealisticCompositor, SlotConfig, DEFAULT_SLOTS
from colab_bridge import ColabGradioBridge, load_config, save_config

st.set_page_config(
    page_title="Brass Line Hirer - Digital Catalogue Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Luxury CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Montserrat:wght@300;400;500;600&display=swap');

    :root {
        --gold-primary: #d4af37;
        --gold-light: #f3e5ab;
        --dark-green: #0a1e16;
        --dark-surface: #12241d;
        --text-gold: #e8d8a6;
    }

    .main {
        background: radial-gradient(circle at 50% 20%, #163024 0%, #08140f 100%);
        color: #f0f0f0;
        font-family: 'Montserrat', sans-serif;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Cinzel', serif !important;
        letter-spacing: 2px;
        color: var(--gold-primary) !important;
    }

    .brand-header {
        text-align: center;
        padding: 20px 0 10px 0;
        border-bottom: 1px solid rgba(212, 175, 55, 0.25);
        margin-bottom: 20px;
    }

    .brand-subtitle {
        font-size: 0.95rem;
        letter-spacing: 3px;
        color: var(--gold-light);
        opacity: 0.85;
        text-transform: uppercase;
    }

    .stButton>button {
        background: linear-gradient(135deg, #c5a028 0%, #9e7d17 100%) !important;
        color: #0d1a14 !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        border: 1px solid #f3e5ab !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
    }

    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .status-connected {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid #22c55e;
    }
    .status-offline {
        background: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid #eab308;
    }

    div[data-testid="stSidebar"] {
        background-color: #0a1712 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.2);
    }
</style>
""", unsafe_allow_html=True)


# Header
st.markdown("""
<div class="brand-header">
    <div class="brand-title" style="font-size: 2.2rem; font-weight: 700;">BRASS LINE HIRER</div>
    <div class="brand-subtitle">Autonomous Digital Catalogue Studio</div>
</div>
""", unsafe_allow_html=True)

# State initialization
if "config" not in st.session_state:
    st.session_state.config = load_config()

if "bridge" not in st.session_state:
    st.session_state.bridge = ColabGradioBridge()
    # Test connection on launch
    st.session_state.bridge.test_connection()

if "generated_image" not in st.session_state:
    if os.path.exists("Luxury_Catalogue_Master.png"):
        st.session_state.generated_image = Image.open("Luxury_Catalogue_Master.png")
    elif os.path.exists("Final_Catalogue_Output.png"):
        st.session_state.generated_image = Image.open("Final_Catalogue_Output.png")
    else:
        st.session_state.generated_image = None


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ System Controls")

    # Colab Gradio Bridge Panel
    st.markdown("#### 🌐 Google Colab AI Endpoint")
    gradio_input = st.text_input(
        "Live Gradio URL",
        value=st.session_state.config.get("gradio_endpoint_url", "https://d2963a9a901fe1a4e2.gradio.live"),
        help="Active Gradio link hosted on Google Colab."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Check Link"):
            st.session_state.bridge.set_endpoint(gradio_input)

    if st.session_state.bridge.is_connected:
        st.markdown("<span class='status-badge status-connected'>🟢 Colab Qwen 2.1 Online</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='status-badge status-offline'>⚡ Local Precision Engine Active</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🎨 Precision Studio Tuning")
    scale_factor = st.slider("Product Scale", min_value=0.7, max_value=1.3, value=1.0, step=0.05)
    y_offset = st.slider("Vertical Base Grounding (px)", min_value=-40, max_value=40, value=0, step=2)
    warmth = st.slider("Studio Warmth Harmonization", min_value=0.0, max_value=2.0, value=1.0, step=0.1)

    st.markdown("---")
    engine_choice = st.radio(
        "Generation Engine",
        ["Local Precision Engine (Reflections & Contact Physics)", "Google Colab Qwen 2.1 AI Model"]
    )


# Main Layout
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.markdown("### 📦 Product Selection")
    st.caption("Upload or select products to professionally place on the four marble podiums.")

    input_mode = st.radio("Source", ["4 Demo Brass Products", "Upload Custom Products"], horizontal=True)

    selected_products = []
    if input_mode == "4 Demo Brass Products":
        selected_products = ["Product 1.jpeg", "Product 2.jpeg", "Product 3.jpeg", "Product 4.jpeg"]
        p1, p2 = st.columns(2)
        with p1:
            st.image("Product 1.jpeg", caption="Product 1: Chafing Dish", use_container_width=True)
            st.image("Product 3.jpeg", caption="Product 3: Handi Stand", use_container_width=True)
        with p2:
            st.image("Product 2.jpeg", caption="Product 2: Chafing Dome", use_container_width=True)
            st.image("Product 4.jpeg", caption="Product 4: Burner Riser", use_container_width=True)
    else:
        uploaded_files = st.file_uploader(
            "Upload 1 to 4 product photos",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for f in uploaded_files[:4]:
                selected_products.append(Image.open(f))

    st.markdown("---")
    gen_btn = st.button("✨ GENERATE LUXURY CATALOGUE PAGE", use_container_width=True)


with col_right:
    st.markdown("### 🏆 High-Resolution Catalogue Output")

    if gen_btn and selected_products:
        if engine_choice == "Local Precision Engine (Reflections & Contact Physics)":
            with st.spinner("Extracting cutouts, rendering marble reflections & contact shadows..."):
                compositor = PhotorealisticCompositor("Empty Template.png")
                out_img = compositor.generate_page(
                    selected_products,
                    scale_factor=scale_factor,
                    y_offset=y_offset,
                    warmth=warmth
                )
                st.session_state.generated_image = out_img
                out_img.save("Luxury_Catalogue_Master.png", quality=95)
                st.toast("Generated with marble reflections & contact physics!", icon="✨")
        else:
            with st.spinner("Calling Google Colab Qwen 2.1 model endpoint..."):
                prompt = "Put these product images inside template such that they look professionally placed and natural. Do not name those products."
                prod_paths = [p if isinstance(p, str) else "Product 1.jpeg" for p in selected_products]
                qwen_img = st.session_state.bridge.generate_with_qwen(
                    prompt=prompt,
                    template_path="Empty Template.png",
                    product_paths=prod_paths
                )
                if qwen_img:
                    st.session_state.generated_image = qwen_img
                    qwen_img.save("Qwen_Generated_Output.png")
                    st.toast("Qwen 2.1 inference finished!", icon="✨")
                else:
                    st.error("Colab endpoint call failed or returned empty. Check the terminal logs.")

    if st.session_state.generated_image is not None:
        st.image(st.session_state.generated_image, caption="1024 × 1536 Catalogue Output", use_container_width=True)

        buf = io.BytesIO()
        st.session_state.generated_image.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download High-Res Catalogue Page (PNG)",
            data=buf.getvalue(),
            file_name="Brass_Line_Hirer_Catalogue.png",
            mime="image/png",
            use_container_width=True
        )
