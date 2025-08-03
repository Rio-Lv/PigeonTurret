import cv2
import subprocess
import numpy as np

# --- Configuration ---
WIDTH, HEIGHT = 640, 480
FPS = 24
GRID_COLOR = (0, 255, 0)  # Green
GRID_LINES = 5
STREAM_PORT = 3333

def draw_grid(frame):
    """
    Draws a grid on the given frame.
    """
    h, w, _ = frame.shape
    # Draw vertical lines
    for i in range(1, GRID_LINES):
        x = int(w * i / GRID_LINES)
        cv2.line(frame, (x, 0), (x, h), GRID_COLOR, 1)
    # Draw horizontal lines
    for i in range(1, GRID_LINES):
        y = int(h * i / GRID_LINES)
        cv2.line(frame, (0, y), (w, y), GRID_COLOR, 1)
    return frame

def main():
    """
    Captures video, draws a grid, displays it locally, and streams it.
    """
    print("[*] Starting video capture...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    # Command to stream video using ffmpeg and netcat
    # This command will listen for connections on the specified port
    stream_command = [
        'ffmpeg',
        '-f', 'rawvideo',
        '-pixel_format', 'bgr24',
        '-s', f'{WIDTH}x{HEIGHT}',
        '-r', str(FPS),
        '-i', '-',
        '-f', 'mpegts',
        '-b:v', '800k',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        'pipe:1'
    ]

    nc_command = ['nc', '-l', '-k', '-p', str(STREAM_PORT)]

    print(f"[*] Starting stream: {' '.join(stream_command)} | {' '.join(nc_command)}")

    # Start the ffmpeg process
    ffmpeg_process = subprocess.Popen(stream_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    # Start the netcat process, piping ffmpeg's output to it
    nc_process = subprocess.Popen(nc_command, stdin=ffmpeg_process.stdout)


    cv2.namedWindow("Video Feed with Grid", cv2.WINDOW_NORMAL)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[!] Error: Failed to grab frame.")
                break

            # Draw the grid on the frame
            frame_with_grid = draw_grid(frame.copy())

            # Display the frame locally
            cv2.imshow("Video Feed with Grid", frame_with_grid)

            # Write the frame with the grid to ffmpeg's stdin
            try:
                ffmpeg_process.stdin.write(frame_with_grid.tobytes())
            except (BrokenPipeError, IOError):
                print("[!] ffmpeg process has closed. Restarting...")
                # Restart the processes if the pipe breaks
                ffmpeg_process.kill()
                nc_process.kill()
                ffmpeg_process = subprocess.Popen(stream_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                nc_process = subprocess.Popen(nc_command, stdin=ffmpeg_process.stdout)


            # Check for 'q' key to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[*] Stopping...")
                break
    finally:
        print("[*] Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        # Terminate the streaming processes
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        nc_process.kill()
        print("[*] Done.")

if __name__ == "__main__":
    main()
