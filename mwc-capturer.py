import os
import time
from datetime import datetime
import numpy as np
import cv2
import gpiod
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

# Parameter
motion_threshold = 1.0  # Sensitivitas gerakan
motion_timeout = 5  # Detik sebelum berhenti merekam jika tidak ada gerakan
recording = False
last_motion_time = None  # Waktu terakhir deteksi gerakan

# Inisialisasi kamera
camera = Picamera2()
video_config = camera.create_video_configuration()
camera.configure(video_config)
camera.start_preview(Preview.NULL)  # Tidak menampilkan preview

# Folder penyimpanan
output_folder = "recordings"
os.makedirs(output_folder, exist_ok=True)

# Deteksi Gerakan yang Diperbaiki
def detect_motion(prev_frame, curr_frame):
    """Deteksi gerakan dengan perbedaan frame."""
    diff = cv2.absdiff(prev_frame, curr_frame)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    motion_level = np.sum(thresh) / thresh.size
    detector = motion_level > motion_threshold
    print(f"[Motion Detected] Motion level: {motion_level:.2f}")
    return detector


def start_recording():
    global recording
    filename = f"{output_folder}/motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output = FfmpegOutput(filename)
    camera.start_recording(H264Encoder(), output)
    recording = True
    print(f"Recording started: {filename}")

def stop_recording():
    global recording, last_motion_time
    camera.stop_recording()
    recording = False
    last_motion_time = None  # Reset supaya bisa mulai rekaman baru
    print("Recording stopped.")

# Kontrol LED IR
IRLED = 16
chip = gpiod.Chip('gpiochip4')
LED_LINE = chip.get_line(IRLED)
LED_LINE.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)

def relay_on_time_between():
    """Nyalakan LED IR antara jam 17:00 - 05:00."""
    start_time = 17
    end_time = 5
    current_time = datetime.now().hour
    if current_time >= start_time or current_time <= end_time:
        LED_LINE.set_value(0)
        print("LED is ON")
    else:
        LED_LINE.set_value(1)
        print("LED is OFF")



try:
    while True:
        relay_on_time_between()
        # Mulai kamera
        camera.start()

        # Ambil frame awal untuk referensi
        prev_frame = camera.capture_array()
        prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2GRAY)
        prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)  # Blur untuk mengurangi noise
        while True:
            relay_on_time_between()
            # Ambil frame baru
            frame = camera.capture_array()
            curr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            curr_frame = cv2.GaussianBlur(curr_frame, (21, 21), 0)

            isDetect = detect_motion(prev_frame, curr_frame)

            if isDetect:
                if not recording:
                    start_recording()
                last_motion_time = time.time()
            else:
                if recording and last_motion_time and time.time() - last_motion_time > motion_timeout:
                    stop_recording()
                    break
            prev_frame = curr_frame  # Perbarui frame referensi
            time.sleep(0.1)  # Jeda untuk mengurangi beban CPU
        camera.stop() 
        # reset all the parameters needed like recording, last_motion_time, etc.
        recording = False
        last_motion_time = None
        print("Video Didapatkan")

except KeyboardInterrupt:
    print("Program dihentikan oleh pengguna.")

finally:
    camera.close()
    LED_LINE.release()
    chip.close()
    recording = False
    last_motion_time = None
    print("Program dihentikan.")
    
