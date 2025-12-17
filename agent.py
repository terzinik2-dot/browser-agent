"""
Main Browser Agent loop.
"""

from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from browser import create_browser
from config import get_config
from markers import get_interactive_elements, draw_markers, elements_to_text
from tools import execute_action, ActionResult
from vision import VisionClient, encode_image


console = Console()


class BrowserAgent:
    """AI agent that controls browser to complete tasks."""

    def __init__(self, on_ask: Optional[Callable[[str], str]] = None):
        """
        Initialize agent.

        Args:
            on_ask: Callback function when agent needs to ask user a question.
                    Takes question string, returns answer string.
        """
        self.config = get_config()
        self.vision = VisionClient()
        self.browser: Optional[BrowserManager] = None
        self.history: List[Dict[str, Any]] = []
        self.on_ask = on_ask or self._default_ask

    def _default_ask(self, question: str) -> str:
        """Default ask implementation using console input."""
        console.print(f"\n[yellow]Agent asks:[/yellow] {question}")
        return console.input("[green]Your answer:[/green] ")

    async def run(self, task: str) -> str:
        """
        Run agent to complete a task.

        Args:
            task: Task description from user

        Returns:
            Result message
        """
        console.print(Panel(f"[bold blue]Task:[/bold blue] {task}", title="Browser Agent"))

        async with create_browser() as browser:
            self.browser = browser
            self.history = []

            for step in range(1, self.config.max_steps + 1):
                console.print(f"\n[dim]Step {step}/{self.config.max_steps}[/dim]")

                result = await self._step(task)

                if result.get("done"):
                    console.print(Panel(
                        f"[bold green]Completed:[/bold green] {result.get('message', 'Task done')}",
                        title="Result"
                    ))
                    return result.get("message", "Task completed")

                if result.get("error") and step > 3:
                    # Check for repeated errors
                    recent_errors = sum(1 for h in self.history[-5:] if h.get("error"))
                    if recent_errors >= 3:
                        console.print("[red]Too many consecutive errors, stopping.[/red]")
                        return "Failed: Too many errors"

            console.print("[yellow]Max steps reached[/yellow]")
            return "Reached maximum steps without completing task"

    async def _step(self, task: str) -> Dict[str, Any]:
        """Execute one step of the agent loop."""
        page = self.browser.page

        # 1. Take screenshot
        console.print("  [dim]Taking screenshot...[/dim]")
        screenshot = await self.browser.screenshot()

        # 2. Find interactive elements
        console.print("  [dim]Finding elements...[/dim]")
        elements = await get_interactive_elements(page)
        console.print(f"  [dim]Found {len(elements)} interactive elements[/dim]")

        # 3. Draw markers on screenshot
        marked_screenshot = draw_markers(screenshot, elements)
        screenshot_b64 = encode_image(marked_screenshot)

        # 4. Get elements text description
        elements_text = elements_to_text(elements)

        # 5. Ask Claude for next action
        console.print("  [dim]Asking Claude...[/dim]")
        action = self.vision.ask_claude(
            screenshot_b64=screenshot_b64,
            task=task,
            history=self.history,
            current_url=self.browser.get_url(),
            elements_text=elements_text,
        )

        # Display action
        self._display_action(action)

        # 6. Handle special actions
        action_type = action.get("action")

        if action_type == "done":
            return {"done": True, "message": action.get("result", "Task completed")}

        if action_type == "ask":
            question = action.get("question", "Need more information")
            answer = self.on_ask(question)
            self.history.append({
                "action": "ask",
                "question": question,
                "answer": answer,
            })
            return {"done": False}

        if action_type == "error":
            error_msg = action.get("error", "Unknown error")
            console.print(f"  [red]Error:[/red] {error_msg}")
            self.history.append({"action": "error", "error": error_msg})
            return {"error": True, "message": error_msg}

        # 7. Execute action
        result = await execute_action(page, action, elements)

        # Display result
        if result.success:
            console.print(f"  [green]OK:[/green] {result.message}")
        else:
            console.print(f"  [red]Failed:[/red] {result.message}")
            if result.error:
                console.print(f"  [dim]{result.error}[/dim]")

        # 8. Wait for page to stabilize
        await self.browser.wait_for_stable()

        # 9. Record in history
        history_entry = {
            "action": action_type,
            "result": result.message if result.success else None,
            "error": result.error if not result.success else None,
        }

        # Add action-specific details
        if action_type == "click":
            history_entry["element"] = action.get("element")
        elif action_type == "type":
            history_entry["element"] = action.get("element")
            history_entry["text"] = action.get("text")
        elif action_type == "goto":
            history_entry["url"] = action.get("url")
        elif action_type == "scroll":
            history_entry["direction"] = action.get("direction")
        elif action_type == "press":
            history_entry["key"] = action.get("key", "Enter")

        self.history.append(history_entry)

        return {"done": False, "error": not result.success}

    def _display_action(self, action: Dict[str, Any]):
        """Display action in a nice format."""
        action_type = action.get("action", "unknown")
        thought = action.get("thought", "")

        # Build action description
        if action_type == "click":
            desc = f"Click element [{action.get('element')}]"
        elif action_type == "type":
            desc = f"Type '{action.get('text')}' into [{action.get('element')}]"
        elif action_type == "goto":
            desc = f"Go to {action.get('url')}"
        elif action_type == "scroll":
            desc = f"Scroll {action.get('direction', 'down')}"
        elif action_type == "wait":
            desc = "Wait for page load"
        elif action_type == "press":
            desc = f"Press {action.get('key', 'Enter')}"
        elif action_type == "done":
            desc = f"Done: {action.get('result')}"
        elif action_type == "ask":
            desc = f"Ask: {action.get('question')}"
        else:
            desc = f"Unknown action: {action_type}"

        # Create table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("Action", f"[bold]{desc}[/bold]")
        if thought:
            table.add_row("Thought", f"[dim]{thought}[/dim]")

        console.print(table)


async def run_agent(task: str, on_ask: Optional[Callable[[str], str]] = None) -> str:
    """
    Convenience function to run agent.

    Args:
        task: Task description
        on_ask: Optional callback for user questions

    Returns:
        Result message
    """
    agent = BrowserAgent(on_ask=on_ask)
    return await agent.run(task)
