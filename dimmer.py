import time
import gpiod

# Konfigurasi GPIO
IRLED = 16
chip = gpiod.Chip('gpiochip4')
LED_LINE = chip.get_line(IRLED)
LED_LINE.request(consumer="LED Checker", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)

print("IR LED Checker started. Press Ctrl+C to stop.")

try:
    while True:
        # Nyalakan LED IR selama 5 detik
        LED_LINE.set_value(0)
        print("IR LED ON")
        time.sleep(5)
        
        # Matikan LED IR selama 5 detik
        LED_LINE.set_value(1)
        print("IR LED OFF")
        time.sleep(5)

except KeyboardInterrupt:
    print("\nIR LED Checker stopped by user.")

finally:
    LED_LINE.set_value(1)  # Pastikan LED mati saat program berakhir
    LED_LINE.release()
    chip.close()
    print("Cleanup completed.")
