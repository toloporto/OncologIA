# Cleanup Script for OncologIA
# Removes temporary files and obsolete scripts

Write-Host "Starting cleanup process..." -ForegroundColor Cyan

# Define exact files to remove
$filesToRemove = @(
    "MANUAL_PSICOWEBAI.md",
    "requirements_week1.txt",
    "week1_data_curation.py",
    "test_api.ps1",
    "inspect_mr.py",
    "create_dummy_pdf.py",
    "create_dummy_pdf_robust.py",
    "debug_fhir.py",
    "debug_imports.py",
    "check_models.py",
    "train_psycho.py",
    "fhir_export_test.json"
)

# Define directories to remove
$dirsToRemove = @(
    ".mypy_cache",
    ".tmp.driveupload",
    "ffmpeg_temp"
)

# Remove specific files
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "Deleted file: $file" -ForegroundColor Green
    } else {
        Write-Host "File not found (already deleted?): $file" -ForegroundColor Yellow
    }
}

# Remove directories
foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force
        Write-Host "Deleted directory: $dir" -ForegroundColor Green
    }
}

# Recursively remove __pycache__ directories
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "Deleted cache: $($_.FullName)" -ForegroundColor DarkGray
}

Write-Host "Cleanup complete." -ForegroundColor Cyan
