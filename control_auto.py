# realtime_control.py - Low-latency autonomous object centering with a threaded frame reader
import argparse
import sys
import time
import socket
import cv2
import numpy as np
import threading
from pynput import keyboard
from ultralytics import YOLO

# ======== CONFIGURATION ========
# --- Stream and Control ---
STREAM_URL = "tcp://192.168.1.120:3333"  # Video stream from Pi
PI_IP = "192.168.1.120"                   # Command IP for Pi
PORT = 4444                               # Command port for Pi
COMMAND_INTERVAL = 0.1                 # Seconds between commands
FRAME_SKIP = 5                           # Process every 5th frame (can be lower with threaded reader)

# --- AI and Vision ---
MODEL_PATH = "yolov8n.pt"                 # Path to YOLO model
TARGET_CLASSES = ["pigeon", "bird", "cup", "mug", "glass", "person"]  # Classes to detect
DEADZONE_PERCENT = 0.1                    # 10% deadzone around center
SPEED_FACTOR = 1.0                        # Global speed multiplier (0.1-1.0)
# ===============================

# Initialize YOLO model
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ Loaded YOLO model: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    sys.exit(1)

window_name = "Real-time Autonomous Control"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# Initialize command socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_pi_command():
    """Establish command connection to Raspberry Pi"""
    try:
        sock.connect((PI_IP, PORT))
        print(f"✅ Command socket connected to {PI_IP}:{PORT}")
        return True
    except ConnectionRefusedError:
        print("❌ Command connection refused. Is the receiver script running on the Pi?")
        return False
    except OSError as e:
        print(f"❌ Command connection error: {e}")
        return False

def send_command(dx, dy):
    """Send movement command to Raspberry Pi"""
    command_str = f"{dx:.3f},{dy:.3f},{SPEED_FACTOR:.2f}\n"
    try:
        sock.sendall(command_str.encode())
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("❌ Connection lost! Attempting to reconnect...")
        if connect_to_pi_command():
            sock.sendall(command_str.encode())
            print(f"📤 Re-sent: {command_str.strip()}")

def calculate_movement(image_shape, target_center):
    """Calculate dx, dy to center the target"""
    h, w = image_shape[:2]
    center_x, center_y = w // 2, h // 2
    dx = (target_center[0] - center_x) / (w / 2)
    dy = (target_center[1] - center_y) / (h / 2)
    dx = 0 if abs(dx) < DEADZONE_PERCENT else dx
    dy = 0 if abs(dy) < DEADZONE_PERCENT else dy
    return -dx * SPEED_FACTOR, dy * SPEED_FACTOR

