"""
PENIN-Ω CLI
===========

Command-line interface for PENIN-Ω IA³ system.

Usage:
    penin version          # Show version
    penin evolve           # Run evolution cycles
    penin guard            # Start Σ-Guard service
    penin meta             # Start Ω-META service
    penin sr               # Start SR-Ω∞ service
    penin league           # Start ACFA League service
    penin services         # Start all services
"""

import typer
from typing import Optional

app = typer.Typer(
    name="penin",
    help="PENIN-Ω — IA³ Auto-Evolutiva com Ética Embutida",
    add_completion=False,
)


@app.command()
def version():
    """Show PENIN-Ω version"""
    from penin import __version__
    
    typer.echo(f"🧠 PENIN-Ω v{__version__}")
    typer.echo(f"   IA³: Auto-Evolutiva, Ética, Auditável")


@app.command()
def evolve(
    n: int = typer.Option(1, "--n", "-n", help="Number of evolution cycles"),
    budget: float = typer.Option(10.0, "--budget", "-b", help="Daily budget in USD"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run (no real LLM calls)"),
):
    """Run evolution cycles"""
    
    typer.echo(f"\n🚀 PENIN-Ω Evolution")
    typer.echo(f"   Cycles: {n}")
    typer.echo(f"   Budget: ${budget:.2f}")
    typer.echo(f"   Provider: {provider}")
    typer.echo(f"   Mode: {'DRY-RUN' if dry_run else 'PRODUCTION'}\n")
    
    from penin.runners.evolution_runner import run_evolution
    
    try:
        run_evolution(n_cycles=n, budget_usd=budget, provider=provider, dry_run=dry_run)
        typer.echo("\n✅ Evolution complete!\n")
    except Exception as e:
        typer.echo(f"\n❌ Evolution failed: {e}\n", err=True)
        raise typer.Exit(code=1)


@app.command()
def guard(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8001, "--port", "-p", help="Port to bind"),
):
    """Start Σ-Guard service"""
    
    typer.echo(f"\n🛡️  Starting Σ-Guard service on {host}:{port}...\n")
    
    import uvicorn
    
    try:
        uvicorn.run(
            "penin.guard.sigma_guard_service:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\n✅ Σ-Guard stopped\n")


@app.command()
def meta(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8002, "--port", "-p", help="Port to bind"),
):
    """Start Ω-META service"""
    
    typer.echo(f"\n🧬 Starting Ω-META service on {host}:{port}...\n")
    
    import uvicorn
    
    try:
        uvicorn.run(
            "penin.meta.omega_meta_service:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\n✅ Ω-META stopped\n")


@app.command()
def sr(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8003, "--port", "-p", help="Port to bind"),
):
    """Start SR-Ω∞ service"""
    
    typer.echo(f"\n🔮 Starting SR-Ω∞ service on {host}:{port}...\n")
    
    import uvicorn
    
    try:
        uvicorn.run(
            "penin.sr.sr_service:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\n✅ SR-Ω∞ stopped\n")


@app.command()
def league(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8004, "--port", "-p", help="Port to bind"),
):
    """Start ACFA League service"""
    
    typer.echo(f"\n🏆 Starting ACFA League service on {host}:{port}...\n")
    
    import uvicorn
    
    try:
        uvicorn.run(
            "penin.league.acfa_service:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\n✅ ACFA League stopped\n")


@app.command()
def services(
    guard_port: int = typer.Option(8001, help="Σ-Guard port"),
    meta_port: int = typer.Option(8002, help="Ω-META port"),
    sr_port: int = typer.Option(8003, help="SR-Ω∞ port"),
    league_port: int = typer.Option(8004, help="ACFA League port"),
):
    """Start all services (requires multiprocessing)"""
    
    typer.echo("\n🚀 Starting all PENIN-Ω services...\n")
    typer.echo("   🛡️  Σ-Guard:     :{guard_port}")
    typer.echo("   🧬 Ω-META:      :{meta_port}")
    typer.echo("   🔮 SR-Ω∞:       :{sr_port}")
    typer.echo("   🏆 ACFA League: :{league_port}\n")
    
    typer.echo("⚠️  Use docker-compose to run all services simultaneously")
    typer.echo("   docker-compose up -d\n")


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()
