#!/usr/bin/env python3
"""
extract_report_photos.py
------------------------
Standalone script that extracts photos and their descriptions from
Innovative Plant Consulting (IPC) QA Photo Inspection Report PDFs.

Each PDF page has a 2×2 grid of photos (fewer on the last page).
The description text for each photo appears directly below it.

Usage
-----
Process all reports in the default folder:
    python extract_report_photos.py

Process a single report:
    python extract_report_photos.py --report 33

Custom source / output paths:
    python extract_report_photos.py \
        --source "C:\\path\\to\\pdfs" \
        --output "C:\\path\\to\\output"

Requirements
------------
    python -m pip install PyMuPDF
"""

import argparse
import os
import re
import sys

# ---------------------------------------------------------------------------
# Attempt to import PyMuPDF (fitz).  Give a helpful message if missing.
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
except ImportError:
    print(
        "\n[ERROR] PyMuPDF is not installed.  Run:\n"
        "    python -m pip install PyMuPDF\n"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------

DEFAULT_SOURCE = (
    r"C:\Users\lukep\OneDrive\Desktop\2.16.2026 Transfer"
    r"\TVA Barkley 2nd Half\Pictures\All Photo Reports\PDFs"
)

PDF_GLOB_PATTERN = "IPC QA Photo Inspection Report-*.pdf"

# Header / footer text to ignore when searching for descriptions
HEADER_STRINGS = {
    "INNOVATIVE PLANT CONSULTING",
    "DRIVING INSPECTION FORWARD",
}

# Substrings that, if found in a matched description, indicate the text is
# header content that leaked through (e.g. a partial line from the IPC banner).
HEADER_SUBSTRINGS = ("INNOVATIVE", "PLANT CONSULTING", "DRIVING INSPECTION")

# Images smaller than these thresholds are considered logos / decorations.
# Real weld photos are large; IPC circular logos are small.
# Use OR logic: skip if width < threshold OR height < threshold.
MIN_IMAGE_WIDTH = 200   # pixels
MIN_IMAGE_HEIGHT = 200  # pixels
MIN_IMAGE_BYTES = 5_000  # 5 KB — logos are typically well under this

# The IPC header occupies roughly the top 12% of each page.
# Any image whose vertical centre falls in this region is a logo.
HEADER_REGION_FRACTION = 0.12

# Characters not allowed in Windows filenames
WIN_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')

# ANSI colour helpers (fall back gracefully on Windows without VT100)
def _ansi(code: str) -> str:
    """Return the ANSI escape sequence if stdout is a TTY, else empty string."""
    if sys.stdout.isatty():
        return f"\033[{code}m"
    return ""


RESET  = _ansi("0")
BOLD   = _ansi("1")
GREEN  = _ansi("32")
YELLOW = _ansi("33")
CYAN   = _ansi("36")
RED    = _ansi("31")
MAGENTA = _ansi("35")


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------

def sanitize_filename(text: str) -> str:
    """
    Make *text* safe to use as a Windows filename.

    • Replace inch-mark characters (") and foot-mark (') with 'in' / 'ft'.
      These characters are common measurement marks in structural inspection
      descriptions (e.g. '12"' for 12 inches) and are not allowed in Windows
      filenames.
    • Replace all other Windows-forbidden characters with underscores.
    • Collapse multiple underscores / spaces.
    • Strip leading / trailing whitespace and dots.
    """
    # Replace inch / foot marks first so they become readable tokens.
    # In IPC inspection descriptions, " always denotes inches and ' denotes feet.
    text = text.replace('"', "in").replace("\u201c", "in").replace("\u201d", "in")
    text = text.replace("'", "ft").replace("\u2018", "ft").replace("\u2019", "ft")

    # Replace remaining forbidden characters with underscores
    text = WIN_INVALID_CHARS.sub("_", text)

    # Collapse consecutive underscores
    text = re.sub(r"_+", "_", text)

    # Strip boundary characters
    text = text.strip(" _.")

    # Truncate to a sane length (Windows MAX_PATH minus some overhead)
    max_len = 180
    if len(text) > max_len:
        text = text[:max_len].rstrip(" _.")

    return text or "UNNAMED"


def unique_filename(folder: str, base_name: str, ext: str = ".jpg") -> str:
    """
    Return a filename (without folder) that does not already exist in *folder*.
    Appends ' (2)', ' (3)' etc. when the base name is already taken.
    """
    candidate = base_name + ext
    if not os.path.exists(os.path.join(folder, candidate)):
        return candidate

    counter = 2
    while True:
        candidate = f"{base_name} ({counter}){ext}"
        if not os.path.exists(os.path.join(folder, candidate)):
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# Per-page extraction
# ---------------------------------------------------------------------------

def is_header_or_footer_text(text: str) -> bool:
    """Return True if *text* belongs to the page header or footer."""
    stripped = text.strip().upper()
    if stripped in HEADER_STRINGS:
        return True
    # Footer pattern: "Page N of M"
    if re.fullmatch(r"PAGE\s+\d+\s+OF\s+\d+", stripped):
        return True
    return False


def extract_page_photos(page: "fitz.Page") -> list[dict]:
    """
    Extract photos and their matched description strings from a single page.

    Returns a list of dicts:
        {"image_bytes": bytes, "description": str, "page_num": int}
    ordered top-left → top-right → bottom-left → bottom-right.
    """
    page_rect = page.rect
    page_width = page_rect.width

    # ------------------------------------------------------------------
    # 1. Collect images that are large enough to be real photos
    # ------------------------------------------------------------------
    raw_images = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            base_image = page.parent.extract_image(xref)
        except Exception:
            continue

        img_bytes = base_image.get("image", b"")
        img_width = base_image.get("width", 0)
        img_height = base_image.get("height", 0)

        # Skip small images using OR logic — either dimension or byte size too small.
        if img_width < MIN_IMAGE_WIDTH or img_height < MIN_IMAGE_HEIGHT:
            continue
        if len(img_bytes) < MIN_IMAGE_BYTES:
            continue

        # Find the bounding rect of this image on the page.
        # get_image_rects() returns a list of Rect objects in current PyMuPDF
        # versions; older builds may wrap the Rect in a namedtuple with a .rect
        # attribute.  Handle both shapes.
        rects = page.get_image_rects(xref)
        if not rects:
            continue

        # Use the first (largest / most prominent) occurrence
        rect = rects[0]
        if hasattr(rect, "rect"):
            # Older PyMuPDF wraps the Rect in an object with a .rect attribute
            rect = rect.rect

        # Skip images whose vertical centre falls in the header region.
        # The IPC header (logos + title) occupies roughly the top 12% of the page.
        img_center_y = (rect.y0 + rect.y1) / 2
        if img_center_y < page_rect.height * HEADER_REGION_FRACTION:
            continue

        raw_images.append(
            {
                "xref": xref,
                "bytes": img_bytes,
                "ext": base_image.get("ext", "jpg"),
                "rect": rect,
                "width": img_width,
                "height": img_height,
            }
        )

    if not raw_images:
        return []

    # ------------------------------------------------------------------
    # 2. Safety cap: never more than 4 weld photos per page.
    #    If more images slipped through, keep only the 4 largest by area.
    # ------------------------------------------------------------------
    if len(raw_images) > 4:
        raw_images.sort(key=lambda i: i["width"] * i["height"], reverse=True)
        raw_images = raw_images[:4]

    # ------------------------------------------------------------------
    # 3. Sort images top-to-bottom, left-to-right
    # ------------------------------------------------------------------
    raw_images.sort(key=lambda i: (round(i["rect"].y0 / 50) * 50, i["rect"].x0))

    # ------------------------------------------------------------------
    # 4. Collect text lines, skip header / footer
    #
    # We use get_text("dict") rather than get_text("blocks") so that text
    # spanning the same vertical position in different columns (e.g. the
    # left and right photo descriptions on one page row) are kept as
    # separate entries with their correct individual x-positions.
    # ------------------------------------------------------------------
    text_blocks = []
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # 0 = text block
            continue
        for line in block.get("lines", []):
            # Reconstruct the line text from its spans
            raw_text = "".join(s["text"] for s in line.get("spans", [])).strip()
            if not raw_text:
                continue
            if is_header_or_footer_text(raw_text):
                continue

            bbox = line["bbox"]  # (x0, y0, x1, y1)
            text_blocks.append(
                {
                    "text": raw_text,
                    "x0": bbox[0],
                    "y0": bbox[1],
                    "x1": bbox[2],
                    "y1": bbox[3],
                    "cx": (bbox[0] + bbox[2]) / 2,
                }
            )

    # ------------------------------------------------------------------
    # 5. Match each image to the closest text block below it
    # ------------------------------------------------------------------
    results = []
    used_text_indices: set[int] = set()

    for img in raw_images:
        img_rect = img["rect"]
        img_cx = (img_rect.x0 + img_rect.x1) / 2
        img_bottom = img_rect.y1

        # Tolerance: text centre must be within half the page width of the
        # image centre (generous enough for a 2-column layout)
        x_tolerance = page_width / 2.5

        best_idx = None
        best_dist = float("inf")

        for idx, tb in enumerate(text_blocks):
            if idx in used_text_indices:
                continue
            # Must be below the image
            if tb["y0"] < img_bottom - 5:
                continue
            # Must be horizontally close
            if abs(tb["cx"] - img_cx) > x_tolerance:
                continue

            dist = tb["y0"] - img_bottom
            if dist < best_dist:
                best_dist = dist
                best_idx = idx

        if best_idx is not None:
            used_text_indices.add(best_idx)
            description = text_blocks[best_idx]["text"].replace("\n", " ").strip()
            # Sanity-check: if the matched text is header content that leaked
            # through, discard it so the caller generates an UNKNOWN_* name.
            desc_upper = description.upper()
            if any(phrase in desc_upper for phrase in HEADER_SUBSTRINGS):
                description = ""
        else:
            description = ""  # caller will create an UNKNOWN_* name

        results.append(
            {
                "bytes": img["bytes"],
                "ext": img["ext"],
                "description": description,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Per-PDF processing
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: str, output_folder: str, report_num: str) -> dict:
    """
    Process a single PDF and save extracted photos to *output_folder*.

    Returns a summary dict:
        {"report": str, "extracted": int, "warnings": int, "errors": list[str]}
    """
    summary = {"report": report_num, "extracted": 0, "warnings": 0, "errors": []}

    print(
        f"\n{BOLD}{CYAN}Processing: {os.path.basename(pdf_path)}{RESET}"
    )
    print(f"  Output folder: {output_folder}")

    os.makedirs(output_folder, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        msg = f"  {RED}[ERROR]{RESET} Could not open PDF: {exc}"
        print(msg)
        summary["errors"].append(str(exc))
        return summary

    total_pages = len(doc)

    # Track per-page image indices for UNKNOWN fallback names
    global_img_counter = 0

    for page_index in range(total_pages):
        page = doc[page_index]
        page_num = page_index + 1

        try:
            photos = extract_page_photos(page)
        except Exception as exc:
            warn = f"  {YELLOW}[WARN]{RESET} Page {page_num}: extraction error — {exc}"
            print(warn)
            summary["warnings"] += 1
            continue

        extracted_this_page = 0

        for img_data in photos:
            global_img_counter += 1
            description = img_data["description"]

            if description:
                base_name = sanitize_filename(description)
            else:
                base_name = f"UNKNOWN_Page{page_num}_Img{global_img_counter}"
                print(
                    f"  {YELLOW}[WARN]{RESET} Page {page_num}: "
                    f"no description found for image {global_img_counter} — "
                    f"saving as {base_name}.jpg"
                )
                summary["warnings"] += 1

            filename = unique_filename(output_folder, base_name, ".jpg")
            out_path = os.path.join(output_folder, filename)

            try:
                with open(out_path, "wb") as fh:
                    fh.write(img_data["bytes"])
                summary["extracted"] += 1
                extracted_this_page += 1
            except OSError as exc:
                # Very long filenames or other OS errors
                fallback = f"UNKNOWN_Page{page_num}_Img{global_img_counter}"
                fallback_file = unique_filename(output_folder, fallback, ".jpg")
                try:
                    with open(os.path.join(output_folder, fallback_file), "wb") as fh:
                        fh.write(img_data["bytes"])
                    summary["extracted"] += 1
                    extracted_this_page += 1
                    print(
                        f"  {YELLOW}[WARN]{RESET} Page {page_num}: "
                        f"saved as fallback name due to OS error: {exc}"
                    )
                    summary["warnings"] += 1
                except Exception as exc2:
                    print(
                        f"  {RED}[ERROR]{RESET} Page {page_num}: "
                        f"could not save image — {exc2}"
                    )
                    summary["errors"].append(str(exc2))

        status = f"{GREEN}✓{RESET}" if extracted_this_page > 0 else f"{YELLOW}(no photos){RESET}"
        print(
            f"  Page {page_num}/{total_pages}: "
            f"Extracted {extracted_this_page} photo(s) {status}"
        )

    doc.close()

    status_icon = f"{GREEN}✅{RESET}" if not summary["errors"] else f"{RED}❌{RESET}"
    print(
        f"  {status_icon} Report {report_num} complete: "
        f"{summary['extracted']} photos extracted"
    )
    return summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract photos from IPC QA Photo Inspection Report PDFs "
            "and save them as JPEG files named after their descriptions."
        )
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Folder containing the PDF reports (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Root folder for output subfolders. "
            "Defaults to the same location as --source."
        ),
    )
    parser.add_argument(
        "--report",
        default=None,
        metavar="NUMBER",
        help=(
            "Process only the report with this number "
            "(e.g., --report 33).  "
            "Omit to process all reports."
        ),
    )
    args = parser.parse_args()

    source_folder = args.source
    output_root = args.output or source_folder
    target_report = args.report

    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------
    print(
        f"\n{BOLD}{CYAN}"
        "╔══════════════════════════════════════════════════════╗\n"
        "║   IPC Photo Report Extractor — TVA Barkley Dam      ║\n"
        "╚══════════════════════════════════════════════════════╝"
        f"{RESET}"
    )

    # ------------------------------------------------------------------
    # Locate PDFs
    # ------------------------------------------------------------------
    if not os.path.isdir(source_folder):
        print(
            f"\n{RED}[ERROR]{RESET} Source folder not found:\n"
            f"  {source_folder}\n"
            "Use --source to specify the correct path."
        )
        sys.exit(1)

    all_files = sorted(os.listdir(source_folder))

    # Match "IPC QA Photo Inspection Report-<NUMBER>.pdf"
    pdf_pattern = re.compile(
        r"^IPC QA Photo Inspection Report-(\d+)\.pdf$", re.IGNORECASE
    )

    pdfs: list[tuple[str, str]] = []  # list of (full_path, report_number)
    for fname in all_files:
        m = pdf_pattern.match(fname)
        if m:
            rnum = m.group(1)
            if target_report and rnum != target_report:
                continue
            pdfs.append((os.path.join(source_folder, fname), rnum))

    if not pdfs:
        if target_report:
            print(
                f"\n{YELLOW}[WARN]{RESET} No PDF found for report {target_report} "
                f"in:\n  {source_folder}"
            )
        else:
            print(
                f"\n{YELLOW}[WARN]{RESET} No matching PDFs found in:\n"
                f"  {source_folder}\n"
                f"  (expected names like 'IPC QA Photo Inspection Report-33.pdf')"
            )
        sys.exit(0)

    print(f"\nFound {BOLD}{len(pdfs)}{RESET} PDF report(s) in source folder.")

    # ------------------------------------------------------------------
    # Process each PDF
    # ------------------------------------------------------------------
    summaries: list[dict] = []
    for pdf_path, rnum in pdfs:
        out_folder = os.path.join(output_root, f"Report-{rnum} Photos")
        summary = process_pdf(pdf_path, out_folder, rnum)
        summaries.append(summary)

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    total_extracted = sum(s["extracted"] for s in summaries)
    total_warnings = sum(s["warnings"] for s in summaries)
    total_errors = sum(len(s["errors"]) for s in summaries)

    print(
        f"\n{BOLD}"
        "═══════════════════════════════════════════════════════\n"
        "SUMMARY\n"
        "═══════════════════════════════════════════════════════"
        f"{RESET}"
    )

    for s in summaries:
        icon = f"{GREEN}✅{RESET}" if not s["errors"] else f"{RED}❌{RESET}"
        warn_note = (
            f"  {YELLOW}({s['warnings']} warnings){RESET}"
            if s["warnings"]
            else ""
        )
        print(f"  Report {s['report']}: {s['extracted']} photos {icon}{warn_note}")

    print(f"  {'─' * 25}")
    print(f"  {BOLD}Total: {total_extracted:,} photos extracted{RESET}")

    if total_warnings:
        print(f"  {YELLOW}Warnings: {total_warnings}{RESET}")
    else:
        print(f"  {GREEN}Warnings: 0{RESET}")

    if total_errors:
        print(f"  {RED}Errors:   {total_errors}{RESET}")

    print(
        f"{BOLD}"
        "═══════════════════════════════════════════════════════"
        f"{RESET}\n"
    )


if __name__ == "__main__":
    main()
