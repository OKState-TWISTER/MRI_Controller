from datetime import datetime
from enum import Enum
# Log levels for printing to console, does not effect log files
# 0 - Print nothing
# 1 - Print Error
# 2 - Print Warning
# 3 - Print Info
# 4 - Print Debug
class LOG_LEVEL(Enum):
    OFF = 0
    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4

class colors:
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    DEBUG = '\033[96m'
    END = '\033[0m'

class logger:
    def __init__(self, filename="log.txt", level=LOG_LEVEL.INFO):
        self.file = open(filename, "a")
        self.level = level

    def error(self, err):
        out = f"[ERROR] [{datetime.now().isoformat()}] {err}"
        self.file.write(f"{out}\n")
        self.file.flush()
        if self.level.value >= LOG_LEVEL.ERROR.value:
            print(f"{colors.ERROR}{out}{colors.END}")
        

    def warn(self, warn):
        out = f"[WARN] [{datetime.now().isoformat()}] {warn}"
        self.file.write(f"{out}\n")
        self.file.flush()
        if self.level.value >= LOG_LEVEL.WARN.value:
            print(f"{colors.WARNING}{out}{colors.END}")
    
    def info(self, info):
        out = f"[INFO] [{datetime.now().isoformat()}] {info}"
        self.file.write(f"{out}\n")
        self.file.flush()
        if self.level.value >= LOG_LEVEL.INFO.value:
            print(out)
    
    def debug(self, debug):
        out = f"[DEBUG] [{datetime.now().isoformat()}] {debug}"
        self.file.write(f"{out}\n")
        self.file.flush()
        if self.level.value >= LOG_LEVEL.DEBUG.value:
            print(f"{colors.DEBUG}{out}{colors.END}")