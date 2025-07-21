from PySide6 import QtCore, QtWidgets
import time
from enum import Enum
from logger import logger, LOG_LEVEL

class SIDE(Enum):
    TX = 0
    RX = 1
    BOTH = 2
    
class JitterController(QtCore.QThread):
    send_command = QtCore.Signal(dict) # cmd
    send_command_to_target = QtCore.Signal(dict, str) #cmd, target

    def __init__(self, parent=None, scope=None, logger=None, duration=10.0, side=SIDE.BOTH):
        super().__init__(parent=parent)
        self.scope = scope
        self.logger = logger
        self.duration = duration
        self.side = side

        self.test_timer = QtCore.QTimer(self)
        self.test_timer.setSingleShot(True)
        self.test_timer.setInterval(self.duration)
        self.test_timer.timeout.connect(self.on_test_timeout)
        
    def setDuration(self, duration):
        if self.logger is not None:
            self.logger.debug(f"[JITTER] Set duration to {duration}")
        self.duration = duration
        self.test_timer.setInterval(self.duration)

    def startMeasurement(self):
        self.logger = logger("jitter_log", LOG_LEVEL.DEBUG)
        if self.logger is not None:
            self.logger.debug("[JITTER] Running Jitter Measurment")
        cmd = {}
        cmd['timestamp'] = time.time()
        cmd['cmd'] = "meas"
        cmd['args'] = {}
        cmd['args']['type'] = 'jitter'
        cmd['args']['duration'] = self.duration

        self.tx_response = None
        self.rx_response = None

        if self.side == SIDE.BOTH or self.side == SIDE.TX:
            self.send_command_to_target.emit(cmd, "tx")
        if self.side == SIDE.BOTH or self.side == SIDE.RX:
            self.send_command_to_target.emit(cmd, "rx")

        self.test_timer.start()

        

    def run(self):
        self.startMeasurement()

    @QtCore.Slot(str, dict)
    def on_tcp_data(self, src, data):
        self.logger.debug("Received TCP data")
        if self.side == SIDE.TX:
            if src == "Tx Pi":
                self.tx_response = data
                self.logger.info("[JITTER] Data received from tx")
        elif self.side == SIDE.RX:
            if src == "Rx Pi":
                self.rx_response = data
                self.logger.info("[JITTER] Data received from rx")
        elif self.side == SIDE.BOTH:
            if src == "Rx Pi":
                self.rx_response = data
                self.logger.info("[JITTER] Data received from rx")
            elif src == "Tx Pi":
                self.tx_response = data
                self.logger.info("[JITTER] Data received from tx")

    @QtCore.Slot()
    def on_test_timeout(self):
        if self.logger is not None:
            self.logger.info("[JITTER] Measurement Complete!")


            

        
