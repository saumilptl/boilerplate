"""Service runner with hot-reload support for development."""

import os
import signal
import subprocess
import sys
import time
from enum import Enum

import psutil
import typer
from rich.console import Console

app = typer.Typer(name="serve", help="Run API or worker services")
console = Console()


class ServiceType(str, Enum):
    """Available service types."""

    API = "api"
    WORKER = "worker"


def kill_process_tree(process: subprocess.Popen) -> None:
    """Kill the process and all its children gracefully."""
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)

        # Terminate all processes
        for p in [*children, parent]:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                continue

        # Wait for processes to terminate
        gone, alive = psutil.wait_procs([*children, parent], timeout=1)

        # Force kill remaining processes
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                continue

    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        console.print(f"[bold red]Error killing process tree: {e}[/bold red]", file=sys.stderr)


def build_api_command(reload: bool) -> list[str]:
    """Build command for API service."""
    base_cmd = [
        "poetry",
        "run",
        "uvicorn",
        "app.api.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    if reload:
        return [
            "watchmedo",
            "auto-restart",
            "--directory",
            "./app/",
            "--recursive",
            "--pattern",
            "*.py",
            "--",
            *base_cmd,
        ]
    return base_cmd


def build_worker_command(reload: bool, beat: bool) -> list[str]:
    """Build command for Celery worker."""
    celery_cmd = [
        "poetry",
        "run",
        "celery",
        "-A",
        "app.worker.app:celery_app",
        "worker",
        "--loglevel=info",
    ]

    if beat:
        celery_cmd.append("--beat")

    if reload:
        return [
            "watchmedo",
            "auto-restart",
            "--directory",
            "./app/",
            "--recursive",
            "--pattern",
            "*.py",
            "--",
            *celery_cmd,
        ]
    return celery_cmd


def wait_for_processes(processes: list[subprocess.Popen], signal_handler) -> None:
    """Wait for processes and handle their exit codes."""
    while processes:
        for proc in list(processes):
            return_code = proc.poll()
            if return_code is not None:
                processes.remove(proc)
                if return_code != 0:
                    console.print(f"[yellow]Process exited with code {return_code}[/yellow]")
                    signal_handler(None, None)

        if processes:
            time.sleep(0.1)


def start_service(service: ServiceType, reload: bool, beat: bool) -> subprocess.Popen:
    """Start the appropriate service and return the process."""
    if service == ServiceType.API:
        cmd = build_api_command(reload)
    elif service == ServiceType.WORKER:
        cmd = build_worker_command(reload, beat)
    else:
        raise ValueError(f"Unknown service: {service}")

    return subprocess.Popen(cmd)


@app.command(name="api")
def serve_api(
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload for development"),
) -> None:
    """Run the FastAPI application server."""
    processes: list[subprocess.Popen] = []

    def signal_handler(_signum, _frame):
        """Handle shutdown signals gracefully."""
        for proc in processes:
            if proc and proc.poll() is None:
                kill_process_tree(proc)
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        console.print("[bold green]Starting API server[/bold green]")
        if reload:
            console.print("[yellow]Hot-reload enabled - watching for file changes...[/yellow]")
        process = start_service(ServiceType.API, reload, False)
        processes.append(process)
        wait_for_processes(processes, signal_handler)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error running command: {e}[/bold red]", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
    finally:
        for proc in processes:
            if proc and proc.poll() is None:
                kill_process_tree(proc)


@app.command(name="worker")
def serve_worker(  # noqa: C901
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload for development"),
    beat: bool = typer.Option(False, "--beat", "-B", help="Run beat scheduler alongside worker"),
) -> None:
    """Run the Celery worker."""
    processes: list[subprocess.Popen] = []

    # Check environment variable for beat
    if os.getenv("RUN_CELERY_BEAT", "").lower() == "true":
        beat = True

    def signal_handler(_signum, _frame):
        """Handle shutdown signals gracefully."""
        for proc in processes:
            if proc and proc.poll() is None:
                kill_process_tree(proc)
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        console.print("[bold green]Starting Celery worker[/bold green]")
        if reload:
            console.print("[yellow]Hot-reload enabled - watching for file changes...[/yellow]")
        if beat:
            console.print("[blue]Running beat scheduler alongside worker[/blue]")

        process = start_service(ServiceType.WORKER, reload, beat)
        processes.append(process)
        wait_for_processes(processes, signal_handler)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error running command: {e}[/bold red]", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
    finally:
        for proc in processes:
            if proc and proc.poll() is None:
                kill_process_tree(proc)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
