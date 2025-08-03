import cv2
import argparse
import sys
import threading
import time

class VideoStream:
    """
    A threaded class to read frames from a camera stream for low latency.
    """
    def __init__(self, src=0):
        print(f"Attempting to connect to stream: {src}")
        self.stream = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if not self.stream.isOpened():
            raise IOError(f"Cannot open stream: {src}")

        # Hint to the backend to keep the buffer size small
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True

    def start(self):
        """Starts the background frame-reading thread."""
        self.thread.start()
        return self

    def _update(self):
        """The core loop that continuously grabs frames."""
        while not self.stopped:
            if not self.stream.isOpened():
                self.stopped = True
                continue
            self.grabbed, self.frame = self.stream.read()

    def read(self):
        """Returns the most recent frame."""
        return self.frame

    def stop(self):
        """Stops the thread and releases resources."""
        self.stopped = True
        self.thread.join()
        self.stream.release()

def draw_grid(frame, rows=4, cols=4, color=(0, 255, 0), thickness=1):
    """Draws a grid overlay on the given frame."""
    if frame is None:
        return None
        
    height, width, _ = frame.shape
    if height == 0 or width == 0:
        return frame
        
    row_height = height // rows
    col_width = width // cols

    for i in range(1, rows):
        cv2.line(frame, (0, i * row_height), (width, i * row_height), color, thickness)
    for i in range(1, cols):
        cv2.line(frame, (i * col_width, 0), (i * col_width, height), color, thickness)
    
    return frame

def view_stream_low_latency(stream_url):
    """
    Connects to a video stream using the threaded reader and displays it.
    """
    try:
        vs = VideoStream(src=stream_url).start()
        print("✅ Successfully connected to stream. Press 'q' to quit.")
    except IOError as e:
        print(f"❌ {e}")
        print("Please ensure the stream is active and the URL is correct.")
        return

    while not vs.stopped:
        frame = vs.read()

        if frame is None:
            time.sleep(0.1) # Wait briefly if the first frame isn't ready
            continue

        grid_frame = draw_grid(frame)
        cv2.imshow("Low Latency Grid View", grid_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.stop()
    cv2.destroyAllWindows()
    print("Stream closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View a network video stream with a grid overlay and low latency.")
    parser.add_argument(
        'url', 
        nargs='?', 
        default="tcp://192.168.1.120:3333", 
        help="The URL of the video stream (e.g., tcp://HOST:PORT)"
    )
    args = parser.parse_args()
    
    view_stream_low_latency(args.url)