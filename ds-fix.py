import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import numpy as np

# Inisialisasi Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(video_config)

# Inisialisasi encoder dan output
encoder = H264Encoder()
output = FfmpegOutput('output.mp4')

# Fungsi untuk mendeteksi pergerakan
def detect_motion(frame):
    # Konversi frame ke grayscale
    gray = np.mean(frame, axis=2).astype(np.uint8)
    
    # Hitung perbedaan antara frame saat ini dan frame sebelumnya
    if not hasattr(detect_motion, "prev_frame"):
        detect_motion.prev_frame = gray
        return False
    
    frame_diff = np.abs(gray - detect_motion.prev_frame)
    detect_motion.prev_frame = gray
    
    # Jika perbedaan melebihi threshold, ada pergerakan
    motion_detected = np.mean(frame_diff) > 20  # Threshold bisa disesuaikan
    return motion_detected

# Variabel untuk melacak waktu
last_motion_time = time.time()
recording = False

# Mulai preview
picam2.start_preview()

try:
    while True:
        # Ambil frame dari kamera
        frame = picam2.capture_array("main")
        
        # Deteksi pergerakan
        if detect_motion(frame):
            last_motion_time = time.time()
            if not recording:
                print("Motion detected! Starting recording...")
                picam2.start_recording(encoder, output)
                recording = True
        
        # Jika sedang recording dan tidak ada pergerakan selama 30 detik, stop recording
        if recording and (time.time() - last_motion_time > 30):
            print("No motion for 30 seconds. Stopping recording...")
            picam2.stop_recording()
            recording = False
        
        # Tunggu sebentar sebelum mengambil frame berikutnya
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    if recording:
        picam2.stop_recording()
    picam2.stop_preview()
    picam2.close()
