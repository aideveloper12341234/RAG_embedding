import ctypes
import time

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

try:
    while True:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
        print("Computer is staying awake...")
        time.sleep(60)

except KeyboardInterrupt:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print("Normal sleep settings restored.")
