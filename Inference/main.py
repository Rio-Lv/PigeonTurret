from ultralytics import YOLO
import cv2
import time 

# 👉 “yolov9t.pt” is the tiny model – fastest to test.
#     Swap in your own .pt / .onnx / .engine weight file once you have it.
model = YOLO("yolov9t.pt")


# --- 3a. Single image -------------------------------------------------
start = time.time()
source_path = "images/input.png"       # any image file
results = model(source_path, imgsz=512)           # returns a list (len == #images); here 1
r = results[0]

# r.boxes.xyxy  -> (N,4) tensor of [x1, y1, x2, y2] in *pixel* coords
# r.boxes.cls   -> (N,)  tensor of class indices
# r.boxes.conf  -> (N,)  tensor of confidences 0–1
for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
    class_name = model.names[int(cls)]
    if class_name in ("pigeon", "bird"):         # keep only the classes you care about
        x1, y1, x2, y2 = [int(v) for v in box]   # cast tensor → int
        print(f"{class_name:6s}  {conf:.2f}  @  [{x1},{y1}]-[{x2},{y2}]")

end = time.time()
print(f"Processing time: {end - start:.2f} seconds")
# --- 3b. Folder / webcam / RTSP ---------------------------------------
# results = model("images/", stream=False)       # folder
# results = model(0, stream=True)                # webcam

img = cv2.imread(source_path)
for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
    if model.names[int(cls)] in ("pigeon", "bird"):
        x1,y1,x2,y2 = [int(v) for v in box]
        cv2.rectangle(img, (x1, y1), (x2, y2), thickness=2, color=(0,255,0))
cv2.imwrite("images/output.png", img)

