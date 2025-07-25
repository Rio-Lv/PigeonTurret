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
MOTION_RANGE_STEPS = 1000
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

def send_move(ser, x, y):
    """Formats and sends a move command to the Arduino."""
    command_obj = {"x": int(x), "y": int(y)}
    command_str = json.dumps(command_obj) + '\n'
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
    """Finds the detected object closest to the center of the frame."""
    frame_center_x, frame_center_y = frame_shape[1] // 2, frame_shape[0] // 2
    closest_target = None
    min_distance = float('inf')

    if not results or not results[0]:
        return None

    r = results[0]
    for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
        class_name = model.names[int(cls)]
        if class_name in TARGET_CLASSES:
            x1, y1, x2, y2 = [int(v) for v in box]
            target_center_x, target_center_y = (x1 + x2) // 2, (y1 + y2) // 2
            distance = math.sqrt((target_center_x - frame_center_x)**2 + (target_center_y - frame_center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_target = {"box": (x1, y1, x2, y2), "class_name": class_name}
    return closest_target

def main(serial_port):
    """Main control loop."""
    print(f"🔌 Connecting to Arduino on {serial_port} at {BAUD_RATE} bps...")
    try:
        # Small timeout avoids partial reads while still returning quickly
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        while ser.in_waiting:
            print(f"Arduino says: {ser.readline().decode().strip()}")
    except serial.SerialException as e:
        print(f"❌ Error opening serial port: {e}")
        return

    camera = ThreadedCamera(STREAM_URL)
    camera.start()
    time.sleep(2) # Wait for camera to buffer a frame

    print("🚀 Starting main control loop. Press Ctrl+C to exit.")
    
    try:
        # --- Prime the Buffer ---
        print(f"Priming Arduino buffer with {BUFFER_SIZE} initial commands (move to center)...")
        for _ in range(BUFFER_SIZE):
            send_move(ser, 0, 0)
        
        # --- Main Streaming Loop ---
        while True:
            # 1. Grab a frame and run detection
            ret, frame = camera.read()
            if not ret or frame is None:
                continue

            results = model(frame, verbose=False)
            target = find_closest_target(results, frame.shape)

            motor_x = 0
            motor_y = 0

            if target:
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                box_center_x = (target["box"][0] + target["box"][2]) // 2
                box_center_y = (target["box"][1] + target["box"][3]) // 2

                # Convert pixel offset to motor steps
                # Note: dy is often inverted because pixel Y increases downwards
                dx_norm = (box_center_x - center_x) / (w / 2)
                dy_norm = (box_center_y - center_y) / (h / 2)

                motor_x = dx_norm * MOTION_RANGE_STEPS / 100
                motor_y = dy_norm * MOTION_RANGE_STEPS / 100

                # --- Visual Feedback ---
                x1, y1, x2, y2 = target["box"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, target["class_name"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 2. Show the video feed regardless of Arduino state
            cv2.imshow("YOLO Control", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 3. Check for acknowledgment from Arduino
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                if response != "done":
                    if response:
                        print(f"Arduino message: {response}")
                    continue

                # Send the next move based on the most recent frame
                send_move(ser, motor_x, motor_y)

    except KeyboardInterrupt:
        print("\n🛑 User requested stop.")
    finally:
        print("Cleaning up...")
        # Command motors to center and wait for final acknowledgments
        if 'ser' in locals() and ser.is_open:
            for _ in range(BUFFER_SIZE):
                send_move(ser, 0, 0)
                time.sleep(0.1) # Give it a moment to send
            ser.close()
            print("🔌 Serial port closed.")
        
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simplified YOLO object tracking for Arduino control.')
    parser.add_argument('--port', help='Manually specify the serial port (e.g., COM3 or /dev/ttyACM0).')
    args = parser.parse_args()

    # Find port automatically or use the one specified by the user
    port_to_use = args.port or find_arduino_port()
    
    if not port_to_use:
        print("❌ Could not find Arduino. Please specify the port with --port.")
        sys.exit(1)
        
    main(port_to_use)
