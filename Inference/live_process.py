from ultralytics import YOLO
import cv2
import time
import os

# ======== CONFIGURATION ========
TARGET_FPS = 10  # Set your desired frame rate here
MODEL_PATH = "yolov8n.pt"  # Path to YOLO model
IMAGE_PATH = "livefeed/image.jpg"  # Path to input image
TARGET_CLASSES = ["pigeon", "bird", "person","human"]  # Classes to detect
# ===============================

# Calculate target interval from FPS
TARGET_INTERVAL = 1.0 / TARGET_FPS

# Initialize YOLO model
model = YOLO(MODEL_PATH)
window_name = "Bird Detection Monitor"

# Create output directory if needed
os.makedirs(os.path.dirname(IMAGE_PATH), exist_ok=True)

# Create the display window
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# Timing and performance tracking
last_fps_update = time.time()
frame_count = 0
fps = 0
avg_processing_time = 0

print(f"Starting detection at {TARGET_FPS} FPS...")
print("Press 'q' to exit")

try:
    while True:
        loop_start = time.time()
        
        # Read the latest image
        img = cv2.imread(IMAGE_PATH)
        
        if img is None:
            # Show waiting screen if image not available
            blank = create_waiting_screen(800, 600)
            cv2.imshow(window_name, blank)
            cv2.waitKey(1)
            time.sleep(TARGET_INTERVAL)
            continue
        
        # Run inference
        detect_start = time.time()
        results = model(img, verbose=False)
        detect_end = time.time()
        
        # Process detections
        r = results[0]
        detection_count = 0
        for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            class_name = model.names[int(cls)]
            if class_name in TARGET_CLASSES:
                detection_count += 1
                x1, y1, x2, y2 = [int(v) for v in box]
                
                # Draw bounding box
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"{class_name} {conf:.2f}"
                cv2.putText(img, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Draw crosshair
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cv2.line(img, (center_x-10, center_y), (center_x+10, center_y), 
                        (0, 0, 255), 2)
                cv2.line(img, (center_x, center_y-10), (center_x, center_y+10), 
                        (0, 0, 255), 2)

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
        cv2.putText(img, f"Proc: {avg_processing_time*1000:.1f}ms", (10, 110), 
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
    cv2.destroyAllWindows()
    print("Detection monitor stopped.")

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