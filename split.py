import subprocess
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from rich.prompt import Prompt

console = Console()

def find_unrar():
    """
    Auto-detects UnRAR.exe binary across common Windows installation paths.
    Returns: Absolute path string if found, else None.
    """
    standard_paths = [
        r"C:\Program Files\WinRAR\UnRAR.exe",
        r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
        os.path.join(os.getcwd(), "UnRAR.exe")
    ]
    for path in standard_paths:
        if os.path.exists(path):
            return path
    return None

def print_banner():
    """Displays the professional tool branding and version info."""
    banner = """[bold cyan]
     ██████╗ ██████╗ ███╗   ███╗██████╗  ██████╗ ██╗     ██╗███████╗████████╗
    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔═══██╗██║     ██║██╔════╝╚══██╔══╝
    ██║     ██║   ██║██╔████╔██║██████╔╝██║   ██║██║     ██║███████╗   ██║   
    ██║     ██║   ██║██║╚██╔╝██║██╔══██╗██║   ██║██║     ██║╚════██║   ██║   
    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝╚██████╔╝███████╗██║███████║   ██║   
     ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚═╝╚══════╝   ╚═╝   
                                                                             
    ███████╗██████╗ ██╗     ██╗████████╗████████╗███████╗██████╗ 
    ██╔════╝██╔══██╗██║     ██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
    ███████╗██████╔╝██║     ██║   ██║      ██║   █████╗  ██████╔╝
    ╚════██║██╔═══╝ ██║     ██║   ██║      ██║   ██╔══╝  ██╔══██╗
    ███████║██║     ███████╗██║   ██║      ██║   ███████╗██║  ██║
    ╚══════╝╚═╝     ╚══════╝╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝
    [/bold cyan]
    [bold yellow]   Advanced Large Archive Stream Processor | Production Ready | t.me/tomnuongcay [/bold yellow]
    """
    console.print(banner)

def main():
    """Main execution flow for high-performance archive splitting."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    console.print(Panel.fit(
        "[bold green]SYSTEM STATUS:[/bold green] IDLE | [bold magenta]VERSION:[/bold magenta] 1.0.0", 
        border_style="blue"
    ))

    # Binary validation: Ensures UnRAR is available for stream extraction
    unrar_binary = find_unrar()
    if not unrar_binary:
        console.print("[red]❌ CRITICAL ERROR: UnRAR.exe not found. Please install WinRAR.[/red]")
        input("Press Enter to exit..."); return

    # User Configuration Input
    source_rar = Prompt.ask("[bold green]➜ Source RAR file[/bold green]").strip('"')
    output_base = Prompt.ask("[bold green]➜ Output directory[/bold green]")
    size_input = Prompt.ask("[bold green]➜ Size per part (e.g., 1GB/500MB)[/bold green]", default="1GB")
    batch_size = int(Prompt.ask("[bold green]➜ Parts per batch (Pause after X files)[/bold green]", default="20"))
    start_offset = int(Prompt.ask("[bold green]➜ Start from Part No.[/bold green]", default="1"))

    # Dynamic unit conversion for stream management
    try:
        if "MB" in size_input.upper():
            bytes_per_part = int(size_input.upper().replace("MB", "")) * 1024 * 1024
        else:
            bytes_per_part = int(float(size_input.upper().replace("GB", "")) * 1024 * 1024 * 1024)
    except Exception:
        console.print("[red]❌ ERROR: Invalid size format. Use 1GB or 500MB.[/red]"); return

    if not os.path.exists(output_base):
        os.makedirs(output_base)

    # Core Logic: Extracting archive content to stdout pipe for live splitting
    extraction_cmd = f'"{unrar_binary}" p -inul "{source_rar}"'
    
    try:
        # High-performance buffer allocation (256MB)
        process = subprocess.Popen(
            extraction_cmd, 
            stdout=subprocess.PIPE, 
            shell=True, 
            bufsize=256*1024*1024
        )
        
        # Resume/Skip logic for interrupted workloads
        if start_offset > 1:
            skip_bytes = (start_offset - 1) * bytes_per_part
            with console.status(f"[bold magenta]Fast-forwarding stream to Part {start_offset}...[/bold magenta]"):
                process.stdout.read(skip_bytes)

        part_id = start_offset
        while True:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console
            ) as progress:
                
                batch_total = bytes_per_part * batch_size
                task_tracker = progress.add_task("Streaming raw data...", total=batch_total)

                for _ in range(batch_size):
                    fname = f"part_{part_id:04d}.txt"
                    fpath = os.path.join(output_base, fname)
                    
                    # Buffer-through write strategy for high IOPS efficiency
                    with open(fpath, "wb") as f:
                        current_read = 0
                        while current_read < bytes_per_part:
                            chunk = process.stdout.read(min(100 * 1024 * 1024, bytes_per_part - current_read))
                            
                            if not chunk:
                                if current_read == 0:
                                    console.print("\n[bold green]✅ WORKLOAD COMPLETE: Archive processed successfully.[/bold green]")
                                    process.terminate()
                                    return
                                break
                            
                            f.write(chunk)
                            current_read += len(chunk)
                            progress.update(task_tracker, advance=len(chunk), description=f"[bold yellow]Writing: {fname}")
                        
                        # Handle line-break integrity
                        f.write(process.stdout.readline())
                    
                    part_id += 1

            # Resource management checkpoint
            console.print(Panel(
                f"[bold green]BATCH SUCCESS: {batch_size} PARTS GENERATED[/bold green]\n"
                f"Checkpoint reached at: [cyan]part_{part_id-1:04d}.txt[/cyan]\n"
                f"Recommended: Move files from [yellow]{output_base}[/yellow] before proceeding.",
                title="RESOURCE CHECKPOINT"
            ))
            input("➔ Press Enter to resume next batch..."); console.print("[italic]Resuming data stream...[/italic]")

    except Exception as e:
        console.print(f"[bold red]CRITICAL EXCEPTION: {e}[/bold red]")
    finally:
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main()