#!/usr/bin/env python3
"""
Browser Agent - AI-powered browser automation.

Usage:
    python main.py                    # Interactive mode
    python main.py "task description" # Direct task mode
"""

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Ensure proper event loop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
[bold blue]============================================================
                      Browser Agent
           AI-powered browser automation with Claude
============================================================[/bold blue]
"""
    console.print(banner)


def check_api_key():
    """Check if API key is set."""
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        console.print(Panel(
            "[red]OPENAI_API_KEY not found![/red]\n\n"
            "Set it with:\n"
            "  [cyan]set OPENAI_API_KEY=sk-...[/cyan] (Windows)\n"
            "  [cyan]export OPENAI_API_KEY=sk-...[/cyan] (Linux/Mac)",
            title="Error"
        ))
        sys.exit(1)


def get_task() -> str:
    """Get task from command line or prompt user."""
    # Check command line args
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])

    # Interactive prompt
    console.print("\n[bold]Examples of tasks:[/bold]")
    console.print("  • Перейди на google.com и найди погоду в Москве")
    console.print("  • Найди вакансии Python-разработчика на hh.ru")
    console.print("  • Открой youtube.com и найди видео про котиков")
    console.print("  • Зайди на wikipedia.org и найди статью про искусственный интеллект")
    console.print()

    task = Prompt.ask("[bold green]Enter your task[/bold green]")

    if not task.strip():
        console.print("[red]No task provided, exiting.[/red]")
        sys.exit(0)

    return task.strip()


async def main():
    """Main entry point."""
    print_banner()
    check_api_key()

    task = get_task()

    console.print()
    console.print("[dim]Starting browser...[/dim]")
    console.print("[dim]Press Ctrl+C to stop at any time[/dim]")
    console.print()

    try:
        # Import here to allow API key check first
        from agent import run_agent

        result = await run_agent(task)

        console.print()
        console.print(Panel(
            f"[bold]Final Result:[/bold]\n{result}",
            title="Done",
            border_style="green"
        ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)

    except Exception as e:
        console.print(Panel(
            f"[red]Error:[/red] {str(e)}",
            title="Error",
            border_style="red"
        ))

        # Show traceback in debug mode
        import os
        if os.environ.get("DEBUG"):
            import traceback
            console.print(traceback.format_exc())

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
