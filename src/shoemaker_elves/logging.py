"""
Logging utilities with optional rich support.

This module provides a unified logging interface that uses rich for enhanced output
when available, but gracefully falls back to plain text output when rich is not installed.
"""

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Try to import rich components
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Logger:
    """
    Unified logger that uses rich when available, falls back to plain text otherwise.
    Also supports machine-readable logging to a file.
    """

    def __init__(self, log_dir: Path | None = None, enable_rich: bool = True):
        """
        Initialize the logger.

        Args:
            log_dir: Directory for log files (creates logs/run.log)
            enable_rich: Whether to use rich if available
        """
        self.use_rich = RICH_AVAILABLE and enable_rich
        self.log_dir = log_dir
        self.log_file = None

        if self.use_rich:
            self.console = Console()
        else:
            self.console = None

        # Initialize log file if directory provided
        if log_dir:
            self._init_log_file()

    def _init_log_file(self):
        """Initialize the machine-readable log file."""
        if not self.log_dir:
            return

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "run.log"
            # Create or clear the log file
            with open(self.log_file, 'w') as f:
                self._write_log_entry("session_start", {"timestamp": self._timestamp()})
        except OSError as e:
            print(f"Warning: Could not create log file: {e}")
            self.log_file = None

    def _timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def _write_log_entry(self, event_type: str, data: dict):
        """Write a machine-readable log entry (JSON Lines format)."""
        if not self.log_file:
            return

        try:
            entry = {
                "timestamp": self._timestamp(),
                "event": event_type,
                **data
            }
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except OSError:
            pass  # Silently fail on log write errors

    def print(self, text: str, style: str | None = None):
        """Print text with optional styling."""
        if self.use_rich and style:
            self.console.print(text, style=style)
        else:
            print(text)

    def error(self, text: str):
        """Print an error message."""
        if self.use_rich:
            self.console.print(f"✗ {text}", style="bold red")
        else:
            print(f"ERROR: {text}")
        self._write_log_entry("error", {"message": text})

    def warning(self, text: str):
        """Print a warning message."""
        if self.use_rich:
            self.console.print(f"⚠ {text}", style="bold yellow")
        else:
            print(f"WARNING: {text}")
        self._write_log_entry("warning", {"message": text})

    def success(self, text: str):
        """Print a success message."""
        if self.use_rich:
            self.console.print(f"✓ {text}", style="bold green")
        else:
            print(f"✓ {text}")
        self._write_log_entry("success", {"message": text})

    def info(self, text: str):
        """Print an info message."""
        if self.use_rich:
            self.console.print(f"ℹ {text}", style="cyan")
        else:
            print(f"INFO: {text}")
        self._write_log_entry("info", {"message": text})

    def header(self, text: str):
        """Print a header/title."""
        if self.use_rich:
            self.console.print(Panel(text, style="bold blue"))
        else:
            print(f"\n{'='*60}")
            print(f"  {text}")
            print(f"{'='*60}\n")

    def section(self, text: str):
        """Print a section divider."""
        if self.use_rich:
            self.console.print(f"\n[bold cyan]{text}[/bold cyan]")
            self.console.print("─" * 60)
        else:
            print(f"\n{'─'*60}")
            print(f"  {text}")
            print(f"{'─'*60}")

    def table(self, title: str, columns: list[str], rows: list[list[str]]):
        """Display a table."""
        if self.use_rich:
            table = Table(title=title, show_header=True, header_style="bold magenta")
            for col in columns:
                table.add_column(col)
            for row in rows:
                table.add_row(*row)
            self.console.print(table)
        else:
            print(f"\n{title}")
            print("─" * 60)
            # Print header
            print("  ".join(f"{col:20}" for col in columns))
            print("─" * 60)
            # Print rows
            for row in rows:
                print("  ".join(f"{str(cell):20}" for cell in row))
            print()

        # Log table data
        self._write_log_entry("table", {
            "title": title,
            "columns": columns,
            "rows": rows
        })

    @contextmanager
    def progress(self, description: str = "Processing..."):
        """
        Context manager for progress tracking.

        Usage:
            with logger.progress("Loading tasks") as progress:
                task = progress.add_task("Task 1", total=100)
                for i in range(100):
                    progress.update(task, advance=1)
        """
        if self.use_rich:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console
            )
            with progress:
                yield progress
        else:
            # Fallback: yield a mock progress object
            class MockProgress:
                def add_task(self, description, total=100):
                    print(f"  {description}...")
                    return 0

                def update(self, task_id, advance=1, **kwargs):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            yield MockProgress()

    def task_summary(self, tasks: list[dict], total_cost: float = 0.0):
        """Display a summary of tasks."""
        if self.use_rich:
            # Create a table
            table = Table(title="Task Summary", show_header=True, header_style="bold magenta")
            table.add_column("Status", style="dim", width=8)
            table.add_column("Task", style="cyan")
            table.add_column("Files", style="dim")

            for task in tasks:
                status_icon = {
                    "completed": "[green]✓[/green]",
                    "failed": "[red]✗[/red]",
                    "running": "[yellow]⟳[/yellow]",
                    "pending": "[dim]○[/dim]"
                }.get(task["status"], "?")

                files = task.get("files_modified", [])
                files_str = ", ".join(files[:3])
                if len(files) > 3:
                    files_str += f" (+{len(files) - 3} more)"

                table.add_row(status_icon, task["title"], files_str)

            self.console.print(table)

            # Print cost summary
            if total_cost > 0:
                self.console.print(f"\n[bold]Total Cost:[/bold] [yellow]${total_cost:.2f}[/yellow]")
        else:
            # Plain text fallback
            print("\nTask Summary")
            print("─" * 60)
            for task in tasks:
                status_icon = {
                    "completed": "[+]",
                    "failed": "[x]",
                    "running": "[~]",
                    "pending": "[ ]"
                }.get(task["status"], "[?]")

                print(f"  {status_icon} {task['title']}")

                files = task.get("files_modified", [])
                if files:
                    files_str = ", ".join(files[:5])
                    print(f"      Files: {files_str}")

            if total_cost > 0:
                print(f"\nTotal Cost: ${total_cost:.2f}")
            print()

        # Log task summary
        self._write_log_entry("task_summary", {
            "tasks": tasks,
            "total_cost": total_cost
        })

    def log_event(self, event_type: str, data: dict):
        """Log a custom event to the machine-readable log."""
        self._write_log_entry(event_type, data)

    def close(self):
        """Close the logger and write session end."""
        if self.log_file:
            self._write_log_entry("session_end", {"timestamp": self._timestamp()})


# Singleton instance for convenience
_default_logger: Logger | None = None


def get_logger(log_dir: Path | None = None, enable_rich: bool = True) -> Logger:
    """Get or create the default logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger(log_dir=log_dir, enable_rich=enable_rich)
    return _default_logger


def is_rich_available() -> bool:
    """Check if rich is available."""
    return RICH_AVAILABLE
