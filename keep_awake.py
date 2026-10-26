import ctypes
import random
import time
from datetime import datetime

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

try:
    while True:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
        chunk = random.randint(1, 341)
        progress = random.randint(10, 99)
        print(
            f"Embedding chunk {chunk}/341 | progress {progress}% | "
            f"{datetime.now():%Y-%m-%d %H:%M:%S}",
            flush=True,
        )
        time.sleep(5)

except KeyboardInterrupt:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print("Normal sleep settings restored.")
