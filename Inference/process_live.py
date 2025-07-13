import cv2, time, os
from ultralytics import YOLO

# ----------------- CONFIG ----------------------------------------------------
PI_IP = "192.168.1.120"  # <— your Pi address
STREAM = f"tcp://{PI_IP}:3333"  # tcp stream from raspivid / netcat
SNAP = "livefeed/image.jpg"  # one persistent file
INTERVAL = 5.0  # seconds between saves
# -----------------------------------------------------------------------------

# make sure the folder exists
os.makedirs(os.path.dirname(SNAP), exist_ok=True)

cap = cv2.VideoCapture("tcp://192.168.1.120:3333", cv2.CAP_ANY)
model = YOLO("yolov8n.pt")  # or yolo11n.pt etc.

next_save = time.time() + INTERVAL  # first snapshot delay

count = 0
while True:
    ok, frame = cap.read()
    count += 1
    if count % 10 == 0:
        print("is ok" , ok)  
    if not ok:
        print("Lost stream — exiting")
        break

    # ------------------- YOLO inference --------------------------------------
    results = model(frame, imgsz=640, half=True, device=0)
    for box, cls, conf in zip(
        results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf
    ):
        if model.names[int(cls)] in {"pigeon", "bird", "person", "human"}:
            x1, y1, x2, y2 = map(int, box)
            print([x1, y1, x2, y2], f"{conf:.2f}")
    # ------------------------------------------------------------------------

    # ------------------- periodic snapshot -----------------------------------
    now = time.time()
    if now >= next_save:
        cv2.imwrite(SNAP, frame)  # overwrites the same file
        next_save = now + INTERVAL
    # ------------------------------------------------------------------------

    # optional: small sleep prevents 100 % CPU if FPS » 30
    # time.sleep(0.005)
