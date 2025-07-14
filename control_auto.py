# realtime_control.py - Low-latency autonomous object centering
import argparse
import sys
import time
import socket
import cv2
import numpy as np
from pynput import keyboard
from ultralytics import YOLO
import os

# ======== CONFIGURATION ========
# --- Stream and Control ---
STREAM_URL = "tcp://192.168.1.120:3333" # Video stream from Pi
PI_IP = "192.168.1.120"                # Command IP for Pi
PORT = 4444                            # Command port for Pi
COMMAND_INTERVAL = 0.2                 # Seconds between commands (reduced for lower latency)

# --- AI and Vision ---
MODEL_PATH = "yolov8n.pt"              # Path to YOLO model
TARGET_CLASSES = ["pigeon", "bird", "person", "human"] # Classes to detect
DEADZONE_PERCENT = 0.1                 # 10% deadzone around center
SPEED_FACTOR = 0.2                     # Global speed multiplier (0.1-1.0)
# ===============================

# Initialize YOLO model
try:
    model = YOLO(MODEL_PATH)
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
        print(f"✅  Command socket connected to {PI_IP}:{PORT}")
        return True
    except ConnectionRefusedError:
        print("❌  Command connection refused. Is the receiver script running on the Pi?")
        return False
    except OSError as e:
        print(f"❌  Command connection error: {e}")
        return False

def send_command(dx, dy):
    """Send movement command to Raspberry Pi"""
    command_str = f"{dx:.3f},{dy:.3f},{SPEED_FACTOR:.2f}\n"
    try:
        sock.sendall(command_str.encode())
        print(f"📤 Sent: {command_str.strip()}") # Uncomment for verbose command logging
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("❌  Connection lost! Attempting to reconnect...")
        if connect_to_pi_command():
            sock.sendall(command_str.encode())
            print(f"📤 Re-sent: {command_str.strip()}")

def calculate_movement(image_shape, target_center):
    """Calculate dx, dy to center the target"""
    h, w = image_shape[:2]
    center_x, center_y = w // 2, h // 2

    # Calculate normalized offsets (-1 to 1 range)
    dx = (target_center[0] - center_x) / (w / 2)
    dy = (target_center[1] - center_y) / (h / 2)

    # Apply deadzone
    dx = 0 if abs(dx) < DEADZONE_PERCENT else dx
    dy = 0 if abs(dy) < DEADZONE_PERCENT else dy

    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, dx)), max(-1.0, min(1.0, dy))

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
    def __init__(self):
        self.stop_requested = False
        self.last_command_time = 0
        self.listener = keyboard.Listener(on_press=self.on_press)

    def on_press(self, key):
        """Handle emergency stop on ESC key"""
        if key == keyboard.Key.esc:
            print("🛑 Emergency stop requested!")
            self.stop_requested = True
            return False  # Stop listener

    def run(self):
        """Main control loop"""
        print(f"🚀 Starting real-time autonomous centering...")
        print(f"Press 'q' in the window to exit or ESC for emergency stop.")
        
        self.listener.start()

        # Connect to video stream
        cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"❌ Cannot open stream. Check URL: {STREAM_URL}")
            return

        try:
            while not self.stop_requested:
                # 1. Read Frame Directly from Stream
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Frame read error. Attempting to reconnect stream...")
                    cap.release()
                    time.sleep(2)
                    cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
                    continue

                # 2. Run Inference on the Live Frame
                results = model(frame, verbose=False)
                closest_target = find_closest_target(results, frame.shape)
                dx, dy = 0, 0

                # 3. Process and Draw Results
                if closest_target:
                    # Calculate movement based on the closest target
                    dx, dy = calculate_movement(frame.shape, closest_target["center"])

                    # Draw box for the closest target
                    x1, y1, x2, y2 = closest_target["box"]
                    color = (0, 255, 0) # Green for the locked target
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    label = f"{closest_target['class_name']} {closest_target['confidence']:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                    # Draw movement vector
                    h, w = frame.shape[:2]
                    center_x, center_y = w // 2, h // 2
                    end_x = int(center_x + dx * w / 4)
                    end_y = int(center_y + dy * h / 4)
                    cv2.arrowedLine(frame, (center_x, center_y), (end_x, end_y), (0, 255, 255), 3)

                # 4. Send Command at a Regular Interval
                current_time = time.time()
                if current_time - self.last_command_time >= COMMAND_INTERVAL:
                    send_command(dx, dy)
                    self.last_command_time = current_time

                # 5. Display Information and Frame
                info_text = f"Targeting: {'Yes' if closest_target else 'No'} | Move: dx={dx:.2f}, dy={dy:.2f}"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow(window_name, frame)

                # Check for exit keys
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            self.cleanup(cap)
            
    def cleanup(self, cap):
        """Gracefully shut down all connections and resources"""
        print("\nCleaning up...")
        send_command(0, 0) # Send a final stop command
        sock.close()
        cap.release()
        cv2.destroyAllWindows()
        self.listener.stop()
        print("🔌 Connections closed. Clean exit.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real-time autonomous object centering.')
    parser.add_argument('--ip', default=PI_IP, help='Raspberry Pi IP for commands.')
    parser.add_argument('--stream', default=STREAM_URL, help='URL of the video stream.')
    parser.add_argument('--model', default=MODEL_PATH, help='Path to the YOLO model.')
    parser.add_argument('--speed', type=float, default=SPEED_FACTOR, help='Speed factor (0.1-1.0).')
    args = parser.parse_args()

    PI_IP = args.ip
    STREAM_URL = args.stream
    MODEL_PATH = args.model
    SPEED_FACTOR = args.speed

    if not connect_to_pi_command():
        sys.exit(1)

    controller = RealTimeControl()
    controller.run()