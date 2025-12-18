import argparse
import ctypes
import os
import re
import shlex
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
import keyboard
from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
from pycaw.pycaw import AudioUtilities

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.join(sys._MEIPASS, "dependencies")
else:
    BASE_DIR = os.path.join(os.getcwd(), "dependencies")

FFMPEG_EXE = os.path.join(BASE_DIR, "ffmpeg.exe")
VB_CABLE_INF = os.path.join(BASE_DIR, "vbMmeCable64_win10.inf")
AUDIOREPEATER_EXE = os.path.join(BASE_DIR, "audiorepeater.exe")

_console_handler_ref = None
_cleanup_done = False

def cleanup_audio():
    """
    Safely cleans up audio resources.
    This function is idempotent and can be called multiple times safely.
    """
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    stop_audiorepeater()
    uninstall_vb_cable()

def register_console_close_handler():
    """
    Registers a Windows console control handler to clean up audio resources
    on console close, user logoff, or system shutdown.
    """
    global _console_handler_ref

    def _console_close_handler(event):
        # CTRL_CLOSE_EVENT (2), CTRL_LOGOFF_EVENT (5), CTRL_SHUTDOWN_EVENT (6)
        if event in (2, 5, 6):
            cleanup_audio()
        return False

    _handler_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
    _console_handler_ref = _handler_type(_console_close_handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_handler_ref, True)

def ensure_admin(args=None):
    """
    Ensures the script is running with administrative privileges.
    If not, it restarts the script as an administrator and exits the current process.
    """
    if not ctypes.windll.shell32.IsUserAnAdmin() and not any(arg in sys.argv for arg in ('-h', '--help')):
        if getattr(sys, 'frozen', False):
            arguments = " ".join(f'"{a}"' for a in sys.argv[1:])
        else:
            arguments = " ".join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, arguments, None, 1)
        os._exit(0)

