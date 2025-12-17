"""
Browser actions: click, type, scroll, goto, etc.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from markers import Element


@dataclass
class ActionResult:
    """Result of executing an action."""

    success: bool
    message: str
    error: Optional[str] = None


async def execute_action(
    page: Page,
    action: Dict[str, Any],
    elements: List[Element],
) -> ActionResult:
    """
    Execute an action on the page.

    Args:
        page: Playwright page
        action: Action dict from Claude
        elements: List of interactive elements

    Returns:
        ActionResult with success status and message
    """
    action_type = action.get("action", "unknown")

    try:
        if action_type == "goto":
            return await action_goto(page, action.get("url", ""))

        elif action_type == "click":
            element_idx = action.get("element")
            return await action_click(page, element_idx, elements)

        elif action_type == "type":
            element_idx = action.get("element")
            text = action.get("text", "")
            return await action_type_text(page, element_idx, text, elements)

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            return await action_scroll(page, direction)

        elif action_type == "wait":
            return await action_wait(page)

        elif action_type == "press":
            key = action.get("key", "Enter")
            return await action_press_key(page, key)

        elif action_type == "done":
            result = action.get("result", "Task completed")
            return ActionResult(success=True, message=f"Done: {result}")

        elif action_type == "ask":
            question = action.get("question", "Need more information")
            return ActionResult(success=True, message=f"Question: {question}")

        elif action_type == "error":
            return ActionResult(success=False, message="Error", error=action.get("error"))

        else:
            return ActionResult(
                success=False,
                message=f"Unknown action: {action_type}",
                error=f"Unknown action type: {action_type}",
            )

    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Action failed: {action_type}",
            error=str(e),
        )


async def action_goto(page: Page, url: str) -> ActionResult:
    """Navigate to URL."""
    if not url:
        return ActionResult(success=False, message="No URL provided", error="URL is empty")

    # Ensure URL has protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)  # Wait for JS to initialize
        return ActionResult(success=True, message=f"Navigated to {url}")
    except PlaywrightTimeout:
        return ActionResult(success=True, message=f"Navigated to {url} (timeout waiting for full load)")
    except Exception as e:
        return ActionResult(success=False, message=f"Failed to navigate to {url}", error=str(e))


async def action_click(page: Page, element_idx: int, elements: List[Element]) -> ActionResult:
    """Click on element by index."""
    if element_idx is None:
        return ActionResult(success=False, message="No element specified", error="Element index is None")

    # Find element
    element = None
    for el in elements:
        if el.index == element_idx:
            element = el
            break

    if not element:
        return ActionResult(
            success=False,
            message=f"Element [{element_idx}] not found",
            error=f"Element with index {element_idx} not in elements list (have {len(elements)} elements)",
        )

    try:
        # Try clicking by coordinates first (more reliable with markers)
        await page.mouse.click(element.x, element.y)
        await page.wait_for_timeout(500)
        return ActionResult(success=True, message=f"Clicked element [{element_idx}]: {element.text[:30] if element.text else element.tag}")
    except Exception as e:
        # Fallback to selector
        try:
            await page.click(element.selector, timeout=5000)
            await page.wait_for_timeout(500)
            return ActionResult(success=True, message=f"Clicked element [{element_idx}] via selector")
        except Exception as e2:
            return ActionResult(
                success=False,
                message=f"Failed to click element [{element_idx}]",
                error=f"Click failed: {e}, Selector fallback: {e2}",
            )


async def action_type_text(
    page: Page, element_idx: int, text: str, elements: List[Element]
) -> ActionResult:
    """Type text into element."""
    if element_idx is None:
        return ActionResult(success=False, message="No element specified", error="Element index is None")

    if not text:
        return ActionResult(success=False, message="No text to type", error="Text is empty")

    # Find element
    element = None
    for el in elements:
        if el.index == element_idx:
            element = el
            break

    if not element:
        return ActionResult(
            success=False,
            message=f"Element [{element_idx}] not found",
            error=f"Element with index {element_idx} not in elements list",
        )

    try:
        # Click to focus first
        await page.mouse.click(element.x, element.y)
        await page.wait_for_timeout(200)

        # Clear existing text and type new
        await page.keyboard.press("Control+a")
        await page.keyboard.type(text, delay=50)

        return ActionResult(success=True, message=f"Typed '{text}' into element [{element_idx}]")
    except Exception as e:
        # Fallback to selector
        try:
            await page.fill(element.selector, text, timeout=5000)
            return ActionResult(success=True, message=f"Typed '{text}' into element [{element_idx}] via selector")
        except Exception as e2:
            return ActionResult(
                success=False,
                message=f"Failed to type into element [{element_idx}]",
                error=f"Type failed: {e}, Selector fallback: {e2}",
            )


async def action_scroll(page: Page, direction: str = "down") -> ActionResult:
    """Scroll the page."""
    try:
        if direction == "down":
            await page.mouse.wheel(0, 500)
        elif direction == "up":
            await page.mouse.wheel(0, -500)
        elif direction == "left":
            await page.mouse.wheel(-500, 0)
        elif direction == "right":
            await page.mouse.wheel(500, 0)
        else:
            await page.mouse.wheel(0, 500)  # Default down

        await page.wait_for_timeout(500)
        return ActionResult(success=True, message=f"Scrolled {direction}")
    except Exception as e:
        return ActionResult(success=False, message=f"Failed to scroll {direction}", error=str(e))


async def action_wait(page: Page) -> ActionResult:
    """Wait for page to load."""
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeout:
        pass  # Timeout is ok, page might have continuous loading

    await page.wait_for_timeout(1000)
    return ActionResult(success=True, message="Waited for page load")


async def action_press_key(page: Page, key: str = "Enter") -> ActionResult:
    """Press a keyboard key."""
    try:
        await page.keyboard.press(key)
        await page.wait_for_timeout(500)
        return ActionResult(success=True, message=f"Pressed {key}")
    except Exception as e:
        return ActionResult(success=False, message=f"Failed to press {key}", error=str(e))


async def press_enter(page: Page) -> ActionResult:
    """Press Enter key (convenience function)."""
    return await action_press_key(page, "Enter")
