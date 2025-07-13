# control_auto.py - Autonomous object centering with YOLO and TCP control
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
TARGET_FPS = 10  # Set your desired frame rate here
MODEL_PATH = "yolov8n.pt"  # Path to YOLO model
IMAGE_PATH = "livefeed/image.jpg"  # Path to input image
TARGET_CLASSES = ["pigeon", "bird", "person", "human"]  # Classes to detect
PI_IP = "192.168.1.120"  # Raspberry Pi's IP
PORT = 4444
DEADZONE_PERCENT = 0.1  # 10% deadzone around center
# ===============================

# Calculate target interval from FPS
TARGET_INTERVAL = 1.0 / TARGET_FPS

# Initialize YOLO model
model = YOLO(MODEL_PATH)
window_name = "Autonomous Centering Control"

# Create output directory if needed
os.makedirs(os.path.dirname(IMAGE_PATH), exist_ok=True)

# Create the display window
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_pi():
    """Establish connection to Raspberry Pi"""
    try:
        sock.connect((PI_IP, PORT))
        print("✅  Connected to {0}:{1}".format(PI_IP, PORT))
        return True
    except ConnectionRefusedError:
        print("❌  Connection refused. Is receiver.py running?")
        return False
    except OSError as e:
        print("❌  Connection error: {0}".format(e))
        return False

def send_command(dx, dy):
    """Send movement command to Raspberry Pi"""
    command_str = "{{dx:{}, dy:{}}}".format(dx, dy)
    try:
        sock.sendall(command_str.encode())
        print("📤 Sent: {}".format(command_str))
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("❌  Connection lost! Attempting to reconnect...")
        if connect_to_pi():
            sock.sendall(command_str.encode())
            print("📤 Re-sent: {}".format(command_str))

def create_waiting_screen(width, height):
    """Create a placeholder image when no input is available"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    text = "Waiting for input image..."
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return img

def calculate_movement(image, target_center):
    """Calculate dx, dy to center the target"""
    h, w = image.shape[:2]
    center_x, center_y = w // 2, h // 2
    
    # Calculate normalized offsets (-1 to 1 range)
    dx = (target_center[0] - center_x) / (w / 2)
    dy = (target_center[1] - center_y) / (h / 2)
    
    # Apply deadzone
    dx = 0 if abs(dx) < DEADZONE_PERCENT else dx
    dy = 0 if abs(dy) < DEADZONE_PERCENT else dy
    
    # Clamp to [-1, 1] and quantize
    dx = max(-1, min(1, dx))
    dy = max(-1, min(1, dy))
    
    # Quantize to -1, 0, 1 for simpler control
    dx = 1 if dx > 0.5 else (-1 if dx < -0.5 else 0)
    dy = 1 if dy > 0.5 else (-1 if dy < -0.5 else 0)
    
    return dx, dy

def find_closest_target(results, image):
    """Find the closest target to the image center"""
    h, w = image.shape[:2]
    center_x, center_y = w // 2, h // 2
    closest_target = None
    min_distance = float('inf')
    
    r = results[0]
    for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
        class_name = model.names[int(cls)]
        if class_name in TARGET_CLASSES:
            x1, y1, x2, y2 = [int(v) for v in box]
            target_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            # Calculate distance to center
            distance = np.sqrt((target_center[0] - center_x)**2 + 
                             (target_center[1] - center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_target = target_center
    
    return closest_target

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Autonomous object centering')
    parser.add_argument('--ip', default=PI_IP, help='Raspberry Pi IP')
    parser.add_argument('--model', default=MODEL_PATH, help='YOLO model path')
    parser.add_argument('--image', default=IMAGE_PATH, help='Image path')
    args = parser.parse_args()
    PI_IP = args.ip
    MODEL_PATH = args.model
    IMAGE_PATH = args.image
    
    if not connect_to_pi():
        sys.exit(1)
    
    print(f"Starting autonomous centering at {TARGET_FPS} FPS...")
    print("Press 'q' to exit")
    
    # Timing and performance tracking
    last_fps_update = time.time()
    frame_count = 0
    fps = 0
    avg_processing_time = 0
    
    # Keyboard listener for emergency stop
    stop_requested = False
    
    def on_press(key):
        nonlocal stop_requested
        if key == keyboard.Key.esc:
            print("🛑 Emergency stop requested!")
            send_command(0, 0)  # Stop movement
            stop_requested = True
            return False  # Stop listener
    
    # Start keyboard listener in non-blocking mode
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    try:
        while not stop_requested:
            loop_start = time.time()
            
            # Read the latest image
            img = cv2.imread(IMAGE_PATH)
            
            if img is None:
                # Show waiting screen if image not available
                blank = create_waiting_screen(800, 600)
                cv2.imshow(window_name, blank)
                cv2.waitKey(1)
                time.sleep(TARGET_INTERVAL)
                send_command(0, 0)  # Stop movement
                continue
            
            # Run inference
            detect_start = time.time()
            results = model(img, verbose=False)
            detect_end = time.time()
            
            # Find closest target
            closest_target = find_closest_target(results, img)
            
            # Initialize movement
            dx, dy = 0, 0
            detection_count = 0
            
            # Process detections
            r = results[0]
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                class_name = model.names[int(cls)]
                if class_name in TARGET_CLASSES:
                    detection_count += 1
                    x1, y1, x2, y2 = [int(v) for v in box]
                    target_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    
                    # Highlight closest target
                    is_closest = (closest_target == target_center)
                    color = (0, 255, 0) if is_closest else (0, 0, 255)
                    thickness = 3 if is_closest else 1
                    
                    # Draw bounding box
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
                    
                    # Draw label
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(img, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Draw crosshair
                    cv2.line(img, (target_center[0]-15, target_center[1]), 
                            (target_center[0]+15, target_center[1]), color, 2)
                    cv2.line(img, (target_center[0], target_center[1]-15), 
                            (target_center[0], target_center[1]+15), color, 2)
            
            # Calculate movement if target found
            if closest_target:
                dx, dy = calculate_movement(img, closest_target)
                
                # Draw movement vector
                h, w = img.shape[:2]
                center_x, center_y = w // 2, h // 2
                end_x = int(center_x + dx * w/4)
                end_y = int(center_y + dy * h/4)
                cv2.arrowedLine(img, (center_x, center_y), (end_x, end_y), 
                               (0, 255, 255), 3, tipLength=0.3)
            
            # Send movement command
            send_command(dx, dy)
            
            # Calculate performance metrics
            frame_count += 1
            current_time = time.time()
            processing_time = current_time - loop_start
            
            # Update FPS counter every second
            if current_time - last_fps_update >= 1.0:
                fps = frame_count / (current_time - last_fps_update)
                frame_count = 0
                last_fps_update = current_time
                avg_processing_time = processing_time  # Track most recent processing time
            
            # Add info overlay
            cv2.putText(img, f"FPS: {fps:.1f}/{TARGET_FPS}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, f"Detections: {detection_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, f"Movement: dx={dx}, dy={dy}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, f"Model: {MODEL_PATH}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            # Display result
            cv2.imshow(window_name, img)
            
            # Calculate remaining time and wait
            processing_time = time.time() - loop_start
            sleep_time = max(0, TARGET_INTERVAL - processing_time)
            
            # Exit on 'q' key or if window is closed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
                
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        send_command(0, 0)  # Stop movement
        sock.close()
        cv2.destroyAllWindows()
        listener.stop()
        print("🔌 Connection closed. Clean exit.")