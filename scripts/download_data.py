#!/usr/bin/env python3
"""
Script to download NYC Taxi trip data from TLC website.
Downloads PARQUET files for specified months and years.
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

NYC_TAXI_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
DATA_TYPES = ["yellow_tripdata", "green_tripdata", "fhv_tripdata"]
DEFAULT_DATA_TYPE = "yellow_tripdata"
DEFAULT_YEAR = 2024
DEFAULT_MONTHS = [1, 2, 3]  # January, February, March


def download_file(url: str, filepath: Path, progress: Progress, task_id) -> bool:
    """Download a file with progress tracking."""
    try:
        with httpx.stream("GET", url, timeout=300) as response:
            if response.status_code != 200:
                console.print(f"[red]Error: {response.status_code} for {url}")
                return False
            
            total_size = int(response.headers.get("content-length", 0))
            progress.update(task_id, total=total_size)
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task_id, advance=len(chunk))
            
            return True
    except Exception as e:
        console.print(f"[red]Download failed: {e}")
        return False


def get_data_url(data_type: str, year: int, month: int) -> str:
    """Generate URL for NYC taxi data file."""
    filename = f"{data_type}_{year}-{month:02d}.parquet"
    return urljoin(NYC_TAXI_BASE_URL, filename)


def main():
    parser = argparse.ArgumentParser(description="Download NYC Taxi trip data")
    parser.add_argument(
        "--data-type", 
        choices=DATA_TYPES, 
        default=DEFAULT_DATA_TYPE,
        help=f"Type of taxi data to download (default: {DEFAULT_DATA_TYPE})"
    )
    parser.add_argument(
        "--year", 
        type=int, 
        default=DEFAULT_YEAR,
        help=f"Year to download (default: {DEFAULT_YEAR})"
    )
    parser.add_argument(
        "--months", 
        nargs="+", 
        type=int, 
        default=DEFAULT_MONTHS,
        help=f"Months to download (default: {DEFAULT_MONTHS})"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/raw"),
        help="Output directory for downloaded files"
    )
    parser.add_argument(
        "--sample", 
        action="store_true",
        help="Download only one month for testing"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force re-download even if file exists"
    )
    
    args = parser.parse_args()
    
    # Use only first month if sample mode
    if args.sample:
        args.months = [args.months[0]]
        console.print("[yellow]Sample mode: downloading only one month")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[green]Downloading {args.data_type} data for {args.year}")
    console.print(f"[green]Months: {args.months}")
    console.print(f"[green]Output directory: {args.output_dir}")
    
    downloaded_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        for month in args.months:
            url = get_data_url(args.data_type, args.year, month)
            filename = Path(url).name
            filepath = args.output_dir / filename
            
            # Check if file already exists
            if filepath.exists() and not args.force:
                console.print(f"[yellow]File already exists: {filepath}")
                downloaded_files.append(filepath)
                continue
            
            task_id = progress.add_task(
                f"Downloading {filename}", 
                total=None
            )
            
            console.print(f"[blue]Downloading: {url}")
            
            if download_file(url, filepath, progress, task_id):
                console.print(f"[green]✓ Downloaded: {filepath}")
                downloaded_files.append(filepath)
            else:
                console.print(f"[red]✗ Failed to download: {filename}")
                progress.remove_task(task_id)
    
    # Summary
    console.print(f"\n[green]Downloaded {len(downloaded_files)} files:")
    for filepath in downloaded_files:
        file_size = filepath.stat().st_size / (1024 * 1024)  # MB
        console.print(f"  {filepath.name} ({file_size:.1f} MB)")
    
    if downloaded_files:
        console.print(f"\n[green]Data ready for processing!")
        console.print(f"[blue]Next steps:")
        console.print(f"  make validate-data  # Validate downloaded data")
        console.print(f"  make train-baseline # Train a baseline model")
    else:
        console.print(f"[red]No files downloaded successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()