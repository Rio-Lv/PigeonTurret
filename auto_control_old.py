import sys
import time
import json
import math
import threading
import argparse
import serial
import cv2
from ultralytics import YOLO
import serial 
# ======== CONFIGURATION ========
# --- Stream and Model ---
STREAM_URL = "tcp://192.168.1.120:3333" # Video stream URL
MODEL_PATH = "yolov8n.pt"                # Path to your YOLO model
TARGET_CLASSES = ["cup"]  # Classes to detect
MIN_CONFIDENCE = 0.7  # Minimum confidence for detection

# --- Arduino Communication ---
BAUD_RATE = 115200
# This MUST match the BUFFER_SIZE in the Arduino sketch
BUFFER_SIZE = 4

# --- Motion Control ---
# Maps the camera view to the stepper motor's coordinate space.
STEPS_PER_SCREEN_WIDTH = 1500
LIMIT = STEPS_PER_SCREEN_WIDTH/2
MIN_MOVE_DISTANCE = 0.05
# ===============================

# Initialize YOLO model
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ YOLO model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    sys.exit(1)
    

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

def get_target_coordinates(results, frame_shape):
    """
    Return (dx_norm, dy_norm) for the *nearest* object that
    • is in TARGET_CLASSES, and
    • has detector confidence ≥ MIN_CONFIDENCE.

    Offsets are normalised to [-1, 1]:
        +x → right,  +y → down.
    Prints the class and confidence of the chosen detection.
    Falls back to (0.0, 0.0) if none qualify.
    """
    target_set = {cls.lower() for cls in TARGET_CLASSES}

    try:
        if not results or not results[0]:
            return 0.0, 0.0

        h, w = frame_shape[:2]
        cx_frame, cy_frame = w / 2.0, h / 2.0

        best_dx = best_dy = None
        best_cls = None
        best_conf = None
        min_d2 = float("inf")

        r = results[0]
        for i in range(len(r.boxes.xyxy)):
            label = model.names[int(r.boxes.cls[i])]
            conf  = float(r.boxes.conf[i])

            # Apply class + confidence filters
            if label.lower() not in target_set or conf < MIN_CONFIDENCE:
                continue

            # Compute squared distance of box‑centre to frame‑centre
            x1, y1, x2, y2 = map(float, r.boxes.xyxy[i])
            dx = (x1 + x2) / 2.0 - cx_frame
            dy = (y1 + y2) / 2.0 - cy_frame
            d2 = dx * dx + dy * dy

            if d2 < min_d2:
                min_d2   = d2
                best_dx  = dx
                best_dy  = dy
                best_cls = label
                best_conf = conf

        if best_dx is None:             # nothing matched both filters
            print("⚠️  No target class ≥ 70 % confidence found.")
            return 0.0, 0.0

        # Normalise to [-1, 1] and clamp
        dx_norm = max(min(best_dx / (w / 2.0), 1.0), -1.0)
        dy_norm = max(min(best_dy / (h / 2.0), 1.0), -1.0)

        print(f"🔍 Closest target: {best_cls}  (confidence {best_conf*100:.1f} %)")
        return dx_norm, dy_norm

    except Exception as e:
        print(f"❌ Error finding closest target: {e}")
        return 0.0, 0.0

def go(ser, coord):
    """Formats and sends a move command to the Arduino."""
    command_str = json.dumps(coord) + '\n'
    print(f"📤 Sending: {command_str.strip()}...")
    ser.write(command_str.encode('utf-8'))
    response = ser.readline().decode().strip()
    print(f"Arduino acknowledged final move: '{response}'")
    
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
    
    try:
        ser = serial.Serial(arduino_port, BAUD_RATE, timeout=10)
        time.sleep(2)
        print(f"Arduino says: {ser.readline().decode().strip()}")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {arduino_port}. Details: {e}")
        return
    
    global_coord = {"x": 0, "y": 0}  # Global coordinate reference for the turret
    # also acts as max turn helper max abs(X) = 1000 , abs(Y) = 1000
    
    
    while True:                         # run until you ^C
        ret, frame = camera.read()      # <- use the helper
        if not ret:
            time.sleep(0.05)          # give the reader thread time
            continue

        results = model(frame, verbose=False)
        dx, dy  = get_target_coordinates(results, frame.shape)
        
        d = math.sqrt(dx * dx + dy * dy)
        if d < MIN_MOVE_DISTANCE:  # No need to move if target is very close
            print("🔍 Target is close enough, not moving.")
            continue
        
        dx *= STEPS_PER_SCREEN_WIDTH
        dy *= -STEPS_PER_SCREEN_WIDTH
        dx /= 2.0  # Convert to motor steps
        dy /= 2.0  # Convert to motor steps
        print(f"🔍 Detected target: {dx}, {dy}")
        x = global_coord["x"] + dx
        y = global_coord["y"] + dy
        
        
        if x > LIMIT:
            x = LIMIT
        elif x < -LIMIT:
            x = -LIMIT
        if y > LIMIT:
            y = LIMIT
        elif y < -LIMIT:
            y = -LIMIT

        coord = {"x": x, "y": y}
        go(ser, coord)  # Send the coordinates to the Arduino
        global_coord["x"] = x
        global_coord["y"] = y
        time.sleep(0.5)


if __name__ == "__main__":
    main()