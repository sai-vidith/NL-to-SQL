# Nexus GitHub Repository Split and Push Script
# This script initializes separate Git repositories for frontend and backend and pushes them to distinct GitHub remotes.

$BackendDir = Resolve-Path "$PSScriptRoot\..\backend"
$FrontendDir = Resolve-Path "$PSScriptRoot\..\frontend"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Nexus Repository Split & Deploy Tool" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Function to push a single directory to a specific Git URL
function Deploy-Folder {
    param(
        [string]$Path,
        [string]$Name,
        [string]$RemoteUrl
    )

    Write-Host "Processing $Name repository at $Path..." -ForegroundColor Yellow
    Push-Location $Path

    # Initialize git if not already present
    if (-not (Test-Path ".git")) {
        Write-Host "Initializing Git repository..." -ForegroundColor DarkGray
        git init -b main
    }

    # Setup standard gitignore if missing
    if (-not (Test-Path ".gitignore")) {
        if ($Name -eq "Backend") {
            Set-Content -Path ".gitignore" -Value @(
                "__pycache__/",
                "*.py[cod]",
                "*$py.class",
                ".env",
                "nlsql.db",
                "venv/",
                ".pytest_cache/",
                ".coverage"
            )
        } else {
            Set-Content -Path ".gitignore" -Value @(
                "node_modules/",
                "dist/",
                "*.local",
                ".eslintcache",
                ".vite"
            )
        }
    }

    # Stage files
    git add .
    
    # Check if there are changes to commit
    $status = git status --porcelain
    if ($status) {
        git commit -m "Deploy Nexus $Name to GitHub"
    } else {
        Write-Host "No new changes to commit." -ForegroundColor DarkGray
    }

    # Add or update remote
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        if ($existingRemote -ne $RemoteUrl) {
            git remote set-url origin $RemoteUrl
            Write-Host "Updated remote origin to $RemoteUrl" -ForegroundColor DarkGray
        }
    } else {
        git remote add origin $RemoteUrl
        Write-Host "Added remote origin: $RemoteUrl" -ForegroundColor DarkGray
    }

    # Push to main
    Write-Host "Pushing to remote origin main..." -ForegroundColor Green
    git push -u origin main

    Pop-Location
    Write-Host "Done deploying $Name repo!`n" -ForegroundColor Green
}

# Ask user for GitHub remote URLs
$BackendUrl = Read-Host "Enter GitHub Repository URL for Backend (e.g. https://github.com/user/nexus-backend.git)"
$FrontendUrl = Read-Host "Enter GitHub Repository URL for Frontend (e.g. https://github.com/user/nexus-frontend.git)"

if ([string]::IsNullOrWhiteSpace($BackendUrl) -or [string]::IsNullOrWhiteSpace($FrontendUrl)) {
    Write-Error "Both Repository URLs are required. Operation cancelled."
    exit
}

# Deploy
Deploy-Folder -Path $BackendDir -Name "Backend" -RemoteUrl $BackendUrl
Deploy-Folder -Path $FrontendDir -Name "Frontend" -RemoteUrl $FrontendUrl

Write-Host "Both repositories have been pushed to GitHub successfully!" -ForegroundColor Cyan
