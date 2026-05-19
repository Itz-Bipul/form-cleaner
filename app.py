#!/usr/bin/env python3
"""
Single‑file Streamlit dashboard to keep only black text from scanned forms.
Supports images (PNG, JPG, TIFF, BMP) and multi‑page PDFs.

Dependencies (install with pip):
    streamlit opencv-python-headless numpy Pillow PyMuPDF
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO
import zipfile


# ============================================================
# 1. Core filtering function (keep only black/near‑black pixels)
# ============================================================
def keep_only_black(img_bgr, threshold=50, make_transparent=False):
    """
    Keep only black (or near‑black) pixels. Everything else becomes white or transparent.

    Args:
        img_bgr:          BGR image as numpy array
        threshold:        Grayscale value (0–255). Pixels darker than this are kept.
        make_transparent: If True, return RGBA with transparent background.

    Returns:
        Processed image (BGR or BGRA)
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    mask = gray <= threshold

    if make_transparent:
        h, w = img_bgr.shape[:2]
        out = np.zeros((h, w, 4), dtype=np.uint8)
        out[mask] = [0, 0, 0, 255]          # black, opaque
        return out
    else:
        out = np.full_like(img_bgr, 255)    # white
        out[mask] = [0, 0, 0]               # black
        return out


# ============================================================
# 2. PDF utilities (convert PDF to images and back)
# ============================================================
def pdf_to_images(pdf_bytes):
    """Convert PDF bytes → list of BGR numpy arrays (one per page)."""
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
    """Convert list of BGR images → PDF bytes (in memory)."""
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
    """Create a ZIP file containing each image as a separate file."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(images):
            ret, encoded = cv2.imencode(f".{format.lower()}", img)
            if ret:
                zf.writestr(f"page_{i+1}.{format.lower()}", encoded.tobytes())
    zip_buffer.seek(0)
    return zip_buffer


# ============================================================
# 3. Streamlit user interface
# ============================================================
st.set_page_config(page_title="Form Colour Filter", layout="wide")
st.title("📝 Keep Only Black Text – Form Cleaner (Image & PDF)")
st.markdown(
    "Upload a scanned form (image or PDF), adjust the black threshold, "
    "and download the result with only black text remaining."
)

# Sidebar controls
st.sidebar.header("⚙️ Settings")
threshold = st.sidebar.slider(
    "Black threshold",
    0, 255, 50, 5,
    help="Pixels darker than this value are kept as black. Lower = stricter 'black only'."
)
transparent_bg = st.sidebar.checkbox(
    "Transparent background (images only)",
    False,
    help="If checked, the background becomes transparent (PNG only, not for PDF)."
)

# File uploader – accepts images and PDF
uploaded_file = st.file_uploader(
    "Choose an image or PDF",
    type=["png", "jpg", "jpeg", "tiff", "bmp", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        # ------------------------------------------------------------
        # PDF processing
        # ------------------------------------------------------------
        st.subheader("PDF processing")
        with st.spinner("Converting PDF pages to images..."):
            pdf_bytes = uploaded_file.read()
            pages_bgr = pdf_to_images(pdf_bytes)
        st.success(f"Loaded {len(pages_bgr)} page(s).")

        if not pages_bgr:
            st.error("Could not read any pages from the PDF.")
        else:
            # Process all pages
            processed_pages = []
            progress_bar = st.progress(0)
            for i, page in enumerate(pages_bgr):
                processed = keep_only_black(page, threshold, make_transparent=False)
                processed_pages.append(processed)
                progress_bar.progress((i + 1) / len(pages_bgr))

            # Preview first page
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original (page 1)")
                st.image(cv2.cvtColor(pages_bgr[0], cv2.COLOR_BGR2RGB), use_container_width=True)
            with col2:
                st.subheader("Filtered (page 1)")
                st.image(cv2.cvtColor(processed_pages[0], cv2.COLOR_BGR2RGB), use_container_width=True)

            # Download options
            st.subheader("Download")
            download_option = st.radio(
                "Output format:",
                ("PDF (all pages)", "ZIP of images (PNG)"),
                index=0
            )

            if download_option.startswith("PDF"):
                pdf_buffer = images_to_pdf_bytes(processed_pages)
                st.download_button(
                    label="📥 Download cleaned PDF",
                    data=pdf_buffer,
                    file_name="cleaned_form.pdf",
                    mime="application/pdf"
                )
            else:
                zip_buffer = create_zip_of_images(processed_pages, format="PNG")
                st.download_button(
                    label="📥 Download ZIP of images",
                    data=zip_buffer,
                    file_name="cleaned_pages.zip",
                    mime="application/zip"
                )

    else:
        # ------------------------------------------------------------
        # Single image processing
        # ------------------------------------------------------------
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img_bgr is None:
            st.error("Could not read the image. Please try a different file.")
        else:
            processed = keep_only_black(img_bgr, threshold, make_transparent=transparent_bg)

            # Display
            if transparent_bg:
                display_img = Image.fromarray(processed, "RGBA")
            else:
                display_img = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
            original_display = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original")
                st.image(original_display, use_container_width=True)
            with col2:
                st.subheader("Filtered (only black text)")
                st.image(display_img, use_container_width=True)

            # Download
            if transparent_bg:
                success, encoded = cv2.imencode(".png", cv2.cvtColor(processed, cv2.COLOR_RGBA2BGRA))
                mime = "image/png"
                download_ext = "png"
            else:
                output_format = st.sidebar.selectbox(
                    "Output format", ["PNG", "JPEG"], index=0, disabled=transparent_bg
                )
                if output_format == "PNG":
                    success, encoded = cv2.imencode(".png", processed)
                    mime = "image/png"
                    download_ext = "png"
                else:
                    success, encoded = cv2.imencode(".jpg", processed, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    mime = "image/jpeg"
                    download_ext = "jpg"

            if success:
                st.download_button(
                    label="📥 Download filtered image",
                    data=encoded.tobytes(),
                    file_name=f"clean_form.{download_ext}",
                    mime=mime
                )
            else:
                st.error("Error encoding image for download.")
else:
    st.info("👆 Upload an image or PDF to get started.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit, OpenCV & PyMuPDF")