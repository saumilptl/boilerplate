"""CLI commands for database seeding."""

import asyncio
import sys

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="seeder", help="Database seeding commands")
console = Console()


@app.command(name="list")
def list_seeders() -> None:
    """List all available seeders."""
    try:
        from app.infra.database.seed import SeedRegistry

        # Discover all seeders
        SeedRegistry.discover_seeders()

        seeders = SeedRegistry.get_all_seeders()

        if not seeders:
            console.print("[yellow]No seeders found.[/yellow]")
            return

        # Create table
        table = Table(title="Available Seeders", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Dependencies", style="yellow")

        for name, seeder_class in sorted(seeders.items()):
            deps = ", ".join(seeder_class.dependencies) if seeder_class.dependencies else "None"
            table.add_row(
                name,
                seeder_class.description or "No description",
                deps,
            )

        console.print(table)
        console.print(f"\n[bold green]Total seeders: {len(seeders)}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error listing seeders: {e}[/bold red]")
        sys.exit(1)


def _get_seeders_to_run(seeders: list[str] | None, all_seeders: bool) -> list[str] | None:
    """Determine which seeders to run based on arguments."""
    from app.infra.database.seed import SeedRegistry

    if all_seeders:
        seeder_names = list(SeedRegistry.get_all_seeders().keys())
        console.print(f"[bold blue]Running all {len(seeder_names)} seeders...[/bold blue]\n")
        return seeder_names
    if seeders:
        console.print(f"[bold blue]Running {len(seeders)} seeder(s)...[/bold blue]\n")
        return seeders

    console.print("[yellow]No seeders specified. Use --all to run all seeders.[/yellow]")
    return None


async def _run_single_seeder(seeder_name: str, session: any) -> tuple[str, bool, str]:
    """Run a single seeder and return result."""
    from app.infra.database.seed import SeedRegistry

    seeder_class = SeedRegistry.get_seeder(seeder_name)

    if not seeder_class:
        console.print(f"[bold red]Seeder not found: {seeder_name}[/bold red]")
        return (seeder_name, False, "Not found")

    try:
        console.print(f"Running: [cyan]{seeder_name}[/cyan]... ", end="")

        seeder = seeder_class()
        inserted = await seeder.run(session)

        if inserted:
            console.print("[bold green]Data inserted[/bold green]")
            result = (seeder_name, True, "Inserted")
        else:
            console.print("[yellow]Already exists[/yellow]")
            result = (seeder_name, True, "Already exists")

        await session.commit()
        return result

    except Exception as e:
        console.print(f"[bold red]Failed: {e}[/bold red]")
        await session.rollback()
        return (seeder_name, False, str(e))


def _print_results(results: list[tuple[str, bool, str]]) -> None:
    """Print seeder execution results."""
    console.print("\n[bold]Summary:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Seeder", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Result", style="yellow")

    for name, success, result in results:
        status = "[green]Success[/green]" if success else "[red]Failed[/red]"
        table.add_row(name, status, result)

    console.print(table)

    if any(not success for _, success, _ in results):
        sys.exit(1)


async def _execute_seeders(seeder_names: list[str]) -> None:
    """Execute seeders with database session."""
    from app.config import get_config
    from app.infra.database.db import DatabaseManager

    config = get_config()
    db_manager = DatabaseManager(config.DATABASE)

    sorted_seeders = _sort_by_dependencies(seeder_names)
    results = []

    async with db_manager.get_session() as session:
        for seeder_name in sorted_seeders:
            result = await _run_single_seeder(seeder_name, session)
            results.append(result)

    _print_results(results)


@app.command(name="run")
def run_seeders(
    seeders: list[str] = typer.Argument(None, help="Seeder names to run (leave empty for all)"),
    all_seeders: bool = typer.Option(False, "--all", "-a", help="Run all seeders"),
) -> None:
    """Run specific seeders or all seeders."""
    from app.infra.database.seed import SeedRegistry

    try:
        SeedRegistry.discover_seeders()

        seeder_names = _get_seeders_to_run(seeders, all_seeders)
        if not seeder_names:
            return

        asyncio.run(_execute_seeders(seeder_names))

    except Exception as e:
        console.print(f"[bold red]Error running seeders: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@app.command(name="init")
def init_seeders() -> None:
    """Initialize seeder directory structure."""
    import os
    from pathlib import Path

    try:
        # Create seeders directory
        seeders_dir = Path("app/infra/database/seed/seeders")
        seeders_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        init_file = seeders_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Database seeders."""\n')

        # Create example seeder
        example_file = seeders_dir / "example_seeder.py"
        if not example_file.exists():
            example_content = '''"""Example seeder."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.seed import Seeder


class ExampleSeeder(Seeder):
    """Example seeder for demonstration."""

    name = "example"
    description = "Example seeder showing the basic structure"
    dependencies = []

    async def run(self, session: AsyncSession) -> bool:
        """
        Run the seeder.

        Returns:
            True if data was inserted, False if already exists
        """
        # Check if data already exists
        # existing = await session.execute(...)

        # If data exists, return False
        # if existing:
        #     return False

        # Create and insert data
        # obj = SomeModel(...)
        # session.add(obj)
        # await session.flush()

        return True
'''
            example_file.write_text(example_content)

        console.print("[bold green]Seeder directory initialized![/bold green]")
        console.print(f"Location: [cyan]{seeders_dir}[/cyan]")
        console.print("\nCreated files:")
        console.print(f"  - {init_file.relative_to(os.getcwd())}")
        console.print(f"  - {example_file.relative_to(os.getcwd())}")

    except Exception as e:
        console.print(f"[bold red]Error initializing seeders: {e}[/bold red]")
        sys.exit(1)


def _sort_by_dependencies(seeder_names: list[str]) -> list[str]:
    """
    Sort seeders by dependencies using topological sort.

    Args:
        seeder_names: List of seeder names to sort

    Returns:
        Sorted list of seeder names
    """
    from app.infra.database.seed import SeedRegistry

    # Build dependency graph
    graph: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for name in seeder_names:
        seeder_class = SeedRegistry.get_seeder(name)
        if seeder_class:
            graph[name] = seeder_class.dependencies
            in_degree[name] = 0

    # Calculate in-degree
    for name in seeder_names:
        for dep in graph.get(name, []):
            if dep in in_degree:
                in_degree[dep] += 1

    # Topological sort
    queue = [name for name in seeder_names if in_degree[name] == 0]
    sorted_names = []

    while queue:
        name = queue.pop(0)
        sorted_names.append(name)

        for dep in graph.get(name, []):
            if dep in in_degree:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

    return sorted_names


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
