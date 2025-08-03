import serial
import time
import json
import cv2
import numpy as np
import threading

RPI_IP = "raspberrypi.local"  # CHANGE ME: IP address of your Raspberry Pi
VIDEO_PORT = 3333

STEPS_PER_SCREEN_WIDTH = 1500  # More or less Steps per Screen Width/Height
L = STEPS_PER_SCREEN_WIDTH # Length of the motion range in steps
# List of coordinates to move to in sequence
COORDS = [
    {"x": 0, "y": 0},
    {"x": 0, "y": L/2},
    {"x": 0, "y": 0},
    {"x": 0, "y": -L/2},
    {"x": 0, "y": 0},
    {"x": L/2, "y": 0},
    {"x": 0, "y": 0},
    {"x": -L/2, "y": 0},
]

SERIAL_PORT = '/dev/tty.usbmodem14201'
BAUD_RATE = 115200


def display_video_feed(ip, port):
    """
    Connects to a video stream, displays it, and overlays a 4x4 grid.
    """
    # Note: You might need to have GStreamer installed for this to work.
    # The pipeline would look something like:
    # video_url = (
    #     f"tcpclientsrc host={ip} port={port} ! "
    #     "h264parse ! avdec_h264 ! videoconvert ! appsink"
    # )
    video_url = f"tcp://{ip}:{port}"
    print(f"Connecting to video stream at: {video_url}")

    cap = None
    # Retry connecting a few times
    for _ in range(5):
        cap = cv2.VideoCapture(video_url)
        if cap.isOpened():
            print("Successfully connected to video stream.")
            break
        else:
            print("Failed to connect to video stream, retrying...")
            time.sleep(1)

    if not cap or not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    window_name = "Video Feed with Grid"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended. Closing video window.")
            break

        h, w, _ = frame.shape
        # Draw vertical lines for a 4x4 grid
        for i in range(1, 4):
            x = int(w * i / 4)
            cv2.line(frame, (x, 0), (x, h), (0, 255, 0), 1)
        # Draw horizontal lines
        for i in range(1, 4):
            y = int(h * i / 4)
            cv2.line(frame, (0, y), (w, y), (0, 255, 0), 1)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Video feed closed.")


def find_arduino_port():
    """Try to locate a serial port that looks like an Arduino."""
    from serial.tools import list_ports

    KEYWORDS = ("arduino", "usbmodem", "ch340")
    for port in list_ports.comports():
        for keyword in KEYWORDS:
            if keyword in port.description.lower() or keyword in port.device.lower():
                print(f"Found potential Arduino on {port.device}")
                return port.device
    return None


def go(coords):
    """Send a sequence of absolute coordinates to the Arduino."""
    port = find_arduino_port()
    if not port:
        print("Error: Could not automatically find Arduino port.")
        port = SERIAL_PORT

    print(f"Connecting to Arduino on {port} at {BAUD_RATE} bps...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10)
        time.sleep(2)
        print(f"Arduino says: {ser.readline().decode().strip()}")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port}. Details: {e}")
        return

    print("Starting motion control. Press Ctrl+C to stop.")

    try:
        for coord in coords:
            command_str = json.dumps(coord) + '\n'
            print(f"Sending: {command_str.strip()}...")
            ser.write(command_str.encode('utf-8'))
            response = ser.readline().decode().strip()
            print(f"Arduino acknowledged: '{response}'")

        # Return to origin after completion
        command_obj = {"x": 0, "y": 0}
        command_str = json.dumps(command_obj) + '\n'
        ser.write(command_str.encode('utf-8'))
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
    except KeyboardInterrupt:
        print("\nStopping motion. Returning to origin (0,0)...")
        command_obj = {"x": 0, "y": 0}
        command_str = json.dumps(command_obj) + '\n'
        ser.write(command_str.encode('utf-8'))
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")


if __name__ == "__main__":
    # Start the video feed in a background thread
    video_thread = threading.Thread(
        target=display_video_feed, args=(RPI_IP, VIDEO_PORT)
    )
    video_thread.daemon = True  # Allows main program to exit even if thread is running
    video_thread.start()

    # Give the video thread a moment to initialize and connect.
    # Adjust this delay if the video feed takes longer to appear.
    print("Main thread: Waiting for video feed to establish...")
    time.sleep(5)

    print("Main thread: Starting Arduino motion control.")
    go(COORDS)

    print("Main thread: Motion sequence finished. Program will exit.")
