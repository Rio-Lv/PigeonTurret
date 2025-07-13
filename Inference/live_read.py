import cv2
import time
import os

# Create output directory if it doesn't exist
output_dir = 'livefeed'
os.makedirs(output_dir, exist_ok=True)

# TCP stream URL
stream_url = 'tcp://192.168.1.120:3333'

# VideoCapture with reduced buffer size for low latency
cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer

if not cap.isOpened():
    raise IOError("Cannot open stream. Check URL/connection.")

last_save_time = time.time()
save_interval = 0.1  # Update image every 1 second

try:
    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Frame read error. Reconnecting...")
            cap.release()
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        # Save latest frame at specified interval
        current_time = time.time()
        if current_time - last_save_time >= save_interval:
            temp_path = os.path.join(output_dir, 'temp.jpg')
            final_path = os.path.join(output_dir, 'image.jpg')
            
            # Save to temp file first to avoid partial reads
            cv2.imwrite(temp_path, frame)
            os.replace(temp_path, final_path)  # Atomic replacement
            
            print(f"Updated {final_path} at {time.strftime('%X')}")
            last_save_time = current_time

finally:
    cap.release()
    print("Stream closed.")