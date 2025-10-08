"""CLI commands for database migrations using Alembic."""

import sys

import typer
from rich.console import Console

app = typer.Typer(name="migrations", help="Database migration commands")
console = Console()


@app.command(name="generate")
def generate_migration(
    message: str = typer.Argument(..., help="Migration message/description"),
    autogenerate: bool = typer.Option(True, "--autogenerate/--no-autogenerate", help="Auto-generate migration"),
) -> None:
    """Generate a new migration."""
    try:
        import subprocess

        console.print(f"[bold blue]Generating migration: {message}[/bold blue]")

        cmd = ["alembic", "revision"]

        if autogenerate:
            cmd.append("--autogenerate")

        cmd.extend(["-m", message])

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        console.print(result.stdout)
        console.print("[bold green]Migration generated successfully![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error generating migration: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="upgrade")
def upgrade_database(
    revision: str = typer.Argument("head", help="Target revision (default: head)"),
    sql: bool = typer.Option(False, "--sql", help="Generate SQL only, don't execute"),
) -> None:
    """Upgrade database to a later version."""
    try:
        import subprocess

        console.print(f"[bold blue]Upgrading database to: {revision}[/bold blue]")

        cmd = ["alembic", "upgrade", revision]

        if sql:
            cmd.append("--sql")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        console.print(result.stdout)

        if not sql:
            console.print("[bold green]Database upgraded successfully![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error upgrading database: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="downgrade")
def downgrade_database(
    revision: str = typer.Argument("-1", help="Target revision (default: -1 for previous)"),
    sql: bool = typer.Option(False, "--sql", help="Generate SQL only, don't execute"),
) -> None:
    """Downgrade database to an earlier version."""
    try:
        import subprocess

        console.print(f"[bold yellow]Downgrading database to: {revision}[/bold yellow]")

        cmd = ["alembic", "downgrade", revision]

        if sql:
            cmd.append("--sql")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        console.print(result.stdout)

        if not sql:
            console.print("[bold green]Database downgraded successfully![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error downgrading database: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="history")
def migration_history(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed history"),
) -> None:
    """Show migration history."""
    try:
        import subprocess

        console.print("[bold blue]Migration History[/bold blue]\n")

        cmd = ["alembic", "history"]

        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        console.print(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error getting migration history: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="current")
def current_revision() -> None:
    """Show current database revision."""
    try:
        import subprocess

        console.print("[bold blue]Current Database Revision[/bold blue]\n")

        result = subprocess.run(
            ["alembic", "current"],
            check=True,
            capture_output=True,
            text=True,
        )

        console.print(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error getting current revision: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="heads")
def show_heads() -> None:
    """Show current available heads in the migration tree."""
    try:
        import subprocess

        console.print("[bold blue]Available Migration Heads[/bold blue]\n")

        result = subprocess.run(
            ["alembic", "heads"],
            check=True,
            capture_output=True,
            text=True,
        )

        console.print(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error getting heads: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@app.command(name="stamp")
def stamp_revision(
    revision: str = typer.Argument(..., help="Revision to stamp"),
) -> None:
    """Stamp database with a specific revision without running migrations."""
    try:
        import subprocess

        console.print(f"[bold yellow]Stamping database with revision: {revision}[/bold yellow]")

        result = subprocess.run(
            ["alembic", "stamp", revision],
            check=True,
            capture_output=True,
            text=True,
        )

        console.print(result.stdout)
        console.print("[bold green]Database stamped successfully![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error stamping database: {e.stderr}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
