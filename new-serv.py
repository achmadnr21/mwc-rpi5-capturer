import os
import time
import datetime
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Initialize Picamera2
camera = Picamera2()
video_config = camera.create_video_configuration(main={"size": (640, 480)})
camera.configure(video_config)
camera.start_preview(Preview.NULL)
camera.start()


# Background subtractor for motion detection
back_sub = cv2.createBackgroundSubtractorMOG2(history=25, varThreshold=20, detectShadows=True)

# Kernel for morphological operations (removing noise)
kernel = np.ones((20, 20), np.uint8)

# Output folder for videos
output_folder = "/mnt/mydisk/"
os.makedirs(output_folder, exist_ok=True)

# Video encoder
encoder = H264Encoder(bitrate=1000000)

# Motion detection parameters
recording = False
last_motion_time = 0
MOTION_TIMEOUT = 5  # Stop recording after 5 seconds of no motion

print("[INFO] Camera initialized. Monitoring for motion...")

while True:
    frame = camera.capture_array("main")  # Capture frame as a NumPy array
    fg_mask = back_sub.apply(frame)  # Apply motion detection

    # Morphological operation to remove noise
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.medianBlur(fg_mask, 5)
    _, fg_mask = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)

    # Find contours of moving objects
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    areas = [cv2.contourArea(c) for c in contours]

    if areas:
        max_index = np.argmax(areas)  # Find the largest moving object
        cnt = contours[max_index]
        x, y, w, h = cv2.boundingRect(cnt)

        # Draw a bounding box around detected motion
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # If motion is significant, start recording
        if h > 200 and not recording:
            recording = True
            last_motion_time = time.time()
            filename = f"{output_folder}/motion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
            camera.start_recording(encoder, FileOutput(filename))
            print(f"[INFO] Recording started: {filename}")

    else:
        # Stop recording if no motion is detected for MOTION_TIMEOUT seconds
        if recording and (time.time() - last_motion_time > MOTION_TIMEOUT):
            camera.stop_recording()
            recording = False
            print("[INFO] Recording stopped due to inactivity.")


    # Exit on 'q' key press
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Cleanup
camera.stop()
cv2.destroyAllWindows()
print("[INFO] Program exited.")