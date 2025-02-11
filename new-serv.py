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
last_motion_time = None  # Track last

# Initialize camera
camera = Picamera2()
video_config = camera.create_video_configuration()
camera.configure(video_config)
camera.start_preview(Preview.NULL)  # No preview, useful for background operations

output_folder = "recordings"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def detect_motion(prev_frame, curr_frame):
    """Detect motion by comparing frame differences."""
    diff = np.abs(curr_frame - prev_frame)
    return np.sum(diff) / diff.size > motion_threshold  # Average change (it returns a boolean where true means motion detected)

def start_recording():
    # just start recording
    filename = f"{output_folder}/motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output = FfmpegOutput(filename)
    camera.start_recording(H264Encoder(), output)
    print(f"Recording started: {filename}")

def stop_recording():
    # just stop recording and cleanup for next recording
    camera.stop_recording()
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
    global LED_LINE
    LED_LINE.set_value(0 if current_time >= start_time or current_time <= end_time else 1)

# mulai kamera.
camera.start()

# initial frame
prev_frame = camera.capture_array()
prev_frame = np.mean(frame, axis=2)
try:
    while True:
        # capture current frame
        frame = camera.capture_array()
        curr_frame = np.mean(frame, axis=2)

        isDetect = detect_motion(prev_frame, curr_frame)
        if isDetect:
            if not recording:
                start_recording()
                recording = True
            last_motion_time = time.time()
        else:
            if recording and time.time() - last_motion_time > motion_timeout:
                stop_recording()
                recording = False

        relay_on_time_between()
        prev_frame = curr_frame
        time.sleep(0.1)  # Delay to reduce CPU usage

except KeyboardInterrupt:
    print("Program stopped by user.")

finally:
    camera.stop()
    LED_LINE.release()
    chip.close()
    print("Program stopped.")


