import os
import shutil
import subprocess
import sys
import zipfile
import tarfile
import rarfile
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

console = Console()

failed_files = []

def extract_7z(file_path, extract_to):
    start_time = time.time()
    try:
        subprocess.check_call(['7z', 'x', file_path, f'-o{extract_to}'])
        elapsed_time = time.time() - start_time
        console.print(f"[green]Extracted {file_path} in {elapsed_time:.2f} seconds.[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error extracting {file_path} with 7z: {e}[/red]")
        failed_files.append(file_path)
        return False

def extract_zip(file_path, extract_to):
    start_time = time.time()
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        elapsed_time = time.time() - start_time
        console.print(f"[green]Extracted {file_path} in {elapsed_time:.2f} seconds.[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Error extracting {file_path} as zip: {e}[/red]")
        failed_files.append(file_path)
        return False

def extract_tar(file_path, extract_to):
    start_time = time.time()
    try:
        with tarfile.open(file_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_to)
        elapsed_time = time.time() - start_time
        console.print(f"[green]Extracted {file_path} in {elapsed_time:.2f} seconds.[/green]")
        return True
    except (tarfile.TarError, ValueError, PermissionError, EOFError) as e:
        console.print(f"[red]Error extracting {file_path} as tar: {e}[/red]")
        failed_files.append(file_path)
        return False

def extract_rar(file_path, extract_to):
    start_time = time.time()
    try:
        with rarfile.RarFile(file_path) as rar_ref:
            rar_ref.extractall(extract_to)
        elapsed_time = time.time() - start_time
        console.print(f"[green]Extracted {file_path} in {elapsed_time:.2f} seconds.[/green]")
        return True
    except rarfile.Error as e:
        console.print(f"[red]Error extracting {file_path} as rar: {e}[/red]")
        failed_files.append(file_path)
        try:
            # Attempt extraction with unrar if rarfile fails
            subprocess.check_call(['unrar', 'x', file_path, extract_to])
            elapsed_time = time.time() - start_time
            console.print(f"[green]Extracted {file_path} with unrar in {elapsed_time:.2f} seconds.[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error extracting {file_path} with unrar: {e}[/red]")
            failed_files.append(file_path)
            return False

def identify_file_type(file_path):
    """Identifies the file type using the `file` command."""
    try:
        result = subprocess.check_output(['file', '--mime-type', '-b', file_path])
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error identifying file type for {file_path}: {e}[/red]")
        return None

def extract_archive(file_path, extract_to):
    """Extracts an archive file to the specified directory."""
    file_type = identify_file_type(file_path)
    if file_type:
        if file_type in ('application/x-7z-compressed', 'application/x-7z'):
            return extract_7z(file_path, extract_to)
        elif file_type == 'application/zip':
            return extract_zip(file_path, extract_to)
        elif file_type in ('application/x-tar', 'application/gzip', 'application/x-bzip2', 'application/x-xz'):
            return extract_tar(file_path, extract_to)
        elif file_type in ('application/vnd.rar', 'application/x-rar'):
            return extract_rar(file_path, extract_to)
        else:
            console.print(f"[yellow]Unsupported file format: {file_path} ({file_type})[/yellow]")
            failed_files.append(file_path)
            return False
    else:
        console.print(f"[red]Could not determine the file type for {file_path}[/red]")
        failed_files.append(file_path)
        return False

def extract_all_archives(root_dir):
    """Recursively extracts all archives in the given directory."""
    total_files = 0
    total_dirs = 0
    successful_extractions = 0
    failed_extractions = 0

    archives = []
    for root, dirs, files in os.walk(root_dir):
        total_dirs += len(dirs)
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            if file_path.endswith(('.7z', '.zip', '.tar.gz', '.tgz', '.tar', '.tar.bz2', '.tbz2', '.tar.xz', '.txz', '.rar')):
                extract_dir = os.path.splitext(file_path)[0]
                os.makedirs(extract_dir, exist_ok=True)
                archives.append((file_path, extract_dir))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda p: extract_archive(*p), archives))

    successful_extractions = sum(1 for result in results if result)
    failed_extractions = len(results) - successful_extractions

    # Recursively extract nested archives
    nested_stats = [extract_all_archives(os.path.splitext(file_path)[0]) for file_path, _ in archives]
    for stats in nested_stats:
        total_files += stats['total_files']
        total_dirs += stats['total_dirs']
        successful_extractions += stats['successful_extractions']
        failed_extractions += stats['failed_extractions']

    # Remove original archives after successful extraction
    for file_path, _ in archives:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except PermissionError as e:
                console.print(f"[red]Error removing file {file_path}: {e}[/red]")

    return {
        'total_files': total_files,
        'total_dirs': total_dirs,
        'successful_extractions': successful_extractions,
        'failed_extractions': failed_extractions
    }

def main():
    if len(sys.argv) != 3 or '--help' in sys.argv:
        console.print("[cyan]Usage: python script.py <archive_path> <extract_to>[/cyan]")
        console.print("\n[cyan]This script extracts the specified archive and all nested archives recursively.[/cyan]")
        console.print("[cyan]Supported archive formats: .7z, .zip, .tar.gz, .tgz, .tar, .tar.bz2, .tbz2, .tar.xz, .txz, .rar[/cyan]")
        sys.exit(1)

    start_time = time.time()
    archive_path = sys.argv[1]
    extract_to = os.path.join(sys.argv[2], os.path.splitext(os.path.basename(archive_path))[0])

    # Validate selection
    if not os.path.isfile(archive_path):
        console.print("[red]Invalid file path, exiting.[/red]")
        sys.exit(1)
    elif not os.path.isdir(extract_to):
        os.makedirs(extract_to)

    # Extract main archive
    console.print(f"[cyan]Extracting main archive: {archive_path}[/cyan]")
    if extract_archive(archive_path, extract_to):
        console.print("[green]Main archive extracted successfully.[/green]")
    else:
        console.print("[red]Failed to extract main archive.[/red]")

    # Recursively extract all nested archives
    stats = extract_all_archives(extract_to)

    # Display statistics
    table = Table(title="Extraction Summary")
    table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta")

    table.add_row("Total files processed", str(stats['total_files']))
    table.add_row("Total directories processed", str(stats['total_dirs']))
    table.add_row("Successful extractions", str(stats['successful_extractions']))
    table.add_row("Failed extractions", str(stats['failed_extractions']))

    console.print(table)

    # Log failed files
    if failed_files:
        console.print("[red]Failed to extract the following files:[/red]")
        for failed_file in failed_files:
            console.print(f"[red]- {failed_file}[/red]")

    elapsed_time = time.time() - start_time
    console.print(f"[green]Extraction complete in {elapsed_time:.2f} seconds.[/green]")

if __name__ == "__main__":
    main()
