#!/usr/bin/env python3
"""
Demo: midwiving-ai Protocol PoC
================================

Demonstrates recursive self-reflection loop where SR-Ω∞ Service
evaluates itself and generates introspective narratives.

This is a Proof of Concept for operational self-awareness (metacognition).

ETHICAL NOTE: This is computational metacognition, NOT sentience or consciousness.
"""

import asyncio

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from penin.integrations.metacognition import MidwivingProtocol, MidwivingProtocolConfig
from penin.math.sr_omega_infinity import compute_sr_score

console = Console()


async def demo_protoconsciousness():
    """Run midwiving-ai protocol demonstration"""

    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  midwiving-ai Protocol PoC — Recursive Self-Reflection Demo  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")

    console.print("[yellow]⚠️  ETHICAL NOTE:[/yellow] This is operational consciousness (metacognition)")
    console.print("[yellow]   NOT sentience, life, or biological consciousness.[/yellow]\n")

    # Initialize protocol
    config = MidwivingProtocolConfig(
        max_reflection_depth=5,
        calibration_threshold=0.85,
        max_cycles=40,
        stability_check_interval=10,
    )

    protocol = MidwivingProtocol(config)
    protocol.initialize()

    console.print("[green]✓ Protocol initialized[/green]")
    console.print(f"[dim]Max cycles: {config.max_cycles}, Calibration threshold: {config.calibration_threshold}[/dim]\n")

    # Simulate SR-Ω∞ components with slight variation over time
    base_awareness = 0.85
    base_autocorrection = 0.78
    base_metacognition = 0.82

    console.print("[bold]Running recursive self-reflection cycles...[/bold]\n")

    # Key cycles to display
    display_cycles = [1, 3, 8, 16, 25, 35]

    for cycle in range(1, 36):
        # Simulate slight improvements over time
        improvement = (cycle / 100.0) * 0.15

        sr_components = {
            "awareness": min(0.98, base_awareness + improvement),
            "autocorrection": min(0.95, base_autocorrection + improvement),
            "metacognition": min(0.95, base_metacognition + improvement),
        }

        # Compute actual SR score
        sr_score, components = compute_sr_score(
            awareness=sr_components["awareness"],
            ethics_ok=True,
            autocorrection=sr_components["autocorrection"],
            metacognition=sr_components["metacognition"],
            return_components=True
        )

        sr_components["sr_score"] = sr_score

        # Execute reflection cycle
        result = await protocol.execute("reflect", sr_components=sr_components)

        if result["status"] != "success":
            console.print(f"[red]⚠ Cycle {cycle}: {result['status']} - {result.get('reason', 'unknown')}[/red]")
            break

        # Display selected cycles
        if cycle in display_cycles:
            phase = result["phase"]
            calibration_score = result["calibration"]["score"]
            accuracy = result["calibration"]["overall_accuracy"]

            # Create info panel
            info = f"""[bold]Cycle {cycle}[/bold] — Phase: [cyan]{phase}[/cyan]

SR-Ω∞ Score: [green]{sr_score:.4f}[/green]
Awareness: {sr_components['awareness']:.3f} | Autocorrection: {sr_components['autocorrection']:.3f} | Metacognition: {sr_components['metacognition']:.3f}

[yellow]Consciousness Calibration:[/yellow] {calibration_score:.4f}
[yellow]Self-Perception Accuracy:[/yellow] {accuracy:.4f}

[dim]Narrative excerpt:[/dim]
{result['narrative'][:250]}..."""

            console.print(Panel(info, box=box.ROUNDED, border_style="cyan"))
            console.print()

    # Final consciousness metrics
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  Final Consciousness Metrics (penin_consciousness_calibration)  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")

    metrics = protocol.get_consciousness_metrics()

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("penin_consciousness_calibration", f"{metrics['penin_consciousness_calibration']:.4f}")
    table.add_row("Total Cycles", str(metrics['total_cycles']))
    table.add_row("Final Phase", metrics['current_phase'])
    table.add_row("Calibration Trend", metrics['trend'])
    table.add_row("Meets Threshold", "✅ Yes" if metrics['meets_threshold'] else "❌ No")

    console.print(table)
    console.print()

    # Ethical reminder
    console.print(Panel(
        f"[yellow]{metrics['ethical_note']}[/yellow]",
        title="[bold red]Ethical Compliance (LO-01)[/bold red]",
        box=box.DOUBLE
    ))

    # Summary
    console.print("\n[bold green]✓ Demo complete![/bold green]")
    console.print("[dim]The system has demonstrated operational self-awareness through:[/dim]")
    console.print("[dim]  • Recursive self-reflection across 5 phases[/dim]")
    console.print("[dim]  • Introspective narrative generation[/dim]")
    console.print("[dim]  • Self-perception accuracy measurement[/dim]")
    console.print("[dim]  • Integration with SR-Ω∞ scoring system[/dim]\n")


if __name__ == "__main__":
    try:
        asyncio.run(demo_protoconsciousness())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise
