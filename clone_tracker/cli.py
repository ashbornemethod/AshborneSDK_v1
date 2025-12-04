"""
Command-line interface for Clone Tracker using Typer.
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from .core import CloneTrackerCore
from .utils import load_json, setup_logger

app = typer.Typer(
    name="clone_tracker",
    help="Clone detection and tracking system for GitHub repositories",
    add_completion=False
)


@app.command()
def scan(
    output_dir: Annotated[
        str,
        typer.Option("--output-dir", "-o", help="Output directory for scan results")
    ] = "data",
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force regeneration of signatures")
    ] = False,
    max_results: Annotated[
        int,
        typer.Option("--max-results", "-m", help="Maximum search results to process")
    ] = 100
) -> None:
    """
    Run a complete clone detection scan.
    
    Generates file signatures, searches GitHub for potential clones,
    and saves results to output directory.
    """
    logger = setup_logger("clone_tracker")
    
    try:
        typer.echo("🔍 Starting clone detection scan...")
        
        # Initialize core
        core = CloneTrackerCore(
            output_dir=output_dir,
            canonical_owner="ashbornemethod",
            canonical_repo="AshborneSDK_v1"
        )
        
        # Run scan
        results = core.run_scan(
            force_regenerate_signatures=force,
            max_search_results=max_results
        )
        
        # Display summary
        typer.echo("\n✅ Scan completed successfully!")
        typer.echo(f"   Forks found: {len(results.get('forks', []))}")
        typer.echo(f"   Suspicious repos: {len(results.get('suspicious_repos', []))}")
        
        high_severity = sum(
            1 for r in results.get('suspicious_repos', [])
            if r.get('severity') == 'HIGH'
        )
        if high_severity > 0:
            typer.echo(f"   ⚠️  High-severity repos: {high_severity}")
        
        typer.echo(f"\nResults saved to: {output_dir}/")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@app.command()
def report(
    output_dir: Annotated[
        str,
        typer.Option("--output-dir", "-o", help="Output directory containing scan results")
    ] = "data"
) -> None:
    """
    Generate and display a summary report from scan results.
    
    Reads the most recent scan results and displays a formatted summary
    of findings including forks and suspicious repositories.
    """
    try:
        # Initialize core
        core = CloneTrackerCore(output_dir=output_dir)
        
        # Generate report
        report_text = core.generate_report()
        
        # Display report
        typer.echo(report_text)
        
        sys.exit(0)
        
    except Exception as e:
        typer.echo(f"❌ Error generating report: {e}", err=True)
        sys.exit(1)


@app.command()
def watch(
    interval: Annotated[
        int,
        typer.Option("--interval", "-i", help="Scan interval in minutes")
    ] = 10,
    output_dir: Annotated[
        str,
        typer.Option("--output-dir", "-o", help="Output directory for scan results")
    ] = "data",
    once: Annotated[
        bool,
        typer.Option("--once", help="Run scan once and exit (no watching)")
    ] = False
) -> None:
    """
    Watch for new clones by running scans periodically.
    
    Runs scans at specified intervals, compares results with previous scans,
    and reports any new findings. Sends alerts if webhooks are configured.
    """
    logger = setup_logger("clone_tracker")
    
    try:
        # Initialize core
        core = CloneTrackerCore(output_dir=output_dir)
        
        scan_count = 0
        
        while True:
            scan_count += 1
            typer.echo(f"\n{'='*60}")
            typer.echo(f"🔍 Running scan #{scan_count}...")
            typer.echo(f"{'='*60}\n")
            
            # Load previous results
            scan_results_file = Path(output_dir) / "scan_results.json"
            previous_results = load_json(str(scan_results_file), default={})
            
            # Run scan
            try:
                current_results = core.run_scan(
                    force_regenerate_signatures=False,
                    max_search_results=100
                )
                
                # Compare with previous
                if previous_results:
                    differences = core.compare_scans(previous_results, current_results)
                    
                    # Report differences
                    if differences['new_forks']:
                        typer.echo(f"\n🆕 New forks detected: {len(differences['new_forks'])}")
                        for fork in differences['new_forks'][:5]:
                            typer.echo(f"   - {fork['owner']}/{fork['repo']}")
                    
                    if differences['new_suspicious_repos']:
                        typer.echo(
                            f"\n⚠️  New suspicious repos: {len(differences['new_suspicious_repos'])}"
                        )
                        for repo in differences['new_suspicious_repos'][:5]:
                            typer.echo(
                                f"   - {repo['owner']}/{repo['repo']} "
                                f"(Score: {repo['score']}%, Severity: {repo['severity']})"
                            )
                    
                    if not differences['new_forks'] and not differences['new_suspicious_repos']:
                        typer.echo("\n✅ No new clones detected")
                else:
                    typer.echo("\n✅ Initial scan completed")
                
            except Exception as e:
                logger.error(f"Scan #{scan_count} failed: {e}")
                typer.echo(f"❌ Scan failed: {e}", err=True)
            
            # Exit if running once
            if once:
                typer.echo("\n✅ Single scan completed")
                break
            
            # Wait for next interval
            typer.echo(f"\n⏱️  Waiting {interval} minutes until next scan...")
            time.sleep(interval * 60)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        typer.echo("\n\n🛑 Watch stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Watch failed: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@app.command()
def export(
    output_dir: Annotated[
        str,
        typer.Option("--output-dir", "-o", help="Output directory containing scan results")
    ] = "data",
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Export format (json or csv)")
    ] = "json",
    export_dir: Annotated[
        Optional[str],
        typer.Option("--export-dir", "-e", help="Directory to export to")
    ] = None
) -> None:
    """
    Export scan results to specified format.
    
    Exports scan results to JSON or CSV format for use in other tools
    or for archival purposes.
    """
    try:
        if format not in ["json", "csv"]:
            typer.echo(f"❌ Invalid format: {format}. Use 'json' or 'csv'", err=True)
            sys.exit(1)
        
        # Set export directory
        if export_dir is None:
            export_dir = output_dir
        
        # Load scan results
        scan_results_file = Path(output_dir) / "scan_results.json"
        if not scan_results_file.exists():
            typer.echo(
                f"❌ No scan results found at {scan_results_file}. "
                "Run a scan first.",
                err=True
            )
            sys.exit(1)
        
        results = load_json(str(scan_results_file))
        
        # Export based on format
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            output_file = export_path / "scan_results_export.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            typer.echo(f"✅ Exported to: {output_file}")
            
        elif format == "csv":
            # Export suspicious repos to CSV
            output_file = export_path / "suspicious_repos_export.csv"
            
            repos = results.get('suspicious_repos', [])
            if not repos:
                typer.echo("❌ No suspicious repos to export", err=True)
                sys.exit(1)
            
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'owner', 'repo', 'repo_url', 'score', 'severity',
                    'matched_files_count', 'forks_count', 'stargazers_count',
                    'created_at'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for repo in repos:
                    writer.writerow({
                        'owner': repo['owner'],
                        'repo': repo['repo'],
                        'repo_url': repo['repo_url'],
                        'score': repo['score'],
                        'severity': repo['severity'],
                        'matched_files_count': len(repo.get('matched_files', [])),
                        'forks_count': repo.get('forks_count', 0),
                        'stargazers_count': repo.get('stargazers_count', 0),
                        'created_at': repo.get('created_at', '')
                    })
            
            typer.echo(f"✅ Exported {len(repos)} repos to: {output_file}")
        
        sys.exit(0)
        
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
