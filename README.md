# Digital Catalogue Generator (Brass Line Hirer)

Autonomous high-precision catalogue generator that professionally extracts product images and grounds them onto luxury template display podiums.

---

## 🌟 Key Features

1. **Autonomous High-Precision Matting**:
   - Uses neural edge segmentation (`IS-Net`) to cleanly extract complex metallic, reflective, and patterned brass products from raw, uncurated photos (removing background blinds, floors, tables, and reflections).

2. **Physics-Based Contact Shadow & Occlusion**:
   - Generates two-tier contact shadows:
     - **Contact Occlusion**: High-density shadow anchored directly under product feet and base contact lines to eliminate floating.
     - **Diffused Ambient Ground Shadow**: Soft elliptical projection onto the marble pedestal surface matching the studio scene depth.

3. **100% Brand & Template Integrity**:
   - Preserves all original template elements ("BLH", "BRASS LINE HIRER", floral leaf motif, golden arch frames, bottom guarantee badges).
   - **Zero Text / Clean Placards**: Strictly adheres to the requirement that no product names or extra text are written onto the green placards, leaving them pristine.
   - Foreground placard preservation: Golden ornaments and green banners remain crisp in front of the marble pedestal.

4. **Studio Lighting Harmonization**:
   - Calibrates color temperature and tone curve (+warmth, subtle golden highlight glow) so products match the template's warm champagne ambiance.

5. **Pluggable Google Colab Gradio AI Bridge**:
   - Ready to connect to your live Gradio endpoint (Qwen2 / image generation / relighting model) whenever you provide the URL.
   - Built-in automatic fallback: If the Gradio endpoint is offline or not yet connected, the local autonomous engine runs seamlessly with zero downtime.

6. **Dual Interfaces**:
   - **Command Line (CLI)**: For terminal automation, CI/CD, and batch processing.
   - **Interactive Web Studio (Streamlit)**: Luxury UI for live previews, slider tuning, drag-and-drop uploads, and one-click high-res downloads.

---

## 📁 Project Structure

```
Digital Catalogue Generator/
│
├── Empty Template.png          # Base luxury catalogue template (1024 x 1536)
├── Output Sample 1.png         # Reference target output
├── Final_Catalogue_Output.png  # Generated output from the 4 brass products
│
├── catalogue_core.py           # Core matting, shadow physics, & compositing engine
├── colab_bridge.py             # Google Colab Gradio API client & fallback bridge
├── run_generator.py            # CLI entry point (single page & batch mode)
├── app.py                      # Interactive Streamlit Web Studio
├── config.json                 # Persistent configuration (Gradio URL, defaults)
└── README.md                   # System documentation
```

---

## 🚀 How to Run

### 1. Run via CLI (One Command)

To generate a catalogue from the 4 product photos:
```bash
python run_generator.py --template "Empty Template.png" --products "Product 1.jpeg" "Product 2.jpeg" "Product 3.jpeg" "Product 4.jpeg" --output "Final_Catalogue_Output.png"
```

To batch process an entire folder of products (every 4 products creates a new catalogue page):
```bash
python run_generator.py --products-dir ./my_products --batch --output-dir ./output
```

Fine-tuning options:
```bash
python run_generator.py --scale 1.05 --y-offset -5 --warmth 1.2
```

---

### 2. Launch the Interactive Web Studio

Start the luxury web dashboard:
```bash
streamlit run app.py
```
Then open your browser at `http://localhost:8501`.

Inside the web studio:
- Preview products and template.
- Adjust sliders (scale, vertical base position, warmth).
- Connect your Colab Gradio endpoint.
- Click **GENERATE LUXURY CATALOGUE PAGE** and download high-resolution PNGs.

---

### 3. Connecting Your Google Colab Gradio Endpoint

When your Google Colab script generates a public Gradio URL (e.g., `https://xxxx.gradio.live`):

1. **Via Web Studio**: Enter the URL in the sidebar under "Google Colab AI Endpoint" and click **Connect**.
2. **Via CLI**:
   ```bash
   python run_generator.py --gradio-url "https://xxxx.gradio.live"
   ```
3. **Via `config.json`**:
   ```json
   {
     "gradio_endpoint_url": "https://xxxx.gradio.live"
   }
   ```
