#!/usr/bin/env python3
"""
Single‑file Streamlit dashboard to keep only black text from scanned forms.
Supports images (PNG, JPG, TIFF, BMP) and multi‑page PDFs.
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import fitz
from io import BytesIO
import zipfile

# ------------------------------------------------------------
#  Custom CSS for a polished look
# ------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e1e1e, #4a4a4a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .upload-box {
        border: 2px dashed #aaa;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: border-color 0.3s;
    }
    .upload-box:hover {
        border-color: #ff4b4b;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #e43e3e;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,75,75,0.3);
    }
    .footer {
        text-align: center;
        color: #999;
        margin-top: 3rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Core functions (unchanged)
# ------------------------------------------------------------
def keep_only_black(img_bgr, threshold=50, make_transparent=False):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    mask = gray <= threshold
    if make_transparent:
        h, w = img_bgr.shape[:2]
        out = np.zeros((h, w, 4), dtype=np.uint8)
        out[mask] = [0, 0, 0, 255]
        return out
    else:
        out = np.full_like(img_bgr, 255)
        out[mask] = [0, 0, 0]
        return out

def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        images.append(img)
    doc.close()
    return images

def images_to_pdf_bytes(images, dpi=300):
    pdf_doc = fitz.open()
    for img in images:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pix = fitz.Pixmap(fitz.csRGB, rgb.shape[1], rgb.shape[0], rgb.tobytes())
        page = pdf_doc.new_page(width=pix.width / dpi * 72, height=pix.height / dpi * 72)
        page.insert_image(page.rect, pixmap=pix)
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()
    return BytesIO(pdf_bytes)

def create_zip_of_images(images, format="PNG"):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(images):
            ret, encoded = cv2.imencode(f".{format.lower()}", img)
            if ret:
                zf.writestr(f"page_{i+1}.{format.lower()}", encoded.tobytes())
    zip_buffer.seek(0)
    return zip_buffer

# ------------------------------------------------------------
#  UI Layout
# ------------------------------------------------------------
st.set_page_config(page_title="FormCleaner – Black Text Only", layout="wide", page_icon="📝")

# Header
st.markdown('<div class="main-header">📝 FormCleaner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Remove all colors, keep only black text. Upload images or PDFs.</div>', unsafe_allow_html=True)

# Settings in an expander for a cleaner look
with st.sidebar:
    st.header("⚙️ Settings")
    threshold = st.slider("Black threshold", 0, 255, 50, 5,
                          help="Lower = stricter black. Only pixels darker than this value are kept.")
    transparent_bg = st.checkbox("Transparent background (images only)", False,
                                 help="Creates a PNG with transparent background (not for PDFs).")
    st.markdown("---")
    st.caption("Made with ❤️ by Bipul Das")

# Main area
uploaded_file = st.file_uploader(
    "Drag & drop your file here",
    type=["png", "jpg", "jpeg", "tiff", "bmp", "pdf"],
    help="Limit: 200MB per file"
)

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        # PDF processing
        with st.spinner("🔄 Processing PDF pages..."):
            pdf_bytes = uploaded_file.read()
            pages_bgr = pdf_to_images(pdf_bytes)
        st.success(f"✅ Loaded {len(pages_bgr)} page(s)")

        if pages_bgr:
            processed_pages = []
            for i, page in enumerate(pages_bgr):
                processed = keep_only_black(page, threshold)
                processed_pages.append(processed)

            # Preview first page
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original (page 1)")
                st.image(cv2.cvtColor(pages_bgr[0], cv2.COLOR_BGR2RGB), use_container_width=True)
            with col2:
                st.subheader("Filtered (page 1)")
                st.image(cv2.cvtColor(processed_pages[0], cv2.COLOR_BGR2RGB), use_container_width=True)

            # Download options
            st.subheader("📥 Download cleaned result")
            download_choice = st.radio("Format:", ["PDF (all pages)", "ZIP of PNG images"], horizontal=True)
            if download_choice.startswith("PDF"):
                pdf_buffer = images_to_pdf_bytes(processed_pages)
                st.download_button("Download PDF", data=pdf_buffer,
                                   file_name="cleaned_form.pdf", mime="application/pdf")
            else:
                zip_buffer = create_zip_of_images(processed_pages)
                st.download_button("Download ZIP", data=zip_buffer,
                                   file_name="cleaned_pages.zip", mime="application/zip")
    else:
        # Image processing
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img_bgr is None:
            st.error("❌ Could not read the image. Please try a different file.")
        else:
            processed = keep_only_black(img_bgr, threshold, make_transparent=transparent_bg)

            # Display
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original")
                st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)
            with col2:
                st.subheader("Filtered (only black text)")
                if transparent_bg:
                    st.image(Image.fromarray(processed, "RGBA"), use_container_width=True)
                else:
                    st.image(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB), use_container_width=True)

            # Download
            if transparent_bg:
                success, encoded = cv2.imencode(".png", cv2.cvtColor(processed, cv2.COLOR_RGBA2BGRA))
                mime = "image/png"
                ext = "png"
            else:
                output_format = st.radio("Output format:", ["PNG", "JPEG"], horizontal=True)
                if output_format == "PNG":
                    success, encoded = cv2.imencode(".png", processed)
                    mime = "image/png"
                    ext = "png"
                else:
                    success, encoded = cv2.imencode(".jpg", processed, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    mime = "image/jpeg"
                    ext = "jpg"

            if success:
                st.download_button("📥 Download cleaned image", data=encoded.tobytes(),
                                   file_name=f"clean_form.{ext}", mime=mime)
            else:
                st.error("Error encoding image.")

else:
    # Empty state
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-top: 2rem;">
        <div style="text-align: center; max-width: 400px;">
            <h3>✨ Simple & Fast</h3>
            <p style="color: #666;">Upload a scanned form, adjust the threshold, and download a perfectly clean document in seconds.</p>
            <p style="color: #999; font-size: 0.9rem;">Supports JPG, PNG, TIFF, BMP, and multi-page PDFs.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">Built with Streamlit • OpenCV • PyMuPDF</div>', unsafe_allow_html=True)