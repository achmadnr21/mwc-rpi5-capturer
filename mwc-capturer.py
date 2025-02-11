import os
import time
from datetime import datetime
import numpy as np
import gpiod
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

# Camera and motion detection settings
motion_threshold = 8  # Adjust sensitivity (higher = less sensitive)
motion_timeout = 5  # Stop recording 5 seconds after motion stops
recording = False
last_motion_time = None  # Track last detected motion time

# Initialize camera
camera = Picamera2()
video_config = camera.create_video_configuration()
camera.configure(video_config)
camera.start_preview(Preview.NULL)  # No preview, useful for background operations

output_folder = "recordings"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

encoder = H264Encoder()

def detect_motion(prev_frame, curr_frame):
    """Detect motion by comparing frame differences."""
    diff = np.abs(curr_frame - prev_frame)
    return np.sum(diff) / diff.size > motion_threshold  # Average change

def start_recording():
    """Start recording a new video file."""
    global recording, last_motion_time
    recording = True
    last_motion_time = time.time()  # Reset last motion time
    filename = f"{output_folder}/motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output = FfmpegOutput(filename)
    camera.start_recording(encoder, output)
    print(f"Recording started: {filename}")

def stop_recording():
    """Stop recording."""
    global recording
    if recording:
        camera.stop_recording()
        recording = False
        print("Recording stopped.")

# IR LED Control
IRLED = 16
chip = gpiod.Chip('gpiochip4')
LED_LINE = chip.get_line(IRLED)
LED_LINE.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)

def relay_on_time_between():
    """Turn IR LED on between 17:00 and 05:00."""
    start_time = 17
    end_time = 5
    current_time = datetime.now().hour
    LED_LINE.set_value(0 if current_time >= start_time or current_time <= end_time else 1)

# Capture the first frame
camera.start()
frame = camera.capture_array()
prev_frame = np.mean(frame, axis=2)  # Convert to grayscale

# Main loop
try:
    while True:
        relay_on_time_between()
        frame = camera.capture_array()
        curr_frame = np.mean(frame, axis=2)  # Convert to grayscale

        if detect_motion(prev_frame, curr_frame):
            if not recording:
                start_recording()  # Start recording if no recording is happening
            last_motion_time = time.time()  # Update last motion timestamp

        # Stop recording if no motion for more than the timeout duration
        if recording and last_motion_time is not None:
            if time.time() - last_motion_time > motion_timeout:
                stop_recording()
                last_motion_time = None  # Reset motion time to allow new detections

        prev_frame = curr_frame  # Update previous frame
        time.sleep(0.1)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    stop_recording()
    camera.close()
