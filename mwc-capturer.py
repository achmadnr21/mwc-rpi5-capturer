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
recording_duration = 30  # 30 mnt
recording = False
recording_start_time = None

# Initialize camera
camera = Picamera2()

# Configure the camera for video (not still images)
video_config = camera.create_video_configuration()
camera.configure(video_config)

# Configure preview (optional, useful for background operations)
camera.start_preview(Preview.NULL)  # No preview, useful for background operations

output_folder = "recordings"

# Create the folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Initialize encoder and file output for recording
encoder = H264Encoder()
#output = FfmpegOutput(f"motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

def detect_motion(prev_frame, curr_frame):
    """Detect motion by comparing frame differences."""
    diff = np.abs(curr_frame - prev_frame)
    return np.sum(diff) / diff.size > motion_threshold  # Average change

def start_recording():
    """Start recording a new video file."""
    global recording, recording_start_time, output
    recording = True
    recording_start_time = time.time()
    # Update the output with a new filename based on the current time
    output = FfmpegOutput(f"{output_folder}/motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    camera.start_recording(encoder, output)
    print(f"Recording started...")

def stop_recording():
    """Stop recording."""
    global recording
    if recording:
        camera.stop_recording()
        recording = False
        print("Recording stopped.")

IRLED = 16
# Start time default is 17:00 and turn it off next day at 5:00
chip = gpiod.Chip('gpiochip4')
LED_LINE = chip.get_line(IRLED)
LED_LINE.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)

def relay_on_time_between():
    start_time = 17
    end_time = 5
    current_time = datetime.now().hour
    if current_time >= start_time or current_time <= end_time:
        LED_LINE.set_value(0)
    else:
        LED_LINE.set_value(1)

# Capture the first frame
camera.start()  # Start camera
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
                start_recording()
        elif recording and (time.time() - recording_start_time >= recording_duration):
            stop_recording()

        prev_frame = curr_frame  # Update previous frame
        time.sleep(0.1)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    stop_recording()
    camera.close()
