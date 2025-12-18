<#
.SYNOPSIS
Build ScreenRecorder executable using PyInstaller.

.DESCRIPTION
This script installs PyInstaller 6.17.0, builds the ScreenRecorder executable from the .spec file,
moves it to the project root, and cleans up build artifacts.

.USAGE
Run this script from the project root folder:
    .\build_exe.ps1
#>

# Install or update PyInstaller
python -m pip install --no-cache-dir pyinstaller==6.17.0
# Build the executable
pyinstaller --clean ScreenRecorder.spec
# Move the executable to the project root
Move-Item -Path .\dist\ScreenRecorder.exe -Destination .\ -Force
# Remove build artifacts
Remove-Item -Recurse -Force .\build, .\dist
Write-Host "Build completed. ScreenRecorder.exe is now in the project root."