def find_closest_target(results, image_shape):
    """Find the target closest to the image center"""
    h, w = image_shape[:2]
    center_x, center_y = w // 2, h // 2
    closest_target_info = None
    min_distance = float('inf')

    r = results[0]
    for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
        class_name = model.names[int(cls)]
        if class_name in TARGET_CLASSES:
            x1, y1, x2, y2 = [int(v) for v in box]
            target_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            distance = np.sqrt((target_center[0] - center_x)**2 + (target_center[1] - center_y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_target_info = {
                    "center": target_center,
                    "box": (x1, y1, x2, y2),
                    "class_name": class_name,
                    "confidence": conf
                }
    return closest_target_info

class RealTimeControl:
    def __init__(self, frame_skip=2):
        self.frame_skip = max(1, frame_skip)
        self.frame_counter = 0
        self.last_target = None
        self.last_dx = 0
        self.last_dy = 0
        self.last_command_time = 0

        # --- Threading for Video Capture ---
        self.video_capture = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
        if not self.video_capture.isOpened():
            raise IOError(f"Cannot open stream: {STREAM_URL}")
        
        # Try to set a small buffer size (may not be supported by backend)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.latest_frame = None
        self.last_ret = False
        self.frame_lock = threading.Lock()
        self.running = True
        self.capture_thread = threading.Thread(target=self._reader_loop, daemon=True)

        # --- Keyboard Listener ---
        self.listener = keyboard.Listener(on_press=self.on_press)

    def _reader_loop(self):
        """Continuously reads frames from the stream in a dedicated thread."""
        print("🚀 Capture thread started.")
        while self.running:
            ret, frame = self.video_capture.read()
            with self.frame_lock:
                self.last_ret = ret
                self.latest_frame = frame
            if not ret:
                print("⚠️ Stream connection lost in reader thread. Will keep trying to read.")
                time.sleep(1) # Wait a bit before retrying

    def on_press(self, key):
        """Handle emergency stop on ESC key"""
        if key == keyboard.Key.esc:
            print("🛑 Emergency stop requested!")
            self.running = False
            return False  # Stop listener

    def run(self):
        """Main control loop."""
        self.listener.start()
        self.capture_thread.start()

        print("Waiting for first frame from stream...")
        time.sleep(2) 
        print("✅ First frame received. Starting main loop.")
        
        try:
            while self.running:
                # 1. Get the latest frame from the reader thread
                with self.frame_lock:
                    ret, frame = self.last_ret, self.latest_frame

                if not ret or frame is None:
                    time.sleep(0.1)
                    continue

                self.frame_counter += 1
                skip_frame = self.frame_counter % self.frame_skip != 0

                # 2. Process Frame Conditionally
                current_target = None
                if not skip_frame:
                    results = model(frame, verbose=False)
                    current_target = find_closest_target(results, frame.shape)
                    self.last_target = current_target

                    if current_target:
                        self.last_dx, self.last_dy = calculate_movement(frame.shape, current_target["center"])
                    else:
                        self.last_dx, self.last_dy = 0, 0
                else:
                    current_target = self.last_target # Use cached target

                # 3. Visual Feedback
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2

                # --- NEW: Always draw a static crosshair ---
                crosshair_color = (0, 255, 255) # Cyan
                cv2.line(frame, (center_x - 15, center_y), (center_x + 15, center_y), crosshair_color, 2)
                cv2.line(frame, (center_x, center_y - 15), (center_x, center_y + 15), crosshair_color, 2)
                # ---

                if current_target:
                    color = (0, 255, 0) if not skip_frame else (255, 150, 0)
                    label_suffix = "" if not skip_frame else " (cached)"
                    x1, y1, x2, y2 = current_target["box"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{current_target['class_name']}{label_suffix}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    # --- RESTORED: Draw movement vector when target is found ---
                    end_x = int(center_x + self.last_dx * w / 4)
                    end_y = int(center_y + self.last_dy * h / 4)
                    cv2.arrowedLine(frame, (center_x, center_y), (end_x, end_y), (0, 255, 255), 2)
                    # ---

                # 4. Send Commands
                current_time = time.time()
                if current_time - self.last_command_time >= COMMAND_INTERVAL:
                    send_command(self.last_dx, self.last_dy)
                    self.last_command_time = current_time

                # 5. Display Information
                status = "Processing" if not skip_frame else "Skipped"
                info_text = f"Frame: {self.frame_counter} ({status}) | Target: {'Yes' if current_target else 'No'} | Move: {self.last_dx:.2f}, {self.last_dy:.2f}"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow(window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
        finally:
            self.cleanup()

    def cleanup(self):
        """Gracefully shut down all connections and resources."""
        print("\nCleaning up...")
        self.running = False # Signal reader thread to stop
        
        # Wait for threads to finish
        if self.listener.is_alive():
            self.listener.stop()
        if self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2) # Wait up to 2s

        send_command(0, 0) # Send a final stop command
        time.sleep(0.1)
        sock.close()
        
        if self.video_capture.isOpened():
            self.video_capture.release()
        cv2.destroyAllWindows()
        print("🔌 Connections closed. Clean exit.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real-time autonomous object centering with a threaded frame reader.')
    parser.add_argument('--ip', default=PI_IP, help='Raspberry Pi IP for commands.')
    parser.add_argument('--stream', default=STREAM_URL, help='URL of the video stream.')
    parser.add_argument('--model', default=MODEL_PATH, help='Path to the YOLO model.')
    parser.add_argument('--speed', type=float, default=SPEED_FACTOR, help='Speed factor (0.1-1.0).')
    parser.add_argument('--skip', type=int, default=FRAME_SKIP, help='Process every N-th frame (e.g., 2)')
    args = parser.parse_args()

    PI_IP = args.ip
    STREAM_URL = args.stream
    MODEL_PATH = args.model
    SPEED_FACTOR = args.speed
    FRAME_SKIP = max(1, args.skip)

    if not connect_to_pi_command():
        sys.exit(1)

    try:
        controller = RealTimeControl(frame_skip=FRAME_SKIP)
        controller.run()
    except (IOError, KeyboardInterrupt) as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)