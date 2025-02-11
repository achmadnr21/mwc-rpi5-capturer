import picamera
import picamera.array
import numpy as np
import time
from datetime import datetime

# Camera and motion detection settings
motion_threshold = 10  # Adjust sensitivity (higher = less sensitive)
recording_duration = 180  # 3 minutes (180 seconds)
recording = False
recording_start_time = None

# Initialize camera
camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.framerate = 24

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
    camera.start_recording(filename)
    print(f"Recording started: {filename}")

def stop_recording():
    """Stop recording."""
    global recording
    if recording:
        camera.stop_recording()
        recording = False
        print("Recording stopped.")

# Capture the first frame
with picamera.array.PiRGBArray(camera) as stream:
    camera.capture(stream, format='rgb')
    prev_frame = np.mean(stream.array, axis=2)  # Convert to grayscale

# Main loop
try:
    while True:
        with picamera.array.PiRGBArray(camera) as stream:
            camera.capture(stream, format='rgb')
            curr_frame = np.mean(stream.array, axis=2)  # Convert to grayscale

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
