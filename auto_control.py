import sys
import time
import json
import math
import threading
import argparse
import serial
import cv2
from ultralytics import YOLO

# ======== CONFIGURATION ========
# --- Stream and Model ---
STREAM_URL = "tcp://192.168.1.120:3333" # Video stream URL
MODEL_PATH = "yolov8n.pt"                # Path to your YOLO model
TARGET_CLASSES = ["pigeon", "bird", "cup", "mug", "glass", "person"]

# --- Arduino Communication ---
BAUD_RATE = 115200
# This MUST match the BUFFER_SIZE in the Arduino sketch
BUFFER_SIZE = 4

# --- Motion Control ---
# Maps the camera view to the stepper motor's coordinate space.
# If an object is at the far right of the screen, the motor will be commanded to go to +MOTION_RANGE_STEPS.
MOTION_RANGE_STEPS = 6000
# ===============================

# Initialize YOLO model
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ YOLO model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    sys.exit(1)

def find_arduino_port():
    """Tries to find a serial port that looks like an Arduino."""
    from serial.tools import list_ports
    print("🔎 Searching for Arduino port...")
    keywords = ("arduino", "usbmodem", "ch340")
    for port in list_ports.comports():
        for keyword in keywords:
            if keyword in port.description.lower() or keyword in port.device.lower():
                print(f"✅ Found potential Arduino on {port.device}")
                return port.device
    return None

def send_move(ser, coord):
    """Formats and sends a move command to the Arduino."""
    command_str = json.dumps(coord) + '\n'
    print(f"📤 Sending: {command_str.strip()}...")
    ser.write(command_str.encode('utf-8'))

class ThreadedCamera:
    """
    A dedicated thread to continuously read frames from a stream,
    preventing the main loop from blocking.
    """
    def __init__(self, stream_url):
        self.video_capture = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
        if not self.video_capture.isOpened():
            raise IOError(f"Cannot open stream: {stream_url}")
        
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Try to keep buffer small
        self.latest_frame = None
        self.last_ret = False
        self.frame_lock = threading.Lock()
        self.running = True
        self.capture_thread = threading.Thread(target=self._reader_loop, daemon=True)

    def _reader_loop(self):
        print("🚀 Capture thread started.")
        while self.running:
            ret, frame = self.video_capture.read()
            with self.frame_lock:
                self.last_ret = ret
                self.latest_frame = frame
            if not ret:
                time.sleep(1) # Wait before retrying

    def start(self):
        self.capture_thread.start()

    def read(self):
        with self.frame_lock:
            return self.last_ret, self.latest_frame

    def release(self):
        self.running = False
        if self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        if self.video_capture.isOpened():
            self.video_capture.release()
        print("📷 Camera released.")

def find_closest_target(results, frame_shape):
    """
    Return (dx, dy) from frame centre to the nearest TARGET_CLASSES object.
    dx > 0 → right, dy > 0 → down. Returns None if none found.
    """
    try:
        if not results or not results[0]:
            return (0,0)

        h, w = frame_shape[:2]
        cx_frame, cy_frame = w // 2, h // 2
        best_dx = best_dy = None
        min_d2 = float("inf")

        r = results[0]
        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
            if model.names[int(cls)] not in TARGET_CLASSES:
                continue
            x1, y1, x2, y2 = map(int, box)
            dx = (x1 + x2) // 2 - cx_frame
            dy = (y1 + y2) // 2 - cy_frame
            d2 = dx * dx + dy * dy
            if d2 < min_d2:
                min_d2 = d2
                best_dx, best_dy = dx, dy
        if best_dx is None or best_dy is None:
            print("⚠️ No target found.")
            return (0, 0)
        return (best_dx, best_dy) 
    except Exception as e:
        print(f"❌ Error finding closest target: {e}")
        return (0, 0)


def main():
    
    # 1. Get Latest Frame
    # 2. Run YOLO Detection
    # 3. Find Closest Target
    # 4. Calculate Coordinates Relative to Global Coordinate
    # 5. Send Coordinates to Arduino
    # 6. wait for 
    print("🔄 Starting main loop...")
    
    camera = ThreadedCamera(STREAM_URL)
    camera.start()
    
    arduino_port = find_arduino_port()
    if not arduino_port:
        print("❌ Error: Could not automatically find Arduino port.")
    
    global_coord = {"x": 0, "y": 0}  # Global coordinate reference for the turret
    # also acts as max turn helper max abs(X) = 1000 , abs(Y) = 1000
    
    while True:                         # run until you ^C
        ret, frame = camera.read()      # <- use the helper
        if not ret:
            time.sleep(0.05)          # give the reader thread time
            continue

        results = model(frame, verbose=False)
        dx, dy  = find_closest_target(results, frame.shape)

        print(f"🔍 Detected target: {dx}, {dy}")
        time.sleep(0.5)



if __name__ == "__main__":
    main()