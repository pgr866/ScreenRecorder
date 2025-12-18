<#
.SYNOPSIS
Downloads and extracts required dependencies for ScreenRecorder.

.DESCRIPTION
This script downloads FFmpeg, VB-CABLE Virtual Audio Device, and Audio Repeater MME,
extracts only the necessary files into the 'dependencies' folder, and cleans up temporary files.
It ensures that all tools required for recording system audio and microphone input
are available locally without polluting the project root.

DEPENDENCIES FOLDER STRUCTURE AFTER RUNNING:
- dependencies\ffmpeg.exe
- dependencies\vbaudio_cable64_win10.cat
- dependencies\vbaudio_cable64_win10.sys
- dependencies\vbMmeCable64_win10.inf
- dependencies\audiorepeater.exe

USAGE:
Run this script from the project root:
    .\setup_dependencies.ps1
#>

# Path to the dependencies folder
$dependenciesPath = "$PSScriptRoot\dependencies"
New-Item $dependenciesPath -ItemType Directory -Force | Out-Null

# --- FFmpeg 8.0.1 Essentials Build ---
$ffmpegZipPath = "$dependenciesPath\ffmpeg.zip"
$ffmpegZipUrl = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.0.1-essentials_build.zip"
$ffmpegExtractedFolder = "$dependenciesPath\ffmpeg-8.0.1-essentials_build"
Invoke-WebRequest $ffmpegZipUrl -OutFile $ffmpegZipPath
Expand-Archive $ffmpegZipPath $dependenciesPath -Force
Copy-Item "$ffmpegExtractedFolder\bin\ffmpeg.exe" $dependenciesPath -Force
Remove-Item $ffmpegExtractedFolder, $ffmpegZipPath -Recurse -Force

# --- VB-CABLE Virtual Audio Device 2.1.5.8 ---
$vbCableZipUrl = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip"
$vbCableZipPath = "$dependenciesPath\VBCABLE_Driver_Pack45.zip"
$vbCableExtractedFolder = "$dependenciesPath\VBCABLE_Driver_Pack45"
Invoke-WebRequest $vbCableZipUrl -OutFile $vbCableZipPath
Expand-Archive $vbCableZipPath $vbCableExtractedFolder -Force
Copy-Item "$vbCableExtractedFolder\vbaudio_cable64_win10.cat" $dependenciesPath -Force
Copy-Item "$vbCableExtractedFolder\vbaudio_cable64_win10.sys" $dependenciesPath -Force
Copy-Item "$vbCableExtractedFolder\vbMmeCable64_win10.inf" $dependenciesPath -Force
Remove-Item $vbCableExtractedFolder, $vbCableZipPath -Recurse -Force

# --- Audio Repeater MME 1.61.0.4937 ---
$audioRepeaterZipUrl = "https://software.muzychenko.net/freeware/audio_repeater_mme_1_61_0_ks_1_90_0.zip"
$audioRepeaterZipPath = "$dependenciesPath\audio_repeater.zip"
$audioRepeaterExtractedFolder = "$dependenciesPath\audio_repeater_temp"
Invoke-WebRequest $audioRepeaterZipUrl -OutFile $audioRepeaterZipPath
Expand-Archive $audioRepeaterZipPath $audioRepeaterExtractedFolder -Force
Copy-Item "$audioRepeaterExtractedFolder\x64\audiorepeater.exe" $dependenciesPath -Force
Remove-Item $audioRepeaterExtractedFolder, $audioRepeaterZipPath -Recurse -Force
