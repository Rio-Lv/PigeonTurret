import cv2
import argparse
import sys
import threading
import time

class VideoStream:
    """A threaded class to read frames from a UDP stream for low latency."""
    def __init__(self, src=0):
        print(f"Attempting to open stream: {src}")
        self.stream = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if not self.stream.isOpened():
            raise IOError(f"Cannot open stream: {src}")

        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True

    def start(self):
        """Starts the background frame-reading thread."""
        self.thread.start()
        print("✅ Stream reader thread started.")
        return self

    def _update(self):
        """The core loop that continuously grabs frames from the stream."""
        while not self.stopped:
            if not self.stream.isOpened():
                self.stopped = True
                continue
            self.grabbed, self.frame = self.stream.read()

    def read(self):
        """Returns the most recent frame captured by the thread."""
        return self.frame

    def stop(self):
        """Stops the thread and releases camera resources."""
        self.stopped = True
        self.thread.join()
        self.stream.release()
        print("Stream stopped.")

def main(stream_url):
    """Initializes the stream and enters the main display loop."""
    try:
        vs = VideoStream(src=stream_url).start()
    except IOError as e:
        print(f"❌ Error: {e}")
        print("Please ensure the stream source is active and the URL is correct.")
        return

    while not vs.stopped:
        frame = vs.read()

        if frame is None:
            time.sleep(0.1) # Wait if the first frame isn't ready
            continue

        cv2.imshow("UDP Stream Viewer", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View a UDP video stream with low latency.")
    parser.add_argument(
        'url',
        nargs='?',
        default="udp://0.0.0.0:3333",
        help="The URL of the UDP stream (e.g., udp://0.0.0.0:3333)"
    )
    args = parser.parse_args()
    main(args.url)