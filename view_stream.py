import cv2
import argparse


def draw_grid(frame, rows=4, cols=4, color=(0, 255, 0), thickness=1):
    """Draw a grid overlay on the given frame."""
    height, width = frame.shape[:2]
    dy = height // rows
    dx = width // cols

    for i in range(1, rows):
        y = i * dy
        cv2.line(frame, (0, y), (width, y), color, thickness)
    for i in range(1, cols):
        x = i * dx
        cv2.line(frame, (x, 0), (x, height), color, thickness)

    return frame


def main(host, port):
    url = f"tcp://{host}:{port}"
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print(f"Error: Unable to open video stream at {url}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from stream")
            break

        grid_frame = draw_grid(frame)
        cv2.imshow("View Stream", grid_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View network video stream with grid overlay")
    parser.add_argument("host", nargs="?", default="localhost", help="IP address or hostname of the video source")
    parser.add_argument("port", nargs="?", type=int, default=3333, help="TCP port of the video stream")
    args = parser.parse_args()
    main(args.host, args.port)
