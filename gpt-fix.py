from picamera2 import Picamera2
import numpy as np
import time
import subprocess
from datetime import datetime

# Kamera dan pengaturan deteksi gerakan
motion_threshold = 10  # Semakin tinggi, semakin tidak sensitif
recording_duration = 180  # 3 menit (180 detik)
recording = False
recording_start_time = None
video_filename = None

# Inisialisasi kamera
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

def detect_motion(prev_frame, curr_frame):
    """Mendeteksi pergerakan berdasarkan perbedaan frame."""
    diff = np.abs(curr_frame - prev_frame)
    return np.sum(diff) / diff.size > motion_threshold  # Rata-rata perubahan

def start_recording():
    """Memulai perekaman video."""
    global recording, recording_start_time, video_filename
    recording = True
    recording_start_time = time.time()
    video_filename = f"motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    
    picam2.start_recording(video_filename, format="h264")
    print(f"Recording started: {video_filename}")

def stop_recording():
    """Menghentikan perekaman dan mengonversi ke MP4."""
    global recording, video_filename
    if recording:
        picam2.stop_recording()
        recording = False
        print("Recording stopped.")

        # Konversi ke MP4 menggunakan ffmpeg
        mp4_filename = video_filename.replace(".h264", ".mp4")
        subprocess.run(["ffmpeg", "-framerate", "24", "-i", video_filename, "-c:v", "libx264", "-preset", "fast", "-crf", "22", mp4_filename], check=True)
        print(f"Video saved as: {mp4_filename}")

        # Hapus file H264 agar tidak memenuhi penyimpanan
        subprocess.run(["rm", video_filename], check=True)

# Ambil frame pertama sebagai referensi
prev_frame = np.mean(picam2.capture_array(), axis=2)  # Konversi ke grayscale

# Loop utama
try:
    while True:
        curr_frame = np.mean(picam2.capture_array(), axis=2)  # Konversi ke grayscale

        if detect_motion(prev_frame, curr_frame):
            if not recording:
                start_recording()
        elif recording and (time.time() - recording_start_time >= recording_duration):
            stop_recording()

        prev_frame = curr_frame  # Update frame sebelumnya
        time.sleep(0.1)  # Delay untuk mengurangi penggunaan CPU

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    stop_recording()
    picam2.close()
