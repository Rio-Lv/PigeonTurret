import sys
import time
import json
import math
import threading
import argparse
import serial
import cv2
import os
from ultralytics import YOLO
import serial 

# ======== CONFIGURATION ========
# --- Stream and Model ---
STREAM_URL = "tcp://192.168.1.120:3333" # Video stream URL
MODEL_PATH = "yolov8n.pt"                # Path to your YOLO model
TARGET_CLASSES = ["cup"]  # Classes to detect
MIN_CONFIDENCE = 0.7  # Minimum confidence for detection

# --- Arduino Communication ---
BAUD_RATE = 115200
BUFFER_SIZE = 4 # This MUST match the BUFFER_SIZE in the Arduino sketch

# --- Motion Control ---
# Maps the camera view to the stepper motor's coordinate space.
STEPS_PER_SCREEN_WIDTH = 1500
LIMIT = STEPS_PER_SCREEN_WIDTH/2
MIN_MOVE_DISTANCE = 0.05



class Turret:
    def __init__(self):
        self.stream = self._init_stream()
        self.model = YOLO(MODEL_PATH)
    
    @staticmethod 
    def _init_stream():
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;udp|"
            "fflags;nobuffer|flags;low_delay|"
            "probesize;32|analyzeduration;0|max_delay;0"
        )
        stream = cv2.VideoCapture(STREAM_URL,cv2.CAP_FFMPEG)
        stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        return stream

if __name__ == "__main__":
    turret = Turret()
    print("Turret initialized with video stream and YOLO model.")
