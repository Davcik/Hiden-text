"""
Created on Mon Aug 25 13:46:31 2025

@author: davcik
"""

# pip install PyMuPDF
import fitz  # PyMuPDF
from typing import List, Tuple, Dict, Any

def is_invisible_render_mode(span: Dict[str, Any]) -> bool:
    """
    Detect invisible text via PDF text rendering mode.
    PyMuPDF exposes 'render_mode' for spans in get_text('rawdict') / 'dict' in recent versions.
    Mode 3 = invisible (per PDF spec text rendering modes). 
    """
    rm = span.get("render_mode")
    return rm == 3  # 3 = invisible

def is_fully_transparent(span: Dict[str, Any]) -> bool:
    """
    Consider text non-visible if fill opacity is zero (alpha == 0).
    Some PDFs may expose 'alpha' or 'opacity' per span; if absent, fall back to color-only logic.
    """
    # PyMuPDF spans commonly have 'color' (RGB int) and sometimes 'alpha', depending on version.
    alpha = span.get("alpha")
    fill_opacity = span.get("opacity")  # alternative key if present
    if isinstance(alpha, (int, float)) and alpha == 0:
        return True  # fully transparent fill 
    if isinstance(fill_opacity, (int, float)) and fill_opacity == 0:
        return True  # fully transparent fill 
    return False

def is_white_on_white(span: Dict[str, Any], page_bg_rgb: Tuple[int, int, int] = (255, 255, 255)) -> bool:
    """
    Heuristic: White text on a white background is likely not visible.
    This is imperfect because true background may be images or shapes.
    """
    color_int = span.get("color")
    if color_int is None:
        return False
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b) == page_bg_rgb  # white by default

def extract_hidden_text_spans(pdf_path: str) -> List[Tuple[int, Dict[str, Any]]]:
    """
    Return list of (page_number, span_dict) for spans likely 'hidden'.
    """
    hidden = []
    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            # Use 'rawdict' to retain low-level span info including render mode, flags, color, etc.
            data = page.get_text("rawdict")
            for block in data.get("blocks", []):
                if block.get("type") != 0:  # text blocks only
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        rm_hidden = is_invisible_render_mode(span)  
                        alpha_hidden = is_fully_transparent(span)   # alpha/opacity 0 
                        white_hidden = is_white_on_white(span)      # heuristic
                        if rm_hidden or alpha_hidden or white_hidden:
                            hidden.append((page_index + 1, span))
    return hidden

def print_hidden_text(pdf_path: str) -> None:
    hidden_spans = extract_hidden_text_spans(pdf_path)
    if not hidden_spans:
        print("No likely hidden text spans detected.")
        return
    for page_no, span in hidden_spans:
        text = span.get("text", "")
        rm = span.get("render_mode")
        color_int = span.get("color")
        color_hex = f"#{color_int:06x}" if isinstance(color_int, int) else "N/A"
        size = span.get("size")
        font = span.get("font")
        print(f"[Page {page_no}] Hidden text candidate: {text!r} | render_mode={rm} | color={color_hex} | size={size} | font={font}")

# Example usage:
# print_hidden_text(r"C:\Users\USER\Desktop\YOURFILE.pdf")