import sys
import time
import json
import math
import threading
import argparse
import serial
import cv2
import numpy as np # Added for drawing
from ultralytics import YOLO
from serial.tools import list_ports

# ======== CONFIGURATION ========
# --- Stream and Model ---
STREAM_URL = "tcp://192.168.1.120:3333" # Video stream URL
MODEL_PATH = "yolov8n.pt"                # Path to your YOLO model
TARGET_CLASSES = ["mug", "cup"]  # Classes to detect
MIN_CONFIDENCE = 0.7  # Minimum confidence for detection

# --- Arduino Communication ---
BAUD_RATE = 115200
# This MUST match the BUFFER_SIZE in the Arduino sketch
BUFFER_SIZE = 4

# --- Motion Control ---
# Maps the camera view to the stepper motor's coordinate space.
STEPS_PER_SCREEN_WIDTH = 1500
LIMIT = STEPS_PER_SCREEN_WIDTH / 2
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
        
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
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
                print("⚠️ Stream disconnected. Retrying in 1s...")
                time.sleep(1)

    def start(self):
        self.capture_thread.start()

    def read(self):
        with self.frame_lock:
            return self.last_ret, self.latest_frame if self.latest_frame is not None else None

    def release(self):
        self.running = False
        if self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        if self.video_capture.isOpened():
            self.video_capture.release()
        print("📷 Camera released.")

def find_arduino_port():
    """Tries to find a serial port that looks like an Arduino."""
    print("🔎 Searching for Arduino port...")
    keywords = ("arduino", "usbmodem", "ch340")
    for port in list_ports.comports():
        for keyword in keywords:
            if keyword in port.description.lower() or keyword in port.device.lower():
                print(f"✅ Found potential Arduino on {port.device}")
                return port.device
    return None

def go(ser, coord):
    """Formats and sends a move command to the Arduino."""
    command_str = json.dumps(coord) + '\n'
    print(f"📤 Sending: {command_str.strip()}...")
    try:
        ser.write(command_str.encode('utf-8'))
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
    except serial.SerialException as e:
        print(f"❌ Arduino communication error: {e}")


# MODIFIED FUNCTION
def get_target_info(results, frame_shape):
    """
    Finds the best target and returns a dictionary with its details.
    The best target is the one closest to the center of the frame that meets
    the class and confidence criteria.
    """
    target_set = {cls.lower() for cls in TARGET_CLASSES}
    best_target = None
    min_d2 = float("inf") # Minimum squared distance to center

    if not results or not results[0]:
        return None

    h, w = frame_shape[:2]
    cx_frame, cy_frame = w / 2.0, h / 2.0
    r = results[0]

    for i in range(len(r.boxes.xyxy)):
        label = model.names[int(r.boxes.cls[i])]
        conf = float(r.boxes.conf[i])

        if label.lower() not in target_set or conf < MIN_CONFIDENCE:
            continue

        box = r.boxes.xyxy[i].cpu().numpy()
        x1, y1, x2, y2 = map(float, box)
        cx_box = (x1 + x2) / 2.0
        cy_box = (y1 + y2) / 2.0

        # Compute squared distance from box center to frame center
        d2 = (cx_box - cx_frame)**2 + (cy_box - cy_frame)**2

        if d2 < min_d2:
            min_d2 = d2
            dx_norm = (cx_box - cx_frame) / (w / 2.0)
            dy_norm = (cy_box - cy_frame) / (h / 2.0)
            
            best_target = {
                "box": (int(x1), int(y1), int(x2), int(y2)),
                "label": label,
                "confidence": conf,
                "center": (int(cx_box), int(cy_box)),
                "dx_norm": dx_norm,
                "dy_norm": dy_norm
            }

    if best_target:
         print(f"🎯 Target Acquired: {best_target['label']} (Conf: {best_target['confidence']:.2f})")
    
    return best_target

