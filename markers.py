"""
Set-of-Marks implementation: find interactive elements and draw markers.
"""

import io
from dataclasses import dataclass
from typing import List

from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import Page

from config import get_config


@dataclass
class Element:
    """Interactive element on page."""

    index: int
    selector: str
    tag: str
    text: str
    x: int  # center x
    y: int  # center y
    width: int
    height: int

    def __str__(self) -> str:
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"[{self.index}] <{self.tag}> {text_preview}"


# JavaScript to find all interactive elements
FIND_ELEMENTS_JS = """
() => {
    const selectors = [
        'a[href]',
        'button',
        'input:not([type="hidden"])',
        'textarea',
        'select',
        '[role="button"]',
        '[role="link"]',
        '[role="menuitem"]',
        '[role="tab"]',
        '[role="checkbox"]',
        '[role="radio"]',
        '[onclick]',
        '[tabindex]:not([tabindex="-1"])',
        'label[for]',
        '[contenteditable="true"]'
    ];

    const elements = [];
    const seen = new Set();

    for (const selector of selectors) {
        for (const el of document.querySelectorAll(selector)) {
            // Skip if already processed
            if (seen.has(el)) continue;
            seen.add(el);

            // Skip hidden elements
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                continue;
            }

            // Get bounding box
            const rect = el.getBoundingClientRect();

            // Skip elements outside viewport or too small
            if (rect.width < 5 || rect.height < 5) continue;
            if (rect.bottom < 0 || rect.top > window.innerHeight) continue;
            if (rect.right < 0 || rect.left > window.innerWidth) continue;

            // Get text content
            let text = '';
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                text = el.placeholder || el.value || el.getAttribute('aria-label') || '';
            } else if (el.tagName === 'SELECT') {
                text = el.options[el.selectedIndex]?.text || el.getAttribute('aria-label') || '';
            } else {
                text = el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '';
            }
            text = text.trim().replace(/\\s+/g, ' ').substring(0, 100);

            // Build unique selector
            let selector = '';
            if (el.id) {
                selector = `#${el.id}`;
            } else {
                const tag = el.tagName.toLowerCase();
                const classes = Array.from(el.classList).slice(0, 2).join('.');
                selector = classes ? `${tag}.${classes}` : tag;

                // Add text or aria-label for uniqueness
                if (el.getAttribute('aria-label')) {
                    selector += `[aria-label="${el.getAttribute('aria-label').substring(0, 50)}"]`;
                } else if (text && text.length < 30) {
                    // Use text content for links/buttons
                    if (tag === 'a' || tag === 'button') {
                        selector = `${tag}:has-text("${text.substring(0, 30)}")`;
                    }
                }
            }

            elements.push({
                selector: selector,
                tag: el.tagName.toLowerCase(),
                text: text,
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                top: Math.round(rect.top),
                left: Math.round(rect.left)
            });
        }
    }

    // Sort by position (top to bottom, left to right)
    elements.sort((a, b) => {
        const rowDiff = Math.floor(a.top / 50) - Math.floor(b.top / 50);
        if (rowDiff !== 0) return rowDiff;
        return a.left - b.left;
    });

    return elements;
}
"""


async def get_interactive_elements(page: Page) -> List[Element]:
    """Find all interactive elements on the page."""
    raw_elements = await page.evaluate(FIND_ELEMENTS_JS)

    elements = []
    for i, el in enumerate(raw_elements):
        elements.append(
            Element(
                index=i + 1,  # 1-based indexing for human readability
                selector=el["selector"],
                tag=el["tag"],
                text=el["text"],
                x=el["x"],
                y=el["y"],
                width=el["width"],
                height=el["height"],
            )
        )

    return elements


def draw_markers(screenshot_bytes: bytes, elements: List[Element]) -> bytes:
    """Draw numbered markers on screenshot for each element."""
    config = get_config()

    # Open screenshot
    image = Image.open(io.BytesIO(screenshot_bytes))
    draw = ImageDraw.Draw(image)

    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", config.marker_font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config.marker_font_size)
        except OSError:
            font = ImageFont.load_default()

    # Colors
    bg_color = (255, 0, 0)  # Red background
    text_color = (255, 255, 255)  # White text
    border_color = (139, 0, 0)  # Dark red border

    for el in elements:
        label = str(el.index)

        # Calculate label size
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = config.marker_padding

        # Position marker at top-left of element
        marker_x = max(0, el.x - el.width // 2 - 5)
        marker_y = max(0, el.y - el.height // 2 - 5)

        # Draw background rectangle
        rect_x1 = marker_x
        rect_y1 = marker_y
        rect_x2 = marker_x + text_width + padding * 2 + 4
        rect_y2 = marker_y + text_height + padding * 2

        # Draw border
        draw.rectangle([rect_x1 - 1, rect_y1 - 1, rect_x2 + 1, rect_y2 + 1], fill=border_color)
        # Draw background
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=bg_color)
        # Draw text
        draw.text((marker_x + padding + 2, marker_y + padding - 2), label, fill=text_color, font=font)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=config.screenshot_quality)
    return output.getvalue()


def elements_to_text(elements: List[Element]) -> str:
    """Convert elements list to text description."""
    if not elements:
        return "No interactive elements found on page."

    lines = ["Interactive elements on page:"]
    for el in elements:
        lines.append(str(el))

    return "\n".join(lines)
