import time
from datetime import datetime
import numpy as np
import gpiod
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Camera and motion detection settings
motion_threshold = 10  # Adjust sensitivity (higher = less sensitive)
recording_duration = 180  # 3 minutes (180 seconds)
recording = False
recording_start_time = None

# Initialize camera
camera = Picamera2()
camera.configure(camera.create_still_configuration())

# Configure preview
camera.start_preview(Preview.NULL)  # No preview, useful for background operations

# Initialize encoder and file output for recording
encoder = H264Encoder()
output = FileOutput()

def detect_motion(prev_frame, curr_frame):
    """Detect motion by comparing frame differences."""
    diff = np.abs(curr_frame - prev_frame)
    return np.sum(diff) / diff.size > motion_threshold  # Average change

def start_recording():
    """Start recording a new video file."""
    global recording, recording_start_time
    recording = True
    recording_start_time = time.time()
    filename = f"motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    camera.start_recording(encoder, output, filename)
    print(f"Recording started: {filename}")

def stop_recording():
    """Stop recording."""
    global recording
    if recording:
        camera.stop_recording()
        recording = False
        print("Recording stopped.")

IRLED = 16
# start time default is 17:00 and turn it off next day at 5:00
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
