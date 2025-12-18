# 🎥 ScreenRecorder

Screen recorder for **Windows 10/11 64-bit** (MP4 output) with configurable resolution, frame rate, system audio, microphone, mouse cursor, recording duration, console visibility, and output path. **Press Ctrl+F9 to start recording and Ctrl+F10 to stop.** A brief flash appears when the program is ready to start recording, and additional flashes indicate the start and end of the recording.

# ⚡ Quick Start

If you just want to use the recorder without building it yourself, download the precompiled executable from the **[Releases](https://github.com/yourusername/yourproject/releases)** section.
Place it anywhere on your system and run it from the terminal with the desired parameters. For example:

```powershell
.\ScreenRecorder.exe --resolution 1920x1080 --fps 15 --system-audio --microphone
```

This will launch the screen recorder with 1080p resolution, 15 FPS, recording both system audio and microphone input.

## 📝 Usage

Below is the command-line interface for the screen recorder. You can use these options when running `main.py` directly or the precompiled `ScreenRecorder.exe`.

```powershell
usage: ScreenRecorder.exe [-h] [--resolution RESOLUTION] [--fps FPS] [--system-audio] [--microphone] [--show-mouse] [--duration DURATION] [--silently] [--output OUTPUT]

Screen recorder for Windows 10/11 (MP4 output) with optional system audio, microphone, mouse cursor, console hiding, and custom output path. Press Ctrl+F9 to start recording
and Ctrl+F10 to stop. A brief flash appears when the program is ready to start recording, and additional flashes indicate the start and end of the recording.

options:
  -h, --help            show this help message and exit
  --resolution RESOLUTION
                        Video resolution in WIDTHxHEIGHT format (default: 1920x1080)
  --fps FPS             Frames per second for the recording (default: 15)
  --system-audio        Enable recording of system audio through VB-Audio Virtual Cable (default: False)
  --microphone          Enable recording from the default microphone (default: False)
  --show-mouse          Include mouse cursor in the recording (default: False)
  --duration DURATION   Recording duration in seconds (default: unlimited until Ctrl+F10)
  --silently            Start recording silently (console hidden)
  --output OUTPUT       Output file path (default: .\recordings\Recording_YYYYMMDD_HHMMSS.mp4)
```

# 🏗️ Building and Running from Source

- Install [Python 3.14.2](https://www.python.org/ftp/python/3.14.2/python-3.14.2-amd64.exe).

- Install Python dependencies:

    ```powershell
    python -m pip install --no-cache-dir -r requirements.txt
    ```
- Run the PowerShell script `setup_dependencies.ps1` in the project root to download and extract FFmpeg, VB-CABLE, and Audio Repeater into the project's `dependencies` folder:

  ```powershell
  .\setup_dependencies.ps1
  ```

- You can now run the screen recorder directly by executing `main.py` with the desired command-line arguments. For example:

    ```powershell
    python main.py --resolution 1920x1080 --fps 15 --system-audio --microphone
    ```

- **(Optional)** Build Executable using PyInstaller from the project root:

  ```powershell
  .\build_exe.ps1
  ```

After building, you can run `.\ScreenRecorder.exe` as a standalone, portable program.

# 🧩 Third-Party Software
- [FFmpeg 8.0.1 Essentials Build](https://www.ffmpeg.org/)
- [VB-CABLE Virtual Audio Device 2.1.5.8](https://vb-audio.com/Cable/)
- [Audio Repeater MME 1.61.0.4937](https://vac.muzychenko.net/en/repeater.htm)