# NEW FUNCTION
def draw_overlays(frame, target_info, global_coord, motor_steps):
    """Draws all visual aids onto the frame."""
    h, w, _ = frame.shape
    cx_frame, cy_frame = w // 2, h // 2

    # 1. Draw central crosshair
    cv2.line(frame, (cx_frame - 20, cy_frame), (cx_frame + 20, cy_frame), (0, 255, 255), 1)
    cv2.line(frame, (cx_frame, cy_frame - 20), (cx_frame, cy_frame + 20), (0, 255, 255), 1)

    # 2. Draw info for the detected target
    if target_info:
        x1, y1, x2, y2 = target_info["box"]
        cx_box, cy_box = target_info["center"]
        label = f"{target_info['label'].title()} ({target_info['confidence']:.2f})"

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw label
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw vector from frame center to target center
        cv2.arrowedLine(frame, (cx_frame, cy_frame), (cx_box, cy_box), (0, 0, 255), 2)

    # 3. Draw stats panel
    panel_y = h - 70
    cv2.rectangle(frame, (0, panel_y), (w, h), (0, 0, 0), -1) # Black background
    
    stats_text1 = f"Global Coords: (X={global_coord['x']:.0f}, Y={global_coord['y']:.0f})"
    stats_text2 = f"Move Vector (steps): (dx={motor_steps[0]}, dy={motor_steps[1]})"
    
    cv2.putText(frame, stats_text1, (10, panel_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, stats_text2, (10, panel_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return frame

# MODIFIED MAIN FUNCTION
def main():
    print("🔄 Starting system...")
    
    camera = ThreadedCamera(STREAM_URL)
    camera.start()
    
    ser = None # Initialize ser to None
    try:
        arduino_port = find_arduino_port()
        if not arduino_port:
            print("⚠️ WARNING: Could not automatically find Arduino. Running in view-only mode.")
        else:
            try:
                ser = serial.Serial(arduino_port, BAUD_RATE, timeout=10)
                time.sleep(2) # Wait for serial connection to establish
                print(f"Arduino says: {ser.readline().decode().strip()}")
            except serial.SerialException as e:
                print(f"❌ Error: Could not open serial port {arduino_port}. Running in view-only mode. Details: {e}")
                ser = None
    except Exception as e:
        print(f"An error occurred during Arduino setup: {e}")

    global_coord = {"x": 0.0, "y": 0.0}
    cv2.namedWindow("Live Feed", cv2.WINDOW_NORMAL) # Create window

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            results = model(frame, verbose=False)
            target_info = get_target_info(results, frame.shape)
            
            motor_dx, motor_dy = 0, 0

            if target_info:
                # Calculate motor steps from normalized coordinates
                # Note: dy is inverted because screen 'y' is down, but motor 'y' might be up
                motor_dx = target_info["dx_norm"] * (STEPS_PER_SCREEN_WIDTH / 2.0)
                motor_dy = -target_info["dy_norm"] * (STEPS_PER_SCREEN_WIDTH / 2.0)

                # Calculate new global coordinates and apply limits
                x_new = global_coord["x"] + motor_dx
                y_new = global_coord["y"] + motor_dy
                
                x_clamped = max(-LIMIT, min(LIMIT, x_new))
                y_clamped = max(-LIMIT, min(LIMIT, y_new))

                # If there's an Arduino, send the command
                if ser:
                    coord = {"x": int(x_clamped), "y": int(y_clamped)}
                    go(ser, coord)
                
                # Update global coordinates after the move
                global_coord["x"] = x_clamped
                global_coord["y"] = y_clamped
            
            # Draw overlays for the preview
            annotated_frame = draw_overlays(frame, target_info, global_coord, (int(motor_dx), int(motor_dy)))
            
            cv2.imshow('Live Feed', annotated_frame)

            # Exit loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("🛑 Exiting...")
                break
                
    finally:
        # Cleanup
        camera.release()
        if ser and ser.is_open:
            ser.close()
            print("🔌 Serial port closed.")
        cv2.destroyAllWindows()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()