def restart_audio_services():
    """
    Restarts Windows audio services (Audiosrv and AudioEndpointBuilder) to ensure
    audio endpoints are fully reinitialized after driver installation or removal.
    """
    subprocess.run([
        "powershell", "-Command",
        "Stop-Service Audiosrv -Force; "
        "Stop-Service AudioEndpointBuilder -Force; "
        "Start-Service AudioEndpointBuilder; "
        "Start-Service Audiosrv"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Audio services restarted.")

def install_vb_cable():
    """
    Installs the VB-Audio Virtual Cable driver using pnputil.
    Prints installation status and warnings if any occur.
    """
    result = subprocess.run(["pnputil", "/add-driver", VB_CABLE_INF, "/install"], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("Warning: VB-Cable installation returned non-zero code!")
    else:
        print("VB-Cable installed successfully.")
    time.sleep(1)
    restart_audio_services()

def uninstall_vb_cable():
    """
    Uninstalls the VB-Audio Virtual Cable driver using pnputil.
    Restarts audio services to fully release any endpoints.
    """
    subprocess.run(["pnputil", "/delete-driver", VB_CABLE_INF, "/uninstall"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("VB-Cable uninstalled successfully.")
    restart_audio_services()

def set_vb_audio_default():
    """
    Sets the VB-Audio Virtual Cable devices as the default playback (render) and recording (capture) devices.
    Ensures system audio is routed through the virtual cable.
    """
    devices_render = AudioUtilities.GetAllDevices(data_flow=EDataFlow.eRender.value, device_state=DEVICE_STATE.ACTIVE.value)
    vb_render = next((d for d in devices_render if "vb-audio virtual cable" in d.FriendlyName.lower() and "16" not in d.FriendlyName), None)
    if vb_render:
        AudioUtilities.SetDefaultDevice(vb_render.id, roles=[ERole.eConsole, ERole.eCommunications])
    devices_capture = AudioUtilities.GetAllDevices(data_flow=EDataFlow.eCapture.value, device_state=DEVICE_STATE.ACTIVE.value)
    vb_capture = next((d for d in devices_capture if d.FriendlyName == "CABLE Output (VB-Audio Virtual Cable)"), None)
    if vb_capture:
        AudioUtilities.SetDefaultDevice(vb_capture.id, roles=[ERole.eConsole, ERole.eCommunications])
    print("VB-Audio devices set to default.")

def start_audiorepeater(output_device):
    """
    Starts the AudioRepeater application to route system audio to the specified output device.
    Runs the process hidden in the background using PowerShell.
    """
    subprocess.run(["powershell", "-Command", (
        f'Start-Process -FilePath "{AUDIOREPEATER_EXE}" '
        f'-ArgumentList \'/Input:"CABLE Output (VB-Audio Virtual" '
        f'/Output:"{output_device}" '
        f'/AutoStart\' '
        f'-WindowStyle Hidden'
    )])
    print("AudioRepeater started.")

def stop_audiorepeater():
    """
    Stops any running AudioRepeater processes forcefully.
    Suppresses errors if the process is not found.
    """
    try:
        subprocess.run(
            ["powershell", "-Command", 'Stop-Process -Name "audiorepeater" -Force'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        pass
    print("AudioRepeater stopped.")

def flash_screen(duration=100, alpha=0.02):
    root = tk.Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.attributes("-alpha", alpha)
    root.config(bg="white")
    root.after(duration, root.destroy)
    root.mainloop()

def flash_screen_async(duration=100, alpha=0.02):
    threading.Thread(target=flash_screen, args=(duration, alpha), daemon=True).start()

def main(args):
    """
    Main function that handles recording setup and execution.

    Steps:
    1. Determines output file path and creates recordings directory if needed.
    2. Detects system audio and microphone devices if requested.
    3. Installs and configures VB-Audio Virtual Cable if system audio recording is enabled.
    4. Builds the FFmpeg command for screen capture with optional audio inputs.
    5. Prompts the user with recording parameters before starting.
    6. Executes the FFmpeg command to start recording.
    """
    if args.output:
        output_file = args.output
    else:
        recordings_dir = os.path.join(os.getcwd(), "recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        output_file = os.path.join(recordings_dir, f"Recording_{datetime.now():%Y%m%d_%H%M%S}.mp4")
        
    system_audio, microphone = args.system_audio, args.microphone
    if microphone:
        input_device = next(
            d for d in AudioUtilities.GetAllDevices(
                EDataFlow.eCapture.value,
                DEVICE_STATE.ACTIVE.value
            )
            if d.id == AudioUtilities.GetMicrophone().GetId()
        ).FriendlyName
    if system_audio:
        output_device = AudioUtilities.GetSpeakers().FriendlyName

    # Build FFmpeg command
    cmd = [
        FFMPEG_EXE, '-y', '-f', 'gdigrab',
        '-framerate', str(args.fps),
        '-video_size', args.resolution,
        '-draw_mouse', '1' if args.show_mouse else '0',
        '-i', 'desktop'
    ]
    audio_inputs = []
    if system_audio:
        cmd += ['-f', 'dshow', '-i', 'audio=CABLE Output (VB-Audio Virtual Cable)']
        audio_inputs.append((1, 600, '[a_sys]'))
    if microphone:
        cmd += ['-f', 'dshow', '-i', f'audio={input_device}']
        audio_inputs.append((len(audio_inputs)+1, 1200 if system_audio else 500, '[a_mic]' if system_audio else '[a_out]'))
    audio_filters = []
    audio_map = ''
    if audio_inputs:
        audio_filters = [f'[{i}:a]adelay={d}|{d}{l}' for i,d,l in audio_inputs]
        if len(audio_inputs) == 2:
            audio_filters.append(f'{audio_inputs[0][2]}{audio_inputs[1][2]}amerge=inputs=2[a_out]')
            audio_map = '-map [a_out]'
        else:
            audio_map = f'-map {audio_inputs[0][2]}'
    if audio_filters:
        cmd += ['-filter_complex', ';'.join(audio_filters)]
    cmd += ['-map', '0:v']
    if audio_map:
        cmd += shlex.split(audio_map)
    cmd += ['-c:v', 'libx264', '-crf', '20', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p']
    if audio_filters:
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-ac', '2']
    cmd += ['-threads', '0']
    if args.duration:
        cmd += ['-t', str(args.duration + 4)]
    cmd += [output_file]
    
    print(
        f"ScreenRecorder\n\n"
        f"Parameters:\n"
        f"  Resolution: {args.resolution}\n"
        f"  FPS: {args.fps}"
        f"{f'\n  System audio: {output_device}' if system_audio else ''}"
        f"{f'\n  Microphone: {input_device}' if microphone else ''}"
        f"\n  Mouse: {'Yes' if args.show_mouse else 'No'}"
        f"{f'\n  Duration: {args.duration}s' if args.duration else ''}"
        f"\n  Output file: {output_file}\n"
    )

    if system_audio:
        print("\nPreparing system audio...")
        install_vb_cable()
        set_vb_audio_default()
        start_audiorepeater(output_device)
        print("System audio ready!\n")
    
    print("Press Ctrl+F9 to start the recording...")
    flash_screen_async()
    keyboard.wait('ctrl+f9')
    
    print("\nPreparing to record… starting shortly!\n")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while True:
        if os.path.exists(output_file):
            time.sleep(2)
            flash_screen_async()
            print(f"\nRecording started!", flush=True)
            if not args.duration: print("Press Ctrl+F10 to stop the recording...")
            break
        time.sleep(0.1)

    if args.duration:
        proc.wait()
        flash_screen_async()
    else:
        keyboard.wait('ctrl+f10')
        flash_screen_async()
        proc.stdin.write(b'q\n')
        proc.stdin.flush()
        proc.wait()
    print("\nRecording stopped!")

    tmp = output_file + ".tmp.mp4"
    result = subprocess.run(
        [FFMPEG_EXE, "-i", output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    h, m_, s = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stdout).groups()
    duration = int(h)*3600 + int(m_)*60 + float(s)
    subprocess.run([
        FFMPEG_EXE, "-y", "-i", output_file,
        "-ss", str(4 if duration > 4 else 0),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        tmp
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, output_file)
    print(f"Recording saved to: {output_file}\n")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description=(
                "Screen recorder for Windows 10/11 64-bit (MP4 output) with configurable "
                "resolution, frame rate, system audio, microphone, mouse cursor, recording duration, "
                "console visibility, and output path. "
                "Press Ctrl+F9 to start recording and Ctrl+F10 to stop. "
                "A brief flash appears when the program is ready to start recording, "
                "and additional flashes indicate the start and end of the recording."
            )
        )
        parser.add_argument('--resolution', type=str, default="1920x1080", help='Video resolution in WIDTHxHEIGHT format (default: 1920x1080)')
        parser.add_argument('--fps', type=int, default=15, help='Frames per second for the recording (default: 15)')
        parser.add_argument('--system-audio', action='store_true', help='Enable recording of system audio through VB-Audio Virtual Cable (default: False)')
        parser.add_argument('--microphone', action='store_true', help='Enable recording from the default microphone (default: False)')
        parser.add_argument('--show-mouse', action='store_true', help='Include mouse cursor in the recording (default: False)')
        parser.add_argument('--duration', type=int, default=None, help='Recording duration in seconds (default: unlimited until Ctrl+F10)')
        parser.add_argument('--silently', action='store_true', help='Start recording silently (console hidden)')
        parser.add_argument('--output', type=str, default=None, help='Output file path (default: .\\recordings\\Recording_YYYYMMDD_HHMMSS.mp4)')
        args = parser.parse_args()
        if args.system_audio:
            register_console_close_handler()
        ensure_admin(args)
        main(args)
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if 'args' in globals() and args.system_audio:
            cleanup_audio()
            if not args.silently:
                input("Press Enter to exit...")
